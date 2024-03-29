"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 3.0.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from copy import deepcopy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICES_DIR = os.path.abspath(os.path.join(BASE_DIR, '../../services'))
ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',

    # apps
    'main.apps.MainConfig',

    # third party
    'django_extensions',
    'rest_framework',
    'rest_framework.authtoken',
    'django_json_widget',

    # built-in
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.context_processors.settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'db',
        'PORT': 5432,
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

AUTH_USER_MODEL = 'main.User'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'
CSRF_FAILURE_VIEW = 'main.views.csrf_failure'

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = ('main.auth.ConfirmedUserSessionBackend',)
ALL_JSON_RESPONSES = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'main.auth.ConfirmedUserTokenBackend',
        'rest_framework.authentication.SessionAuthentication',  # authenticate with Django login
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'NON_FIELD_ERRORS_KEY': 'error',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json'
}

ALLOW_SIGNUPS = False
PASSWORD_RESET_TIMEOUT = 24 * 60 * 60


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')


# avoid the need for collectstatic in production (see http://whitenoise.evans.io/en/stable/django.html#WHITENOISE_USE_FINDERS )
WHITENOISE_USE_FINDERS = True

from django.utils.log import DEFAULT_LOGGING
LOGGING = deepcopy(DEFAULT_LOGGING)
LOGGING['handlers'] = {
    **LOGGING['handlers'],
    # log everything to console on both dev and prod
    'console': {
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
        'formatter': 'standard',
    },
    # custom error email template
    'mail_admins': {
        'level': 'ERROR',
        'filters': ['require_debug_false'],
        'class': 'main.reporter.CustomAdminEmailHandler'
    },
    # log to file
    'file': {
        'level':'INFO',
        'class':'logging.handlers.RotatingFileHandler',
        'filename': '/tmp/django.log',
        'maxBytes': 1024*1024*5, # 5 MB
        'backupCount': 5,
        'formatter':'standard',
    },
}
LOGGING['loggers'] = {
    **LOGGING['loggers'],
    # only show warnings for third-party apps
    '': {
        'level': 'WARNING',
        'handlers': ['console', 'mail_admins', 'file'],
    },
    # disable django's built-in handlers to avoid double emails
    'django': {
        'level': 'WARNING'
    },
    'django.request': {
        'level': 'ERROR'
    },
    'celery.django': {
        'level': 'INFO',
        'handlers': ['console', 'mail_admins', 'file'],
    },
    # show info for our first-party apps
    **{
        app_name: {'level': 'INFO'}
        for app_name in ('main',)
    },
}
LOGGING['formatters'] = {
    **LOGGING['formatters'],
    'standard': {
        'format': '%(asctime)s [%(levelname)s] %(filename)s %(lineno)d: %(message)s'
    },
}


### CELERY settings ###

if os.environ.get('DOCKERIZED'):
    CELERY_BROKER_URL = 'redis://redis:6379/1'
else:
    CELERY_BROKER_URL = 'redis://guest:guest@localhost::6379/1'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# if celery is launched with --autoscale=1000, celery will autoscale to 1000 but limited by system resources:
CELERY_WORKER_AUTOSCALER = 'celery_resource_autoscaler:ResourceAutoscaler'
CELERY_RESOURCE_LIMITS = [
    {
        'class': 'celery_resource_autoscaler:MemoryLimit',
        'kwargs': {'max_memory': 0.8},
    },
    {
        'class': 'celery_resource_autoscaler:CPULimit',
        'kwargs': {'max_load': 0.8},
    },
]

# These default time limits are useful in Perma, where capturing tasks
# sometimes hang, for still-undiagnosed reasons, and where all tasks
# are expected to be short-lived.
#
# It remains to be determined whether they will prove appropriate here.
#
# If a task is running longer than six minutes, ask it to shut down
CELERY_TASK_SOFT_TIME_LIMIT = 60 * 6
# If a task is running longer than seven minutes, kill it
CELERY_TASK_TIME_LIMIT = 60 * 7

