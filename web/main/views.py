from django.conf import settings
from django.shortcuts import render
from django.urls import reverse

from test.test_helpers import (check_response,)
from .test.test_permissions_helpers import (no_perms_test,)


@no_perms_test
def index(request):
    """
    A placeholder landing page that reuses Perma Payment's design.

    Given:
    >>> client = getfixture('client')
    >>> url = reverse('index')

    It includes some placeholder text and a link to Harvard's Accessibility Policy
    >>> check_response(client.get(url), content_includes=[
    ...     'A Witness Server',
    ...     f'href="{settings.ACCESSIBILITY_POLICY_URL}"'
    ... ])
    """
    return render(request, 'generic.html', {
        'heading': "Perma Eyes",
        'message': "A Witness Server & Suite of Tools for Journalists and Fact Checkers"
    })
