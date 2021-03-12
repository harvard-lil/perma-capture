import datetime
from functools import wraps
import hashlib
import hmac
from pytz import timezone as tz
import secrets
import unicodedata
import urllib.parse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import URLValidator, ProhibitNullCharactersValidator
from django.forms.fields import URLField
from django.http import HttpResponseRedirect, JsonResponse
from django.template import Context, RequestContext, engines


#
# View helpers
#

def auth_view_json_response(view_func, allow_redirects=True):
    """
    A wrapper for the views supplied by django.contrib.auth, converting the response to JSON.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)

        if not settings.ALL_JSON_RESPONSES:
            return response

        if isinstance(response, HttpResponseRedirect):
            # These views redirect on success. Is the desirable for an SPA?
            # If not, we don't need the "done" views. The password reset
            # flow needs careful handling, because on GET it redirects from
            # the token-bearing URL to a tokenless one after verification.
            # I also observe that the change password form redirects to login
            # if you are anonymous: we might want to switch that to 401.
            if allow_redirects:
                return response

        form = response.context_data.get('form')
        if form:
            data = {
                'form': {
                    'is_bound': form.is_bound,
                    'is_valid': form.is_valid(),
                    'initial': form.initial,
                    'data': form.data,
                    'cleaned_data': getattr(form, 'cleaned_data', {}),
                    'errors': form.errors.get_json_data(),
                    'fields': {
                        key: {
                            'type': type(field).__name__,
                            'widget': type(field.widget).__name__,
                            'required': field.required,
                            'initial': field.initial,
                            'help_text': field.help_text,
                        } for key, field in form.fields.items()
                    },
                    'error_messages': getattr(form, 'error_messages', {})
                }
            }
        else:
            data = {'status': 'success'}
        json_response = JsonResponse(
            status=response.status_code,
            data=data
        )
        for header, value in response.items():
            json_response.setdefault(header, value)
        json_response.cookies = response.cookies
        return json_response

    return wrapper


#
# Email
#

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


#
# Capture helpers
#

def prohibit_control_characters_validator(value):
    for char in str(value):
        if unicodedata.category(char)[0] == "C":
            raise ValidationError("Non-printing characters are not allowed.", code='invalid', params={'value': value})


def validate_and_clean_url(url):
    """
    The Django form's URLField provides a bunch of validation and cleanup of submitted URLs.
    Take advantage of that, and restrict allowed protocols to http and https.
    See Django's tests for a full demonstration.
    https://github.com/django/django/blob/5fcfe5361e5b8c9738b1ee4c1e9a6f293a7dda40/tests/forms_tests/field_tests/test_urlfield.py

    N.B. Loopback addresses and reserved IP spaces are considered valid.

    N.B. Though we do restrict allowed protocols to http and https, this does not protect
    against redirect attacks, where an attacker's website redirects to file:///etc/passwrd
    or similar. That must be handled by the code responsible for the capturing browser.
    """
    url_validator = URLField(validators=[
        URLValidator(schemes=['http', 'https']),
        ProhibitNullCharactersValidator(),
        # Our past experience shows it is possible for control characters to make
        # it through and cause problems down the line. Reject them explicitly.
        prohibit_control_characters_validator
    ])
    return url_validator.clean(url)


def get_file_hash(handle, chunk_size=1024, algorithm='sha256'):
    """
    Calculate the file's hash.
    """
    hasher = getattr(hashlib, algorithm)()
    while True:
        chunk = handle.read(chunk_size)
        if not chunk:
            break
        hasher.update(chunk)
    return (hasher.hexdigest(), algorithm)


def override_access_url_netloc(access_url):
    return urllib.parse.urlparse(access_url)._replace(
        netloc=settings.OVERRIDE_DOWNLOAD_URL_NETLOC
    ).geturl()


def parse_querystring(url):
    return urllib.parse.parse_qs(urllib.parse.urlparse(url).query)


def datetime_from_timestamp(ts):
    return datetime.datetime.fromtimestamp(float(ts), tz(settings.TIME_ZONE))


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
