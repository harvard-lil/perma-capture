import hashlib
import hmac
import humps
import requests
import secrets
import urllib.parse

from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, RequestContext, engines


def render_plaintext_template_to_string(template, context, request=None):
    """
    Render a template to string WITHOUT Django's autoescaping, for
    use with non-HTML templates. Do not use with HTML templates!
    """
    # load the django template engine directly, so that we can
    # pass in a Context/RequestContext object with autoescape=False
    # https://docs.djangoproject.com/en/3.0/topics/templates/#django.template.loader.engines
    #
    # (though render and render_to_string take a "context" kwarg of type dict,
    #  that dict cannot be used to configure autoescape, but only to pass keys/values to the template)
    engine = engines['django'].engine
    if request:
        ctx = RequestContext(request, context, autoescape=False)
    else:
        ctx = Context(context, autoescape=False)
    return engine.get_template(template).render(ctx)


def send_template_email(subject, template, context, from_address, to_addresses):
    context.update({s: getattr(settings, s) for s in settings.TEMPLATE_VISIBLE_SETTINGS})
    email_text = render_plaintext_template_to_string(template, context)
    success_count = send_mail(
        subject,
        email_text,
        from_address,
        to_addresses,
        fail_silently=False
    )
    return success_count


def get_file_hash(url, chunk_size=1024, algorithm='sha256'):
    """
    Download URL and calculate the file's hash.
    """
    hasher = getattr(hashlib, algorithm)()
    r = requests.get(url, stream=True)
    for chunk in r.iter_content(chunk_size=1024):
        if chunk:
            hasher.update(chunk)
    return (hasher.hexdigest(), algorithm)


#
# Communicate with the Browserkube/Kubecaptures capture service
#

class CaptureServiceException(Exception):
    pass


def safe_get_response_json(response):
    """
    Return the response's JSON data, or, if absent, an empty dict.
    """
    try:
        data = response.json()
    except ValueError:
        data = {}
    return data


def query_capture_service(method, path, valid_if, params=None, json=None, data=None):

    # Make the request
    try:
        response = requests.request(
            method,
            f"{settings.BACKEND_API}{path}",
            params=params,
            json=humps.camelize(json) if json else None,
            data=humps.camelize(data) if data else None,
            timeout=10,
            allow_redirects=False
        )
    except requests.exceptions.RequestException as e:
        raise CaptureServiceException(f"Communication with the capture service failed: {e}") from e

    # Validate the response
    try:
        data = humps.decamelize(safe_get_response_json(response))
        assert valid_if(response.status_code, data)
    except AssertionError:
        raise CaptureServiceException(f"{response.status_code}: {data}")

    return response, data

def override_access_url_netloc(access_url, internal=False):
    return urllib.parse.urlparse(access_url)._replace(
        netloc=settings.OVERRIDE_ACCESS_URL_NETLOC['internal' if internal else 'external']
    ).geturl()

#
# Webhook signatures
#

def generate_hmac_signing_key(algorithm='sha256'):
    """
    Generate a key of the max recommended length as per https://tools.ietf.org/html/rfc2104.
    Returns a hex-encoded python string.

    See `is_valid_signature` for usage and tests.
    """
    hasher = getattr(hashlib, algorithm)()
    return (secrets.token_hex(hasher.block_size), algorithm)


def sign_data(data, key, algorithm):
    """
    Encode a dictionary as application/x-www-form-urlencoded), sign it
    (HMAC, using the specified hashing algorithm), and return the
    hex-encoded digest as a python string.

    See `is_valid_signature` for usage and tests.
    """
    return hmac.new(
        bytes(key, 'utf-8'),
        bytes(urllib.parse.urlencode(data, doseq=True), 'utf-8'),
        algorithm
    ).hexdigest()


def is_valid_signature(signature, data, key, algorithm):
    """
    Compute the HMAC for a dictionary of data, and return whether
    the supplied signature matches the computed digest.

    >>> key, algorithm = generate_hmac_signing_key()
    >>> data = {"foo": "bar"}
    >>> signature = sign_data(data, key, algorithm)
    >>> assert is_valid_signature(signature, data, key, algorithm)
    """
    return hmac.compare_digest(signature, sign_data(data, key, algorithm))
