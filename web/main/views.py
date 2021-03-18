from celery.task.control import inspect as celery_inspect
from functools import wraps
import redis

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.db.models import Q
from django.db.models.functions import Coalesce
from django.http import (HttpResponseRedirect,  HttpResponseForbidden,
    HttpResponseServerError, HttpResponseBadRequest, JsonResponse
)
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt

import django_filters

from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter  # comment in if we need support for ordering
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response as ApiResponse
from rest_framework import status
from rest_framework.views import APIView

from .forms import SignupForm, UserForm, PasswordResetForm
from .models import CaptureJob, User, WebhookSubscription
from .serializers import CaptureJobSerializer, ReadOnlyCaptureJobSerializer, WebhookSubscriptionSerializer
from .tasks import run_next_capture

from .utils import sign_data, serialize_form

from test.test_helpers import check_response
from .test.test_permissions_helpers import no_perms_test, perms_test

import logging
logger = logging.getLogger(__name__)


###
### Helpers
###

def user_passes_test_or_403(test_func):
    """
    Decorator for views that checks that the user passes the given test,
    raising PermissionDenied if not. Based on Django's user_passes_test.
    The test should be a callable that takes the user object and
    returns True if the user passes.
    """
    def decorator(view_func):
        @login_required()
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not test_func(request.user):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class Paginator(LimitOffsetPagination):

    def __init__(self, *args, **kwargs):
        super().__init__()

        # set the maximum number of items a user sees per page by default
        self.default_limit = kwargs.get('page_size', 100)

        # cap how much larger a user can make a page by manually setting the limit URL param
        self.max_limit = kwargs.get('max_page_size', 500)


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class CaptureJobFilter(django_filters.rest_framework.FilterSet):
    """
    Custom filter for filtering capture jobs by query string.
    """
    active = django_filters.BooleanFilter(method='is_active')
    downloadable = django_filters.BooleanFilter(field_name='archive', lookup_expr='download_url__isnull', exclude=True)
    expired = django_filters.BooleanFilter(method='expired_download')
    url_contains = django_filters.CharFilter(field_name='requested_url', lookup_expr='icontains')
    id__in = NumberInFilter(field_name='id', lookup_expr='in')

    def is_active(self, queryset, name, value):
        active = Q(status__in=['pending', 'in_progress']) | Q(archive__download_url__isnull=False)
        if value:
            return queryset.filter(active)
        return queryset.exclude(active)

    def expired_download(self, queryset, name, value):
        expired = Q(status='completed', archive__download_url__isnull=True)
        if value:
            return queryset.filter(expired)
        return queryset.exclude(expired)

    class Meta:
        model = CaptureJob
        fields = ['status', 'label']


###
### Views
###

