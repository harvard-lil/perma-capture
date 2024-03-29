from storages.backends.s3boto3 import S3Boto3Storage

from django.conf import settings

# used only for suppressing INFO logging in S3Boto3Storage
import logging


#
# Base Classes
#

class S3Storage(S3Boto3Storage):
    # suppress boto3's INFO logging per https://github.com/boto/boto3/issues/521
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    file_overwrite = False


class PrivateS3Storage(S3Storage):
    default_acl = 'private'


#
# Storages
#

class ArchiveStorage(PrivateS3Storage):
    location = 'archives'


def get_archive_storage():
    # We're planning on supporting multiple storage solutions. I'm adding this
    # unnecessary layer of abstraction now, to hopefully encourage design decisions
    # that will make it easier to support multiple and customer-specific storages later.
    return ArchiveStorage(
        querystring_expire=settings.ARCHIVE_EXPIRES_AFTER_MINUTES * 60,
        **settings.DEFAULT_S3_STORAGE
    )


class ScreenshotStorage(PrivateS3Storage):
    location = 'screenshots'


def get_screenshot_storage():
    # For now, configure this way rather than by configuring default storage
    return ScreenshotStorage(**settings.DEFAULT_S3_STORAGE)


def screenshot_directory(instance, filename):
    return f'archive_{instance.id}/{filename}'

