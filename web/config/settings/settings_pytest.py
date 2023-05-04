# Django settings used by pytest

# WARNING: this imports from .settings_dev instead of config.settings, meaning it chooses to IGNORE any settings in
# config/settings/settings.py. This is potentially better (in that it doesn't return different results locally than
# it will on CI), but also potentially worse (in that you can't try out settings tweaks in settings.py and run tests
# against them).

from .settings_dev import *

# Don't use whitenoise for tests. Including whitenoise causes it to rescan static during each test, which greatly
# increases test time.
MIDDLEWARE.remove('whitenoise.middleware.WhiteNoiseMiddleware')

TESTING = True

LAUNCH_CAPTURE_JOBS = False
WEBHOOK_MAX_RETRIES = 1

DEFAULT_S3_STORAGE['bucket_name'] += '-test'

SCOOP_DOCKER_NETWORK = f"{os.environ.get('HOST_DIRECTORY')}_capture-target"
TEST_CAPTURE_TARGET_DOMAINS = os.environ.get('TEST_CAPTURE_TARGET_DOMAINS').split(',')

# Don't block anything
SCOOP_CUSTOM_BLOCKLIST = ","