class CaptureListView(APIView):

    #
    # Set up query string filtering of GET endpoint
    #

    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,  # subclasses can be filtered by keyword if filterset_class is set
        OrderingFilter        # can be ordered by order_by= if ordering_fields is set
    )
    filterset_class = CaptureJobFilter
    ordering_fields = ('created_at', 'url', 'requested_url', 'label', 'status', 'capture_oembed_view')      # lock down order_by fields -- security risk if unlimited

    def filter_queryset(self, queryset):
        """
        Given a queryset, filter it with whichever filter backend is in use.
        Copied from GenericAPIView
        """
        try:
            for backend in list(self.filter_backends):
                queryset = backend().filter_queryset(self.request, queryset, self)
            return queryset
        except DjangoValidationError as e:
            raise ValidationError(e.error_dict)

    #
    # Endpoints
    #

    @method_decorator(perms_test({'results': {200: ['user'], 401: [None]}}))
    def get(self, request):
        """
        List capture jobs for the authenticated user.

        Given:
        >>> _, factory, client= [getfixture(f) for f in ['reset_sequences', 'user_with_capture_jobs_factory', 'client']]
        >>> url = reverse('captures')
        >>> user = factory(job_count=3, status='completed', archive__expired=False)
        >>> _ = factory(user=user, job_count=1, status='completed', archive__expired=True)
        >>> _ = factory(user=user, job_count=1, status='failed')
        >>> _ = factory(user=user, job_count=1, status='in_progress', requested_url='https://perma.cc/canary')
        >>> _ = factory(user=user, job_count=1, status='pending')
        >>> _ = factory(user=user, job_count=1, status='invalid', label='a-very-special-label')
        >>> assert user.capture_jobs.count() == 8
        >>> assert all(n in [job.id for job in user.capture_jobs.all()] for n in [1, 3, 5, 7])
        >>> other_user = factory(job_count=10)

        Logged in users see their capture jobs, paginated.
        >>> response = client.get(url, as_user=user)
        >>> check_response(response)
        >>> assert response.data['count'] == len(response.data['results']) == 8

        ## Filtering

        There are a handful of simple filters.

        You can filter by label...
        >>> response = client.get(f'{url}?label=a-very-special-label', as_user=user)
        >>> check_response(response)
        >>> assert response.data['count'] == len(response.data['results']) == 1
        >>> assert response.data['results'][0]['label'] == 'a-very-special-label'

        ...by status...
        >>> response = client.get(f'{url}?status=completed', as_user=user)
        >>> check_response(response)
        >>> assert response.data['count'] == len(response.data['results']) == 4
        >>> assert response.data['results'][0]['status'] == 'completed'

        ...by ID...
        >>> response = client.get(f'{url}?id__in=1,3,5,7', as_user=user)
        >>> check_response(response)
        >>> assert [job['id'] for job in response.data['results']] == [7, 5, 3, 1]

        ...and by requested URL (contains, case-insensitive).
        >>> response = client.get(f'{url}?url_contains=perma.cc', as_user=user)
        >>> check_response(response)
        >>> assert response.data['count'] == len(response.data['results']) == 1
        >>> assert response.data['results'][0]['requested_url'] == 'https://perma.cc/canary'

        There are also a handful of composite filters.

        Just get capture jobs with archives that are available to download...
        >>> response = client.get(f'{url}?downloadable=true', as_user=user)
        >>> check_response(response)
        >>> assert response.data['count'] == len(response.data['results']) == 3

        ...or capture jobs that succeeded, but whose archives have expired and are no longer available...
        >>> response = client.get(f'{url}?expired=true', as_user=user)
        >>> check_response(response)
        >>> assert response.data['count'] == len(response.data['results']) == 1

        ...or capture jobs that are still "active": pending, in progress, or with downloadable archives.
        >>> response = client.get(f'{url}?active=true', as_user=user)
        >>> check_response(response)
        >>> assert response.data['count'] == len(response.data['results']) == 5

        ## Sorting

        You can order by pk, and ?should we do any timestamps?
        """
        queryset = self.filter_queryset(CaptureJob.objects.filter(
            user=request.user
        ).annotate(
            url=Coalesce('validated_url', 'requested_url')
        ))
        paginator = Paginator()
        items = paginator.paginate_queryset(queryset, request, view=self)
        serializer = ReadOnlyCaptureJobSerializer(items, many=True)
        return paginator.get_paginated_response(serializer.data)

    @method_decorator(perms_test({'results': {201: ['user'], 401: [None]}}))
    def post(self, request):
        """
        Launch capture jobs for the authenticated user.

        Given:
        >>> user, client = [getfixture(f) for f in ['user', 'client']]
        >>> url = reverse('captures')

        You can send a single capture request...
        >>> response = client.post(url, {'requested_url': 'http://example.com'}, content_type='application/json', as_user=user)
        >>> check_response(response, status_code=201)
        >>> assert response.data['status'] == 'pending'

        ...or a list of independent capture requests.
        >>> response = client.post(url, [{'requested_url': 'http://example.com/1'}, {'requested_url': 'http://example.com/2', 'capture_oembed_view': True}], content_type='application/json', as_user=user)
        >>> check_response(response, status_code=201)
        >>> assert not response.data[0]['capture_oembed_view'] and response.data[1]['capture_oembed_view']

        In addition to specifying the URL, your request can optionally include configuration options:
        - whether we should use a headless or 'headful' browser to make the capture;
        - whether you would like the standard web view or the oEmbed snippet view of the target;
        - a label you would like associated with the job, for your convenience;
        - a data string you would like passed along to your webhook callbacks, when the capture is complete;
        - and, finally, "human": an indicator that a human is actively waiting for the result of the capture
          (for instance, watching the UI, waiting for its completion), and so, we should prioritize it... as
          opposed to, for instance, a large batch of URLs that can stand a few seconds of queuing.
        >>> configurable_fields = {
        ...     'requested_url': 'https://twitter.com/permacc/status/1039225277119954944',
        ...     'capture_oembed_view': True,
        ...     'headless': True,
        ...     'label': 'article-1-url-3',
        ...     'webhook_data': 'foo=bar&boo=baz',
        ...     'human': True
        ... }
        >>> response = client.post(url, configurable_fields, content_type='application/json', as_user=user)
        >>> check_response(response, status_code=201)
        >>> for key in configurable_fields:
        ...     assert response.data[key] == configurable_fields[key]

        The rest of the fields are read-only.
        >>> read_only_fields = {
        ...    'status': 'complete',
        ...    'message': {'foo': 'bar'},
        ...    'queue_position': 0,
        ...    'step_count': 5,
        ...    'step_description': 'foo',
        ...    'capture_start_time': "2014-06-16T19:23:24Z",
        ...    'capture_end_time': "2014-06-16T19:23:24Z",
        ...    'archive': 1
        ... }
        >>> response = client.post(url, {'requested_url': 'https://twitter.com/permacc/status/1039225277119954944', 'user': 1, **read_only_fields}, content_type='application/json', as_user=user)
        >>> check_response(response, status_code=201)
        >>> for key in read_only_fields:
        ...     assert response.data[key] != read_only_fields[key]
        >>> assert 'user' not in response.data
        >>> assert CaptureJob.objects.get(id=response.data['id']).user_id != 1
        """
        many = isinstance(request.data, list)
        serializer = CaptureJobSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(user=request.user)
        else:
            return ApiResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if settings.LAUNCH_CAPTURE_JOBS:
            for _ in range(len(request.data) if many else 1):
                run_next_capture.apply_async()

        return ApiResponse(serializer.data, status=status.HTTP_201_CREATED)