# Control whether Celery tasks should be run asynchronously in a background worker
# process or synchronously in the main thread of the calling script / Django request.
# This should normally be False, but it's handy to not require the broker and a
# celery worker daemon to be running sometimes... for instance, if you want to drop into pdb.
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = True  # propagate exceptions when CELERY_TASK_ALWAYS_EAGER=True

# Lets you route particular tasks to particular queues.
# Mentioning a new queue creates it.
CELERY_TASK_ROUTES = {}

# from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {}

### \END CELERY settings ###

# Make these settings available for use in Django's templates.
# e.g. <a href="mailto:{{ CONTACT_EMAIL }}">Contact Us</a>
TEMPLATE_VISIBLE_SETTINGS = (
    'APP_NAME',
    'CONTACT_EMAIL',
    'ALLOW_SIGNUPS',
    'USE_ANALYTICS',
    'ACCESSIBILITY_POLICY_URL',
    'PASSWORD_RESET_TIMEOUT',
    'VITE_ENTRY_PATH',
    'VITE_USE_MANIFEST',
    'RWP_BASE_URL'
)

DEFAULT_FROM_EMAIL = 'info@perma.cc'
CONTACT_EMAIL = 'info@perma.cc'

ACCESSIBILITY_POLICY_URL = 'https://accessibility.huit.harvard.edu/digital-accessibility-policy'

# LIL's analytics JS
USE_ANALYTICS = False

# Since we don't know yet...
APP_NAME = 'capture.perma.cc'

TESTING = False
TEST_CAPTURE_TARGET_DOMAINS = ''

API_PREFIX = 'api'

# Storage
ARCHIVE_EXPIRES_AFTER_MINUTES = 4 * 60
DEFAULT_S3_STORAGE = {
    'endpoint_url': 'http://minio:9000',
    'access_key': 'accesskey',
    'secret_key': 'secretkey',
    'bucket_name': 'perma-capture'
}
OVERRIDE_STORAGE_NETLOC = None

# Scoop
SCOOP_BUILD_CONTEXT = os.path.abspath(os.path.join(BASE_DIR, '../../docker/scoop'))
SCOOP_IMAGE = 'scoop:0.3.1-1'
SCOOP_DOCKER_NETWORK = None
SCOOP_PROXY_PORT = os.environ.get('SCOOP_PROXY_PORT') or '9999'

SCOOP_FATAL_TIMEOUT_SECONDS = 60 * 5

SCOOP_ALLOW_VIDEO_AS_ATTACHMENT = True
SCOOP_MAX_RECORDING_MILLISECONDS = 60 * 4 * 1000
SCOOP_MAX_PAGE_LOAD_MILLISECONDS = None
SCOOP_MAX_NETWORK_IDLE_MILLISECONDS = None
SCOOP_MAX_BROWSER_BEHAVIORS_MILLISECONDS = None
SCOOP_MAX_VIDEO_AS_ATTACHMENT_MILLISECONDS = None
SCOOP_MAX_CERTS_AS_ATTACHMENT_MILLISECONDS = None
SCOOP_MAX_WINDOW_SIZE = None
SCOOP_MAX_RECORDING_SIZE = None
SCOOP_ALLOW_HEADFUL = False
SCOOP_USER_AGENT_SUFFIX = None

SCOOP_CUSTOM_BLOCKLIST = None
SCOOP_LOG_LEVEL = "trace"

LAUNCH_CAPTURE_JOBS = True

# Webhooks
DISPATCH_WEBHOOKS = True
WEBHOOK_DELIVERY_TIMEOUT = 10
WEBHOOK_MAX_RETRIES = 11
EXPOSE_WEBHOOK_TEST_ROUTE = False

# Playback
RWP_BASE_URL = 'https://cdn.jsdelivr.net/npm/replaywebpage@1.7.14'

# Vite/Vue frontend
VITE_MANIFEST_PATH = "main/static/manifest.json"
VITE_ENTRY_PATH = "src/main.ts"
