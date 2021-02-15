from .settings_base import *  # noqa

DEBUG = False

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# logging
LOGGING['handlers']['file']['filename'] = '/var/log/django.log'

VITE_USE_MANIFEST = True