class CaptureDetailView(APIView):

    @method_decorator(perms_test({'args': ['capture_job.pk'], 'results': {200: ['capture_job.user'], 401: [None], 403: ['user']}}))
    def get(self, request, pk):
        """
        Retrieve details of a capture job.

        Given:
        >>> capture_job_factory, client = [getfixture(f) for f in ['capture_job_factory', 'client']]
        >>> invalid_capture_job = capture_job_factory(status='invalid')
        >>> completed_capture_job = capture_job_factory(status='completed')

        If the capture job has an associated archive, its serialization is included:
        >>> response = client.get(reverse('capture', args=[completed_capture_job.pk]), as_user=completed_capture_job.user)
        >>> check_response(response)
        >>> assert isinstance(response.data['archive'], dict)

        Otherwise, 'archive' is None (null in JSON):
        >>> response = client.get(reverse('capture', args=[invalid_capture_job.pk]), as_user=invalid_capture_job.user)
        >>> check_response(response)
        >>> assert response.data['archive'] is None
        """
        target = get_object_or_404(CaptureJob, pk=pk)
        if target.user_id != request.user.id:
            raise PermissionDenied()
        serializer = ReadOnlyCaptureJobSerializer(target)
        return ApiResponse(serializer.data)


class WebhookSubscriptionListView(APIView):

    @method_decorator(perms_test({'results': {200: ['user'], 401: [None]}}))
    def get(self, request):
        """
        List the authenticated user's webhook subscriptions.

        Given:
        >>> client, webhook_subscription = [getfixture(f) for f in ['client', 'webhook_subscription']]

        Simple get:
        >>> response = client.get(reverse('webhooks'), as_user=webhook_subscription.user)
        >>> check_response(response)

        Sample response:
        [{
            "id": 1,
            "created_at": "2020-09-25T20:41:15.774373Z",
            "updated_at": "2020-09-25T20:41:15.774414Z",
            "event_type": "ARCHIVE_CREATED",
            "callback_url": "https://webhookservice.com?hookid=1234",
            "signing_key": "128-byte-key",
            "signing_key_algorithm": "sha256"
        }]
        >>> [subscription] = response.data
        >>> assert subscription['id'] == webhook_subscription.id
        >>> assert subscription['event_type'] == webhook_subscription.event_type == WebhookSubscription.EventType.ARCHIVE_CREATED
        >>> assert subscription['callback_url'] == webhook_subscription.callback_url
        >>> for key in ['created_at', 'updated_at', 'signing_key', 'signing_key_algorithm']:
        ...     assert subscription[key]
        """
        items = WebhookSubscription.objects.filter(user=request.user)
        return ApiResponse(WebhookSubscriptionSerializer(items, many=True).data)

    @method_decorator(perms_test({'results': {400: ['user'], 401: [None]}}))
    def post(self, request):
        """
        Subscribe to a webhook.

        Given:
        >>> client, user = [getfixture(f) for f in ['client', 'user']]
        >>> assert user.webhook_subscriptions.count() == 0
        >>> url = reverse('webhooks')
        >>> data = {'callback_url': 'https://webhookservice.com?hookid=1234', 'event_type': 'ARCHIVE_CREATED'}

        Post the required data as JSON to subscribe:
        >>> response = client.post(url, data, content_type="application/json",  as_user=user)
        >>> check_response(response, status_code=201)
        >>> user.refresh_from_db()
        >>> assert user.webhook_subscriptions.count() == 1

        Sample response:
        {
            "id": 1,
            "created_at": "2020-09-25T20:41:15.774373Z",
            "updated_at": "2020-09-25T20:41:15.774414Z",
            "event_type": "ARCHIVE_CREATED",
            "callback_url": "https://webhookservice.com?hookid=1234",
            "signing_key": "128-byte-key",
            "signing_key_algorithm": "sha256"
        }
        >>> assert response.data['callback_url'] == data['callback_url']
        >>> assert response.data['event_type'] == data['event_type']
        >>> for key in ['created_at', 'updated_at','signing_key', 'signing_key_algorithm']:
        ...     assert key in response.data

        You can subscribe to the same event an arbitrary number of times, even with the same callback URL.
        >>> response = client.post(url, data, content_type="application/json",  as_user=user)
        >>> check_response(response, status_code=201)
        >>> user.refresh_from_db()
        >>> assert user.webhook_subscriptions.count() == 2

        At present, the only available event type is 'ARCHIVE_CREATED':
        >>> for invalid_event in ['archive_created', 'UNSUPPORTED_EVENT']:
        ...     payload = {**data, **{'event_type': invalid_event}}
        ...     response = client.post(url, payload, content_type="application/json", as_user=user)
        ...     check_response(response, status_code=400, content_includes="not a valid choice")
        >>> user.refresh_from_db()
        >>> assert user.webhook_subscriptions.count() == 2

        You may not specify `user`, `id`, `signing_key`, or `signing_key_algorithm`;
        they are populated automatically:
        >>> disallowed_keys = {'id': 1, 'user': 1000, 'signing_key': 'foo', 'signing_key_algorithm': 'bar'}
        >>> response = client.post(url, {**data, **disallowed_keys}, content_type="application/json",  as_user=user)
        >>> check_response(response, status_code=201)
        >>> user.refresh_from_db()
        >>> assert user.webhook_subscriptions.count() == 3
        >>> assert response.data['id'] != disallowed_keys['id']
        >>> assert WebhookSubscription.objects.get(id=response.data['id']).user_id == user.id != disallowed_keys['user']
        >>> assert response.data['signing_key'] != disallowed_keys['signing_key']
        >>> assert response.data['signing_key_algorithm'] != disallowed_keys['signing_key_algorithm']

        If you omit any required data, a subscription is not created:
        >>> for key in ['callback_url', 'event_type']:
        ...     payload = {k:v for k,v in data.items() if k != key}
        ...     check_response(client.post(url, payload, content_type="application/json", as_user=user), status_code=400)
        >>> user.refresh_from_db()
        >>> assert user.webhook_subscriptions.count() == 3
        """
        serializer = WebhookSubscriptionSerializer(data={
            'event_type': request.data.get('event_type'),
            'callback_url': request.data.get('callback_url')
        })
        if serializer.is_valid():
            serializer.save(user=request.user)
            return ApiResponse(serializer.data, status=status.HTTP_201_CREATED)
        return ApiResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WebhookSubscriptionDetailView(APIView):

    def get_subscription_for_user(self, user, pk):
        """
        Get single subscription, making sure that returned object is accessible_to(user).
        """
        subscription = get_object_or_404(WebhookSubscription, pk=pk)
        if subscription.user_id != user.id:
            raise PermissionDenied()
        return subscription

    @method_decorator(perms_test({'args': ['webhook_subscription.id'], 'results': {200: ['webhook_subscription.user'], 401: [None], 403: ['user']}}))
    def get(self, request, pk):
        """
        Retrieve details of a webhook subscription.

        Given:
        >>> client, webhook_subscription = [getfixture(f) for f in ['client', 'webhook_subscription']]

        Simple get:
        >>> response = client.get(reverse('webhook', args=[webhook_subscription.id]), as_user=webhook_subscription.user)
        >>> check_response(response)

        Sample response:
        {'id': 1, 'created_at': '2020-09-24T19:16:36.238012Z', 'updated_at': '2020-09-24T19:16:36.238026Z', 'event_type': 'ARCHIVE_CREATED', 'callback_url': 'https://webhookservice.com?hookid=1234'}
        >>> subscription = response.data
        >>> assert subscription['id'] == webhook_subscription.id
        >>> assert subscription['event_type'] == webhook_subscription.event_type == WebhookSubscription.EventType.ARCHIVE_CREATED
        >>> assert subscription['callback_url'] == webhook_subscription.callback_url
        >>> for key in ['created_at', 'updated_at']:
        ...     assert subscription[key]
        """
        target = self.get_subscription_for_user(request.user, pk)
        serializer = WebhookSubscriptionSerializer(target)
        return ApiResponse(serializer.data)


    @method_decorator(perms_test({'args': ['webhook_subscription.id'], 'results': {204: ['webhook_subscription.user'], 401: [None], 403: ['user']}}))
    def delete(self, request, pk):
        """
        Unsubscribe from a webhook.

        Given:
        >>> client, webhook_subscription = [getfixture(f) for f in ['client', 'webhook_subscription']]
        >>> user = webhook_subscription.user
        >>> assert user.webhook_subscriptions.count() == 1

        Simple delete:
        >>> response = client.delete(reverse('webhook', args=[webhook_subscription.id]), as_user=user)
        >>> check_response(response, status_code=204)
        >>> user.refresh_from_db()
        >>> assert user.webhook_subscriptions.count() == 0
        """
        target = self.get_subscription_for_user(request.user, pk)
        target.delete()
        return ApiResponse(status=status.HTTP_204_NO_CONTENT)


