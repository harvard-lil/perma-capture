from django.test.testcases import SimpleTestCase
from functools import wraps
from rest_framework.response import Response
from urllib.parse import urljoin, urlsplit

from pytest import raises as assert_raises

_default = object()
def check_response(response, status_code=200, content_type=_default, content_includes=None, content_excludes=None):
    assert response.status_code == status_code

    # check content-type if not a redirect
    if response.get('content-type'):
        # For rest framework response, expect json; else expect html.
        if content_type is _default:
            if type(response) == Response:
                content_type = "application/json"
            else:
                content_type = "text/html"
        if content_type is not None:
            assert response['content-type'].split(';')[0] == content_type

    if content_includes or content_excludes:
        content = response.content.decode()
        if content_includes:
            if isinstance(content_includes, str):
                content_includes = [content_includes]
            for content_include in content_includes:
                assert content_include in content
        if content_excludes:
            if isinstance(content_excludes, str):
                content_excludes = [content_excludes]
            for content_exclude in content_excludes:
                assert content_exclude not in content


def assert_url_equal(response, expected_url):
    """
    Based on https://docs.djangoproject.com/en/2.2/_modules/django/test/testcases/#SimpleTestCase.assertRedirects
    """
    if hasattr(response, 'redirect_chain'):
        url, _ = response.redirect_chain[-1]
    else:
        url = response.url

    # Prepend the request path to handle relative path redirects.
    _, _, path, _, _ = urlsplit(url)
    if not path.startswith('/'):
        url = urljoin(response.request['PATH_INFO'], url)

    SimpleTestCase().assertURLEqual(url, expected_url)


def raise_on_call(func, call_count=1, exc=Exception):
    """
    Raise an exception, after a function is called a certain number of times.
    >>> def f(): pass
    >>> bomb = raise_on_call(f, 3, ValueError('I exploded'))
    >>> bomb()
    >>> bomb()
    >>> with assert_raises(ValueError):
    ...     bomb()
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        if wrapper.calls == call_count:
            raise exc
        return func(*args, **kwargs)
    wrapper.calls = 0
    return wrapper
