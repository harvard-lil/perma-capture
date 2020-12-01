from celery.task.control import inspect as celery_inspect
import datetime
from functools import wraps
from pytz import timezone as tz
import random
import redis
import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView
from django.core.exceptions import PermissionDenied
from django.http import (HttpResponseRedirect,  HttpResponseForbidden,
    HttpResponseServerError, HttpResponseBadRequest
)
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response as ApiResponse
from rest_framework import serializers, status
from rest_framework.views import APIView

from .forms import SignupForm, UserForm, PasswordResetForm
from .models import User, WebhookSubscription
from .serializers import WebhookSubscriptionSerializer, ArchiveSerializer
from .utils import generate_hmac_signing_key, sign_data, is_valid_signature, get_file_hash

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


###
### Views
###

class CaptureListView(APIView):

    @method_decorator(perms_test({'results': {200: ['user'], 401: [None]}}))
    def get(self, request):
        """get list of captures
        """
        res = requests.get(f'{settings.BACKEND_API}/captures', params={'userid': request.user.id})
        return ApiResponse(res.json(), status=res.status_code)

    @method_decorator(perms_test({'results': {400: ['user'], 401: [None]}}))
    def post(self, request):
        """ post capture
        """

        try:
            data = {
                'userid': request.user.id,
                'urls': request.data['urls'],
                'tag': request.data.get('tag') or '' ,
                'embeds': request.data.get('embeds') or False
            }
        except KeyError:
            raise serializers.ValidationError("Key 'urls' is required.")

        if settings.SEND_WEBHOOK_DATA_TO_CAPTURE_SERVICE:
            # our callback
            data['webhooks'] = [{
                'callback_url': request.build_absolute_uri(reverse('archived_callback')),
                'signing_key': settings.CAPTURE_SERVICE_WEBHOOK_SIGNING_KEY,
                'signing_key_algorithm': settings.CAPTURE_SERVICE_WEBHOOK_SIGNING_KEY_ALGORITHM,
                'user_data_field': timezone.now().timestamp()
            }]
            # user callbacks
            webhook_subscriptions = WebhookSubscription.objects.filter(
                user=request.user,
                event_type=WebhookSubscription.EventType.ARCHIVE_CREATED
            )
            if webhook_subscriptions:
                for subscription in webhook_subscriptions:
                    data['webhooks'].append({
                        'callback_url': subscription.callback_url,
                        'signing_key': subscription.signing_key,
                        'signing_key_algorithm': subscription.signing_key_algorithm,
                        'user_data_field': request.data.get('user_data_field')
                    })

        res = requests.post(f'{settings.BACKEND_API}/captures', json=data)
        return ApiResponse(res.json(), status=res.status_code)


class CaptureDetailView(APIView):

    @method_decorator(perms_test({'args': ['jobid'], 'results': {200: ['user'], 401: [None]}}))
    def delete(self, request, jobid):
        """ delete capture
        """
        logger.info(f"Deleting job {jobid}")
        res = requests.delete(f"{settings.BACKEND_API}/capture/{jobid}")
        return ApiResponse(res.json(), status=res.status_code)


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
            "signing_key_algorithm": "sha256",
            "user": 1
        }]
        >>> [subscription] = response.data
        >>> assert subscription['id'] == webhook_subscription.id
        >>> assert subscription['user'] == webhook_subscription.user.id
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
            "signing_key_algorithm": "sha256",
            "user": 1
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
        >>> assert response.data['user'] == user.id != disallowed_keys['user']
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
        {'id': 1, 'created_at': '2020-09-24T19:16:36.238012Z', 'updated_at': '2020-09-24T19:16:36.238026Z', 'event_type': 'ARCHIVE_CREATED', 'callback_url': 'https://webhookservice.com?hookid=1234', 'user': 1}
        >>> subscription = response.data
        >>> assert subscription['id'] == webhook_subscription.id
        >>> assert subscription['user'] == webhook_subscription.user.id
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