@perms_test({'results': {200: ['user', None]}})
def index(request):
    """
    Our landing page.

    Given:
    >>> client, user = [getfixture(f) for f in ['client', 'user']]
    >>> url = reverse('index')

    Anonymous users see our placeholder text and the mandatory link to Harvard's Accessibility Policy
    >>> check_response(client.get(url), content_includes=[
    ...     'A Witness Server',
    ...     f'href="{settings.ACCESSIBILITY_POLICY_URL}"'
    ... ])

    Logged in users see their dashboard.
    >>> check_response(client.get(url, as_user=user), content_includes=[
    ...     'Create a new archive',
    ...     f'href="{settings.ACCESSIBILITY_POLICY_URL}"'
    ... ])
    """
    if request.user.is_authenticated:
        return render(request, 'vue_base.html', {
            'rwp_base_url': settings.RWP_BASE_URL,
            'api_prefix': settings.API_PREFIX,
            'heading': 'Create a new archive'
        })
    else:
        return render(request, 'vue_base.html', {
            'heading': settings.APP_NAME,
            'message': "A Witness Server & Suite of Tools for Journalists and Fact Checkers"
        })


@perms_test({'results': {200: ['user', None]}})
def docs(request):
    return render(request, 'vue_base.html', {
        'rwp_base_url': settings.RWP_BASE_URL,
        'heading': 'User Guide'
    })


