import pytest

from django.conf import settings
from django.urls import reverse
from django.test import Client

from test.test_helpers import check_response


@pytest.mark.parametrize('error', ['400', '403', '404', '500'])
def test_error_pages(error, mailoutbox):
    """
    Verify that our injected context variables are present.
    """
    response = Client(raise_request_exception=False).get(reverse(error))
    check_response(response, status_code=int(error), content_includes=[
        settings.APP_NAME,
        settings.CONTACT_EMAIL,
    ])
    if error == '500':
        [email] = mailoutbox
        assert 'Internal Server Error' in email.subject
    elif error == '400':
        [email] = mailoutbox
        assert 'Fishy' in email.subject
    else:
        assert len(mailoutbox) == 0


def test_csrf_error_page():
    """
    Verify that our injected context variables are present.
    """
    client = Client(
        raise_request_exception=False,
        enforce_csrf_checks=True
    )
    check_response(client.post(reverse('403_csrf')), status_code=403, content_includes=[
        settings.APP_NAME,
        settings.CONTACT_EMAIL,
    ])