@no_perms_test
@api_view(['POST'])
@permission_classes([])  # no auth required
def archived_callback(request, format=None):
    """
    Respond upon receiving a notification from the capture service that an archive is complete.

    Given:
    >>> client, job, django_settings = [getfixture(f) for f in ['client', 'job', 'settings']]
    >>> url = reverse('archived_callback')
    >>> user = User.objects.get(id=job['userid'])
    >>> assert user.archives.count() == 0

    By default, we do not expect the data to be signed.
    >>> response = client.post(url, job, content_type='application/json')
    >>> check_response(response)
    >>> user.refresh_from_db()
    >>> assert user.archives.count() == 1

    Signature verification can be enabled via Django settings.
    >>> django_settings.VERIFY_WEBHOOK_SIGNATURE = True
    >>> django_settings.CAPTURE_SERVICE_WEBHOOK_SIGNING_KEY, django_settings.CAPTURE_SERVICE_WEBHOOK_SIGNING_KEY_ALGORITHM = generate_hmac_signing_key()
    >>> response = client.post(url, job, content_type='application/json')
    >>> check_response(response, status_code=400, content_includes='Invalid signature')
    >>> response = client.post(url, job, content_type='application/json',
    ...     HTTP_X_HOOK_SIGNATURE='foo'
    ... )
    >>> check_response(response, status_code=400, content_includes='Invalid signature')
    >>> response = client.post(url, job, content_type='application/json',
    ...     HTTP_X_HOOK_SIGNATURE=sign_data(job, django_settings.CAPTURE_SERVICE_WEBHOOK_SIGNING_KEY, django_settings.CAPTURE_SERVICE_WEBHOOK_SIGNING_KEY_ALGORITHM)
    ... )
    >>> check_response(response, content_includes='ok')
    >>> user.refresh_from_db()
    >>> assert user.archives.count() == 2

    Hashes are calculated if not supplied by the POSTed data.
    >>> assert all(key not in job for key in ['hash', 'hash_algorithm'])
    >>> assert all(archive.hash and archive.hash_algorithm for archive in user.archives.all())

    If we send a timestamp with our initial request and receive it back, we store that value:
    >>> assert user.archives.last().requested_at.timestamp() == job['user_data_field']

    If we do not send a timestamp with our initial request, or if the webhook
    payload does not include it, we default to 00:00:00 UTC 1 January 1970.
    >>> del job['user_data_field']
    >>> response = client.post(url, job, content_type='application/json',
    ...     HTTP_X_HOOK_SIGNATURE=sign_data(job, django_settings.CAPTURE_SERVICE_WEBHOOK_SIGNING_KEY, django_settings.CAPTURE_SERVICE_WEBHOOK_SIGNING_KEY_ALGORITHM)
    ... )
    >>> check_response(response)
    >>> assert 'user_data_field' not in job and 'user_data_field' not in response.data
    >>> assert user.archives.last().requested_at.timestamp() == 0

    The POSTed `userid` must match the id of a registered user.
    >>> job['userid'] = 1000
    >>> response = client.post(url, job, content_type='application/json',
    ...     HTTP_X_HOOK_SIGNATURE=sign_data(job, django_settings.CAPTURE_SERVICE_WEBHOOK_SIGNING_KEY, django_settings.CAPTURE_SERVICE_WEBHOOK_SIGNING_KEY_ALGORITHM)
    ... )
    >>> check_response(response, status_code=400, content_includes=['user', 'Invalid', 'does not exist'])

    Note: though jobid and hash should be unique, it is not enforced by this application
    (as is clear from the examples above).
    """
    if settings.VERIFY_WEBHOOK_SIGNATURE:
        if not is_valid_signature(
            request.headers.get('x-hook-signature', ''),
            request.data,
            settings.CAPTURE_SERVICE_WEBHOOK_SIGNING_KEY,
            settings.CAPTURE_SERVICE_WEBHOOK_SIGNING_KEY_ALGORITHM
        ):
            raise serializers.ValidationError('Invalid signature.')

    # for now, calculate file hash, if not included in POST
    # (hashing is not yet a feature of the capture service)
    hash = request.data.get('hash')
    hash_algorithm = request.data.get('hash_algorithm')
    if request.data.get('url') and (not hash or not hash_algorithm):
        hash, hash_algorithm = get_file_hash(request.data['url'])

    # retrieve the datetime from our user_data_field
    ts = request.data.get('user_data_field', 0)
    requested_at = datetime.datetime.fromtimestamp(ts, tz(settings.TIME_ZONE))

    # validate and save
    serializer = ArchiveSerializer(data={
        'user': request.data.get('userid'),
        'jobid': request.data.get('jobid'),
        'requested_at': requested_at,
        'hash': hash,
        'hash_algorithm': hash_algorithm
    })
    if serializer.is_valid():
        serializer.save()
        if not ts:
            logger.warning(f'No requested_at timestamp received for archive {serializer.instance.id}; defaulting to Unix Epoch.')
        return ApiResponse({'status': 'ok'}, status=status.HTTP_200_OK)
    return ApiResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        return render(request, 'main/dashboard.html')
    else:
        return render(request, 'generic.html', {
            'heading': settings.APP_NAME,
            'message': "A Witness Server & Suite of Tools for Journalists and Fact Checkers"
        })


@perms_test({'results': {200: ['user', None]}})
def docs(request):
    return render(request, 'main/docs.html')


@perms_test({'results': {200: ['user', None]}})
def render_sw(request):
    """
    Render the service worker in the root replay /replay/ path
    """
    return render(request, 'main/sw.js', content_type='application/javascript')


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
    return render(request, 'registration/sign_up.html', {'form': form})


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
    return render(request, 'main/account.html', {
        'form': form
    })


#
# Internal Use Only
#

@perms_test({'args': ['user.id', 'random_webhook_event.name'], 'results': {403: ['user'], 200: ['admin_user'], 'login': [None]}})
@user_passes_test_or_403(lambda user: user.is_staff)
def webhooks_test(request, user_id, event):  # pragma: no cover
    """
    For development and testing only: trigger a webhook for a user.
    """
    user = get_object_or_404(User, pk=user_id)

    payload = {}
    if event == WebhookSubscription.EventType.ARCHIVE_CREATED:
        payload = {
            'userid': user.id,
            'jobid': random.randint(0, 1000000000),
            'url': request.GET.get('url'),
            'user_data_field': timezone.now().timestamp()
        }
    else:
        raise NotImplementedError()

    subscriptions = user.webhook_subscriptions.filter(event_type=event)
    responses = []
    for subscription in subscriptions:
        try:
            responses.append(requests.post(
                subscription.callback_url,
                json=payload,
                headers={'x-hook-signature': sign_data(payload, subscription.signing_key, subscription.signing_key_algorithm)}
            ))
        except requests.exceptions.RequestException as e:
            responses.append({'status_code': None, 'url': subscription.callback_url, 'text': e})

    return render(request, 'manage/webhook-test.html', {
        'user': user,
        'event': event,
        'responses': responses
    })


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