@perms_test({'results': {200: ['user', None]}})
def render_sw(request):
    """
    Render the service worker in the root replay /replay/ path
    """
    return render(request, 'main/sw.js', content_type='application/javascript', context={
        'rwp_base_url': settings.RWP_BASE_URL
    })


@perms_test({'results': {200: ['user', None]}})
@xframe_options_exempt
def replay_error(request):
    """
    The service worker should be installed and handle all requests to /replay?foo=bar,
    but this route serves to catch any requests that fall through by accident
    and communicate debugging suggestions to the user.
    """
    return render(request, 'main/replay-error.html')


#
# User Management
#

@no_perms_test
def sign_up(request):
    """
    Given:
    >>> _, client, mailoutbox, django_settings = [getfixture(f) for f in ['db', 'client', 'mailoutbox', 'settings']]
    >>> django_settings.ALLOW_SIGNUPS = True

    Signup flow -- can sign up:
    >>> check_response(client.get(reverse('sign_up')), content_includes=['Sign up'])
    >>> check_response(client.post(reverse('sign_up'), {
    ...     'email': 'user@example.edu',
    ...     'first_name': 'Test',
    ...     'last_name': 'User'
    ... }), content_includes=['Please check your email for a link'])

    Can confirm the account and set a password with the emailed URL:
    >>> assert len(mailoutbox) == 1
    >>> confirm_url = next(line for line in mailoutbox[0].body.rstrip().split("\\n") if line.startswith('http'))
    >>> check_response(client.get(confirm_url[:-1]+'wrong/'), content_includes=['The password reset link was invalid'])
    >>> new_password_form_response = client.get(confirm_url, follow=True)
    >>> check_response(new_password_form_response, content_includes=['Change my password'])
    >>> check_response(client.post(new_password_form_response.redirect_chain[0][0], {'new_password1': 'anewpass', 'new_password2': 'anewpass'}, follow=True), content_includes=['Your password has been set'])

    Can log in with the new account:
    >>> check_response(client.post(reverse('login'), {'username': 'user@example.edu', 'password': 'anewpass'}, follow=True), content_includes='Create a new archive')

    Received the welcome email after setting password:
    >>> assert len(mailoutbox) == 2
    >>> assert mailoutbox[1].subject == 'Welcome!'
    >>> assert "Here's an email full of welcome and instruction" in mailoutbox[1].body

    While in beta, signup can be disallowed:
    >>> django_settings.ALLOW_SIGNUPS = False
    >>> check_response(client.get(reverse('sign_up')),
    ...     content_includes=['we can send you an invitation'],
    ...     content_excludes=['<form method="POST"']
    ... )
    >>> check_response(client.post(reverse('sign_up'), {
    ...     'email': 'user2@example.edu',
    ...     'first_name': 'Test',
    ...     'last_name': 'User'
    ... }), content_excludes=['Please check your email for a link'])
    >>> assert len(mailoutbox) == 2
    """
    form = SignupForm(request.POST or None, request=request)
    if settings.ALLOW_SIGNUPS and request.method == 'POST':
        if form.is_valid():
            form.save()
            return render(request, 'registration/sign_up_success.html')
    return render(request, 'vue_base.html', {
        'form': form,
        'heading': 'Sign up'
    })


