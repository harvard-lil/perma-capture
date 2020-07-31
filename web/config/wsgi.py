"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# patch email sending to retry on error, to work around sporadic connection issues
from django.core.mail import EmailMessage
from smtplib import SMTPException
from .wsgi_utils import retry_on_exception
_orig_send = EmailMessage.send
def retrying_send(message, *args, **kwargs):
    return retry_on_exception(_orig_send, args=([message] + list(args)), kwargs=kwargs, exception=(SMTPException, TimeoutError))
EmailMessage.send = retrying_send

application = get_wsgi_application()
