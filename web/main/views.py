from celery.task.control import inspect as celery_inspect
from functools import wraps
import redis
import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView
from django.core.exceptions import PermissionDenied
from django.http import (HttpResponseRedirect,  HttpResponseForbidden,
    HttpResponseServerError, HttpResponseBadRequest
)
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator

from rest_framework.decorators import api_view
from rest_framework.response import Response as ApiResponse
from rest_framework import serializers
from rest_framework.views import APIView

from .forms import SignupForm, UserForm, PasswordResetForm
from .models import User

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
                'tag': request.data['tag'],
            }
        except KeyError:
            raise serializers.ValidationError("Keys 'urls' and 'tag' are required.")

        res = requests.post(f'{settings.BACKEND_API}/captures', json=data)
        return ApiResponse(res.json(), status=res.status_code)


class CaptureDetailView(APIView):

    @method_decorator(perms_test({'args': ['mock_job', 'mock_job_index'], 'results': {200: ['user'], 401: [None]}}))
    def delete(self, request, jobid, index):
        """ delete capture
        """
        logger.info(f"Deleting job {jobid}, index {index}")
        res = requests.delete(f"{settings.BACKEND_API}/capture/{jobid}/{index}")
        return ApiResponse(res.json(), status=res.status_code)


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
        return render(request, 'dashboard.html', {
            'rwp_base_url': settings.RWP_BASE_URL,
        })
    else:
        return render(request, 'generic.html', {
            'heading': settings.APP_NAME,
            'message': "A Witness Server & Suite of Tools for Journalists and Fact Checkers"
        })


@no_perms_test
def render_sw(request):
    """
    Render the SW in the root replay /replay/ path
    """
    return render(request, 'sw.js', {
        'rwp_base_url': settings.RWP_BASE_URL
    }, content_type='application/javascript')




#
# User Management
#

@no_perms_test
def sign_up(request):
    """
    Given:
    >>> _, client, mailoutbox = [getfixture(f) for f in ['db', 'client', 'mailoutbox']]

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
    """
    form = SignupForm(request.POST or None, request=request)
    if request.method == 'POST':
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

    We'll need some information about usage limits/paid plans/memberships,
    but we haven't decided how that's going to work yet.
    >>> check_response(response, content_includes=[
    ...     "Usage Plan</h2>",
    ...     "Membership</h2>",
    ... ])
    """
    form = UserForm(request.POST or None, instance=request.user)
    if request.method == "POST":
        if form.is_valid():
            form.save()
    return render(request, 'account.html', {
        'form': form
    })


#
# Internal Use Only
#

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