def reset_password(request):
    """
    Displays the reset password form. We wrap the default Django view to send
    an confirmation email if unconfirmed users try to reset their password.

    Given:
    >>> client, user, unconfirmed_user, deactivated_user, mailoutbox = [getfixture(i) for i in ['client', 'user', 'unconfirmed_user', 'deactivated_user', 'mailoutbox']]
    >>> url = reverse('password_reset')

    Confirmed users receive the password reset email as usual:
    >>> user_response = client.post(url, {"email": user.email}, follow=True)
    >>> assert len(mailoutbox) == 1
    >>> assert f'{settings.APP_NAME}' in  mailoutbox[0].subject
    >>> assert 'Password Reset' in  mailoutbox[0].subject
    >>> assert f'{settings.APP_NAME}' in  mailoutbox[0].body

    Unconfirmed users receive the confirmation email:
    >>> unconfirmed_response = client.post(url, {"email": unconfirmed_user.email}, follow=True)
    >>> assert len(mailoutbox) == 2
    >>> assert 'Please confirm your email' in  mailoutbox[1].subject
    >>> assert f'{settings.APP_NAME}' in  mailoutbox[1].body

    If you enter an address we don't have, or the address of a deactivated user,
    we still show you the "success" page as normal, to avoid leaking any information.
    >>> deactivated_response = client.post(url, {"email": deactivated_user.email}, follow=True)
    >>> nonexistent_response = client.post(url, {"email": "nope@nope.com"}, follow=True)
    >>> assert len(mailoutbox) == 2
    >>> assert user_response.content == unconfirmed_response.content == deactivated_response.content == nonexistent_response.content
    """
    if request.method == "POST":
        try:
            target_user = User.objects.get(email=request.POST.get('email'))
        except User.DoesNotExist:
            target_user = None
        if target_user:
            if not target_user.email_confirmed:
                target_user.send_confirmation_email(request)
                return HttpResponseRedirect(PasswordResetView.success_url)

    class OurPasswordResetView(PasswordResetView):

        def form_valid(self, form):
            """
            Add the request to the email's extra context dict, so that it,
            and context variables added by context processors, are available
            when rendering the reset email text.

            See forms.PasswordResetForm.
            """
            self.extra_email_context = self.extra_email_context or {}
            self.extra_email_context.update({'request': self.request})
            return super().form_valid(form)

    return OurPasswordResetView.as_view(form_class=PasswordResetForm)(request)


@perms_test(
    {'method': 'get', 'results': {405: ['user']}},
    {'method': 'post', 'results': {200: ['user'], 401: [None]}}
)
@api_view(['POST'])
def reset_token(request, format=None):
    """
    Get a new API token.

    Given:
    >>> client, user = [getfixture(i) for i in ['client', 'user']]
    >>> original_token = user.auth_token.key

    >>> response = client.post(reverse('token_reset'), as_user=user)
    >>> user.refresh_from_db()
    >>> check_response(response)
    >>> assert original_token != user.auth_token.key
    >>> assert response.data['token'] == user.auth_token.key
    """
    token = request.user.get_new_token()
    return ApiResponse({
        'token': token.key
    })


@perms_test({'results': {200: ['user'], 'login': [None]}})
@login_required
def account(request):
    """
    Given:
    >>> client, user = [getfixture(i) for i in ['client', 'user']]
    >>> (orig_first, orig_last, orig_email) = (user.first_name, user.last_name, user.email)
    >>> (new_first, new_last, new_email) = ('New First', 'New Last', 'new_email@example.com')
    >>> account_url = reverse('account')
    >>> response = client.get(account_url, as_user=user)

    There's a form for changing your email address or name.
    >>> check_response(response, content_includes=[
    ...     f'value="{user.first_name}"',
    ...     f'value="{user.last_name}"',
    ...     f'value="{user.email}"',
    ... ])

    The form works.
    >>> assert orig_first != new_first and orig_last != new_last and orig_email != new_email
    >>> response = client.post(account_url, {'email': new_email, 'first_name': new_first, 'last_name': new_last}, as_user=user)
    >>> user.refresh_from_db()
    >>> assert user.first_name == new_first and user.last_name == new_last and user.email == new_email
    >>> check_response(response, content_includes=[
    ...     f'value="{user.first_name}"',
    ...     f'value="{user.last_name}"',
    ...     f'value="{user.email}"',
    ... ])

    There's a link to the "Change Password" form.
    >>> check_response(response, content_includes=[
    ...     f"href=\\"{ reverse('password_change') }\\""
    ... ])

    Your API key is displayed, and there's a button for getting a new API key.
    >>> check_response(response, content_includes=[
    ...     "Your API key",
    ...     f'value="{user.auth_token.key}"',
    ...     "Get a new key</button>"
    ... ])
    """
    form = UserForm(request.POST or None, instance=request.user)
    if request.method == "POST":
        if form.is_valid():
            form.save()
        return JsonResponse(serialize_form(form))
    return render(request, 'vue_base.html')


#
# Internal Use Only
#

@no_perms_test
@api_view(['POST'])
@permission_classes([])  # no auth required
def webhook_test(request, format=None):
    logger.debug(request.data)
    return ApiResponse(status=status.HTTP_204_NO_CONTENT)


@perms_test({'results': {403: ['user'], 200: ['admin_user'], 'login': [None]}})
@user_passes_test_or_403(lambda user: user.is_staff)
def celery_queue_status(request):
    """
    A simple report of how many tasks are in the main and background celery queues,
    what tasks are being processed by which workers, and how many tasks each worker
    has completed.

    Given:
    >>> from main.tasks import demo_scheduled_task
    >>> _, client, admin_user = [getfixture(i) for i in ['celery_worker', 'client', 'admin_user']]
    >>> _ = demo_scheduled_task.apply_async()

    The page returns and correctly reports the task was completed.
    >>> check_response(client.get(reverse('celery_queue_status'), as_user=admin_user), content_includes=
    ...     'class="finished">main.tasks.demo_scheduled_task:'
    ... )
    """
    inspector = celery_inspect()
    active = inspector.active()
    reserved = inspector.reserved()
    stats = inspector.stats()

    queues = []
    if active is not None:
        for queue in sorted(active.keys()):
            try:
                queues.append({
                    'name': queue,
                    'active': active[queue],
                    'reserved': reserved[queue],
                    'stats': stats[queue],
                })
            except KeyError:
                pass

    r = redis.from_url(settings.CELERY_BROKER_URL)

    return render(request, 'manage/celery.html', {
        'queues': queues,
        'total_main_queue': r.llen('celery'),
        'total_background_queue': r.llen('background')
    })


#
# Error Handlers
#

def bad_request(request, exception):
    '''
    Custom view for 400 failures, required for proper rendering of
    our custom template, which uses injected context variables.
    https://github.com/django/django/blob/master/django/views/defaults.py#L97
    '''
    return HttpResponseBadRequest(render(request, '400.html'))


def csrf_failure(request, reason="CSRF Failure."):
    '''
    Custom view for CSRF failures, required for proper rendering of
    our custom template, which uses injected context variables.
    https://github.com/django/django/blob/master/django/views/defaults.py#L146
    '''
    return HttpResponseForbidden(render(request, '403_csrf.html'))


def server_error(request):
    '''
    Custom view for 500 failures, required for proper rendering of
    our custom template, which uses injected context variables.
    https://github.com/django/django/blob/master/django/views/defaults.py#L97
    '''
    return HttpResponseServerError(render(request, '500.html'))
