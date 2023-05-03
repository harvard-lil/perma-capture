import itertools
import time
import urllib.parse

from rest_framework.authtoken.models import Token
from rest_framework.settings import api_settings

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models.functions import Now
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .storages import get_profile_storage, profile_job_directory
from .utils import send_template_email, generate_hmac_signing_key

from pytest import raises as assert_raises

import logging
logger = logging.getLogger(__name__)


#
# HELPERS
#

class EditTrackedModel(models.Model):
    """
    Provide subclasses with a has_changed() function that checks whether a field name listed in tracked_fields
    has been changed since the last time the model instance was loaded or saved.

    This is the same functionality provided by django-model-utils and django-dirtyfields, but
    those packages can be error-prone in hard-to-diagnose ways, or impose a significant performance cost:

        https://www.alextomkins.com/2016/12/the-cost-of-dirtyfields/
        https://github.com/jazzband/django-model-utils/issues/331
        https://github.com/jazzband/django-model-utils/pull/313

    This class attempts to do the same thing in a minimally magical way, by requiring child classes to list the
    fields they want to track explicitly. It depends on no Django internals, except for these assumptions:

        (a) deferred fields are populated via refresh_from_db(), and
        (b) populated field values will be added to instance.__dict__

    Originally from https://github.com/harvard-lil/h2o/commit/38f54e5dd7fd5e10d815c8ecfc27692c512729ee#diff-41fd7c2ab0e36742b4af449b181e66f7R43
    """

    class Meta:
        abstract = True

    tracked_fields = []
    original_state = {}

    # built-in methods that need to call reset_original_state() after running:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset_original_state()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.reset_original_state()

    def refresh_from_db(self, *args, **kwargs):
        super().refresh_from_db(*args, **kwargs)
        self.reset_original_state()

    def reset_original_state(self):
        """
        Update original_state with the current value of each field name in tracked_fields.
        Checking k in self.__dict__ means that deferred fields will be omitted entirely,
        rather than fetched.
        """
        self.original_state = {k: getattr(self, k) for k in self.tracked_fields if k in self.__dict__}

    def has_changed(self, field_name):
        """
        Return True if the field with the given name has changed locally. Will return True for all fields of a new
        unsaved instance, and True for deferred fields whether or not they happen to match the database value.

        >>> db, assert_num_queries = [getfixture(f) for f in ['db', 'assert_num_queries']]
        >>> u = User(is_active=True)
        >>> assert u.has_changed('is_active')             # new model: has_changed == True
        >>> u.save()
        >>> assert not u.has_changed('is_active')         # saved: has_changed == False
        >>> u.is_active = False
        >>> assert u.has_changed('is_active')             # changing the saved value: has_changed == True
        >>> u.refresh_from_db()
        >>> assert not u.has_changed('is_active')         # refresh from db: has_changed == False
        >>> u2 = User.objects.get(pk=u.pk)
        >>> assert not u2.has_changed('is_active')        # load new copy from db: has_changed == False
        >>> u2 = User.objects.defer('is_active').get(pk=u.pk)
        >>> with assert_num_queries():
        ...     assert not u2.has_changed('is_active')    # load new copy with deferred field: has_changed == False
        >>> u2.is_active = False
        >>> assert u2.has_changed('is_active')            # assign to deferred field: has_changed == True (may not be correct!)
        """
        if field_name not in self.tracked_fields:  # pragma: no cover
            raise ValueError("%s is not in tracked_fields" % field_name)
        if not self.pk:
            # if model hasn't been saved yet, report all fields as changed
            return True
        if field_name not in self.__dict__:
            # if the field was deferred and hasn't been assigned to locally, report as not changed
            return False
        if field_name not in self.original_state:
            # if the field was deferred and has been assigned to locally, report as changed
            # (which won't be correct if it happens to be assigned the same value as in the db)
            return True
        return self.original_state[field_name] != getattr(self, field_name)


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


#
# MODELS
#

class WebhookSubscription(TimestampedModel):

    class EventType(models.TextChoices):
        ARCHIVE_CREATED = 'ARCHIVE_CREATED', 'Archive Created'

    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='webhook_subscriptions'
    )
    event_type = models.CharField(
        max_length=32,
        choices=EventType.choices,
        default=EventType.ARCHIVE_CREATED
    )
    callback_url = models.URLField()
    signing_key = models.CharField(max_length=512)
    signing_key_algorithm = models.CharField(max_length=32)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'event_type'])
        ]

    def save(self, *args, **kwargs):
        """
        On creation, generate a signing key if not provided:
        >>> user = getfixture('user')
        >>> instance = WebhookSubscription(user=user, callback_url='https://webhookservice.com?hookid=1234')
        >>> assert not instance.signing_key and not instance.signing_key_algorithm
        >>> instance.save()
        >>> assert instance.signing_key and instance.signing_key_algorithm

        If a key and algorithm name are provided, they won't be overridden:
        >>> instance = WebhookSubscription(signing_key='foo', signing_key_algorithm='bar', user=user, callback_url='https://webhookservice.com?hookid=1234')
        >>> assert instance.signing_key and instance.signing_key_algorithm
        >>> instance.save()
        >>> instance.refresh_from_db()
        >>> assert instance.signing_key == 'foo' and instance.signing_key_algorithm == 'bar'
        """
        if not self.pk:
            if not self.signing_key or not self.signing_key_algorithm:
                self.signing_key, self.signing_key_algorithm = generate_hmac_signing_key()

        super().save(*args, **kwargs)


class Job(TimestampedModel):
    """
    Metadata and helpers for tracking celery. Abstract base class.
    """
    class Meta:
        abstract = True

    class Status(models.TextChoices):
        PENDING = 'pending', 'pending'
        IN_PROGRESS = 'in_progress', 'in_progress'
        COMPLETED = 'completed', 'completed'
        FAILED = 'failed', 'failed'
        INVALID = 'invalid', 'invalid'

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    # "message" is a field for reporting validation errors or error messages.
    message = models.JSONField(null=True, blank=True)

    # reporting
    step_count = models.FloatField(default=0)
    step_description = models.CharField(max_length=255, blank=True, null=True)
    capture_start_time = models.DateTimeField(blank=True, null=True)
    capture_end_time = models.DateTimeField(blank=True, null=True)

    def inc_progress(self, inc, description):
        self.step_count = int(self.step_count) + inc
        self.step_description = description
        self.save(update_fields=['step_count', 'step_description', 'updated_at'])

    def mark_completed(self, status=Status.COMPLETED):
        """
        Record completion time and status for this job.
        """
        self.status = status
        self.capture_end_time = Now()
        self.save(update_fields=['status', 'message', 'capture_end_time', 'updated_at'])

    def mark_failed(self, message):
        """
        Mark job as failed, and record message in format for front-end display.
        """
        self.message = {api_settings.NON_FIELD_ERRORS_KEY: [message]}
        self.mark_completed(Job.Status.FAILED)

    def mark_invalid(self, message_dict):
        """
        Mark job as invalid, and record message in format for front-end display.
        """
        self.message = message_dict
        self.mark_completed(Job.Status.INVALID)

    def queue_time(self):
        try:
            delta = self.capture_start_time - self.created_at
            return delta.seconds
        except (ObjectDoesNotExist, TypeError):
            return None
    queue_time.short_description = 'queue time (s)'

    def capture_time(self):
        try:
            delta = self.capture_end_time - self.capture_start_time
            return delta.total_seconds()
        except TypeError:
            return None
    capture_time.short_description = 'capture time (s)'


class CaptureJob(Job):
    """
    Metadata about capture jobs requested by a user.
    """
    requested_url = models.CharField(max_length=2100, db_index=True, blank=True, null=False, default='')
    capture_oembed_view = models.BooleanField(default=False)
    headless = models.BooleanField(default=True)
    log_in_if_supported = models.BooleanField(default=True)
    label = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    webhook_data = models.CharField(max_length=255, blank=True, null=True,
        help_text="This string will be included, verbatim, in any webhook \
        notification response that you have subscribed to receive."
    )
    validated_url = models.CharField(max_length=2100, blank=True, null=True)

    # Record whether a human is actively awaiting the results of the job; may influence queue order.
    human = models.BooleanField(default=False)
    order = models.FloatField(db_index=True)

    user = models.ForeignKey(
        'User',
        on_delete=models.PROTECT,
        related_name='capture_jobs'
    )

    def __str__(self):
        return f"CaptureJob {self.pk}"

    # settings to allow our tests to draw out race conditions
    TEST_PAUSE_TIME = 0
    TEST_ALLOW_RACE = False

    def save(self, *args, **kwargs):

        # If this job does not have an order yet (just created),
        # examine all pending jobs to place this one in a fair position in the queue.
        # "Fair" means round robin: this job will be processed after every other job submitted by this user,
        # and then after every other user waiting in line has had at least one job done.
        if not self.order:

            # get all pending jobs, in reverse priority order
            pending_jobs = CaptureJob.objects.filter(status=CaptureJob.Status.PENDING, human=self.human).order_by('-order')
            # narrow down to just the jobs that come *after* the most recent job submitted by this user
            pending_jobs = list(itertools.takewhile(lambda x: x.user_id != self.user_id, pending_jobs))
            # flip the list of jobs back around to the order they'll be processed in
            pending_jobs = list(reversed(pending_jobs))

            # Go through pending jobs until we find two jobs submitted by the same user.
            # It's not fair for another user to run two jobs after all of ours are done,
            # so this new job should come right before that user's second job.
            next_jobs = {}
            last_job = None
            for pending_job in pending_jobs:
                pending_job_user_id = pending_job.user_id
                if pending_job_user_id in next_jobs:
                    # pending_job is the other user's second job, so this one goes in between that and last_job
                    self.order = last_job.order + (pending_job.order - last_job.order)/2
                    break
                next_jobs[pending_job_user_id] = pending_job
                last_job = pending_job

            # If order isn't set yet, that means we should go last. Find the highest current order and add 1.
            if not self.order:
                if pending_jobs:
                    self.order = pending_jobs[-1].order + 1
                else:
                    self.order = (CaptureJob.objects.filter(human=self.human).aggregate(models.Max('order'))['order__max'] or 0) + 1

        super().save(*args, **kwargs)


    @classmethod
    def get_next_job(cls, reserve=False):
        """
        Return the next job to work on, looking first at the human queue and then at the robot queue.
        If `reserve=True`, mark the returned job with `status=in_progress` and remove from queue so the
        same job can't be returned twice. Caller must make sure the job is actually processed once returned.
        """

        while True:
            next_job = cls.objects.filter(status=cls.Status.PENDING).order_by('-human', 'order', 'pk').first()

            if reserve and next_job:
                if cls.TEST_PAUSE_TIME:
                    time.sleep(cls.TEST_PAUSE_TIME)

                # update the returned job to be in_progress instead of pending, so it won't be returned again
                # set time using database time, so timeout comparisons will be consistent across worker servers
                update_count = cls.objects.filter(
                    status=cls.Status.PENDING,
                    pk=next_job.pk
                ).update(
                    status=cls.Status.IN_PROGRESS,
                    capture_start_time=Now()
                )

                # if no rows were updated, another worker claimed this job already -- try again
                if not update_count and not cls.TEST_ALLOW_RACE:
                    continue

                # load up-to-date time from database
                next_job.refresh_from_db()

            return next_job

    def queue_position(self):
        """
        Search job_queues to calculate the queue position for this job -- how many pending jobs have to be processed
        before this one?
        Returns 0 if job is not pending.
        """
        if self.status != CaptureJob.Status.PENDING:
            return 0

        queue_position = CaptureJob.objects.filter(status=Job.Status.PENDING, order__lte=self.order, human=self.human).count()
        if not self.human:
            queue_position += CaptureJob.objects.filter(status=Job.Status.PENDING, human=True).count()

        return queue_position

    def mark_completed(self, status=Job.Status.COMPLETED):
        """
        Record completion time and status for this job.
        """
        if status == CaptureJob.Status.COMPLETED and not self.archive:
            logger.error(f"To investigate: Capture Job {self.id} has no archive, but was being marked completed.")
            status = CaptureJob.Status.FAILED
        super().mark_completed(status)


class ArchiveQuerySet(QuerySet):
    def expired(self):
        return self.filter(download_url__isnull=False, download_expiration_timestamp__lt=timezone.now())


class Archive(TimestampedModel):
    """
    Metadata about archives produced for a user.
    """
    hash = models.CharField(max_length=256)
    hash_algorithm = models.CharField(max_length=32)
    warc_size = models.IntegerField(blank=True, null=True)
    download_url = models.URLField(max_length=2100, null=True)
    download_expiration_timestamp = models.DateTimeField(null=True)

    # maybe? not sure
    # content_type = models.CharField(max_length=255, null=False, default='', help_text="HTTP Content-type header.")
    # contains_screenshot = models.BooleanField(default=False)
    # Potentially robots.txt / <meta name="robots" content="noarchive"> / X-Robots-Tag Directives

    capture_job = models.OneToOneField(
        'CaptureJob',
        on_delete=models.CASCADE,
        related_name='archive'
    )
    created_with_profile = models.ForeignKey(
        'Profile',
        on_delete=models.PROTECT,
        related_name='archives',
        null=True,
        blank=True
    )

    objects = ArchiveQuerySet.as_manager()

    @property
    def filename(self):
        return f"job-{self.capture_job.id}-{urllib.parse.urlparse(self.capture_job.validated_url).netloc.replace('.', '-')}.wacz"


def validate_profile_netloc(value):
    if value not in settings.PROFILE_SECRETS:
        raise ValidationError(f"We don't currently support the creation of profiles for {value}.")
    return value


class ProfileCaptureJob(Job):
    """
    Metadata about attempts to create browser profiles.
    """
    netloc = models.CharField(max_length=255, validators=[validate_profile_netloc])
    headless = models.BooleanField(default=False)
    screenshot = models.FileField(
        storage=get_profile_storage,
        upload_to=profile_job_directory,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"ProfileCaptureJob {self.pk}"

    def save(self, *args, **kwargs):
        if self.status == ProfileCaptureJob.Status.INVALID:
            raise ValidationError("We don't presently allow invalid ProfileCaptureJobs")
        super().save(*args, **kwargs)

    def get_job_id(self):
        """
        A method for use by the storage helper `profile_job_directory`. Must be defined on both ProfileCaptureJob and Profile.
        """
        return self.id

    @classmethod
    def get_job(cls, pk):
        job = cls.objects.get(id=pk)
        job.status = cls.Status.IN_PROGRESS
        job.capture_start_time = Now()
        job.save()

        # load up-to-date time from database
        job.refresh_from_db()

        return job

    @property
    def has_profile(self):
        try:
            self.profile
        except ObjectDoesNotExist:
            return False
        return True



class Profile(TimestampedModel):
    """
    Browser profile
    https://support.mozilla.org/en-US/kb/profiles-where-firefox-stores-user-data#w_what-information-is-stored-in-my-profile
    """
    netloc = models.CharField(max_length=255)  # denormalized for easier lookups
    headless = models.BooleanField(default=False)  # denormalized for easier lookups
    username = models.CharField(max_length=255)
    verified = models.BooleanField(default=False)
    marked_obsolete = models.DateTimeField(blank=True, null=True)
    profile = models.FileField(storage=get_profile_storage, upload_to=profile_job_directory)
    profile_capture_job = models.OneToOneField(
        'ProfileCaptureJob',
        on_delete=models.CASCADE,
        related_name='profile'
    )

    class Meta:
        indexes = [
            models.Index(fields=['netloc', 'headless', 'verified', 'marked_obsolete'])
        ]

    @classmethod
    def for_url(cls, url, headless):
        profile = cls.objects.filter(
            netloc=urllib.parse.urlparse(url).netloc,
            headless=headless,
            verified=True,
            marked_obsolete__isnull=True
        ).first()

        if profile:
            return profile

    def __str__(self):
        return f"Profile {self.pk}: {self.username} at {self.netloc}"

    def get_job_id(self):
        """
        A method for use by the storage helper `profile_job_directory`. Must be defined on both ProfileCaptureJob and Profile.
        """
        return self.profile_capture_job_id


class UserManager(BaseUserManager):
    """
    Custom manager where email is the unique identifier for authentication instead of username.
    """

    def create_user(self, email, password, **kwargs):
        """
        Given:
        >>> db = getfixture('db')
        >>> email = 'regular_user@EXAMPLE.com'
        >>> password = 'foo'
        >>> user = User.objects.create_user(email=email, password=password)

        Users don't have a 'username' field.
        >>> with assert_raises(AttributeError, match="'User' object has no attribute 'username'"):
        ...    user.username

        Rather, email and password are both required:
        >>> with assert_raises(TypeError, match="missing 2 required positional arguments: 'email' and 'password'"):
        ...    User.objects.create_user()
        >>> with assert_raises(TypeError, match="missing 1 required positional argument: 'password'"):
        ...    User.objects.create_user(email='')
        >>> with assert_raises(ValueError, match='Email address is required'):
        ...    User.objects.create_user(email='', password=password)

        Users' emails are normalized on saving.
        >>> assert user.email != email and user.email == email.lower()

        Standard users are active, need to confirm their email address, and have no special privileges.
        >>> assert user.is_active
        >>> assert not user.email_confirmed
        >>> assert not user.is_staff
        >>> assert not user.is_superuser
        """

        if not email:
            raise ValueError('Email address is required')

        user = self.model(email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **kwargs):
        """
        Given:
        >>> db = getfixture('db')
        >>> email = 'super_user@example.com'
        >>> password = 'foo'
        >>> super_user = User.objects.create_superuser(email=email, password=password)

        Superusers are active and confirmed, and are awarded staff and superuser privileges.
        >>> assert super_user.is_active
        >>> assert super_user.email_confirmed
        >>> assert super_user.is_staff
        >>> assert super_user.is_superuser

        You can't manually set is_staff or is_superuser False:
        >>> with assert_raises(ValueError, match='Superuser must have is_superuser=True.'):
        ...     User.objects.create_superuser(email=email, password=password, is_superuser=False)
        >>> with assert_raises(ValueError, match='Superuser must have is_staff=True.'):
        ...     User.objects.create_superuser(email=email, password=password, is_staff=False)
        """
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        kwargs.setdefault('email_confirmed', True)

        if kwargs.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if kwargs.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        user = self.create_user(email=email, password=password, **kwargs)
        return user

    def get_by_natural_key(self, username):
        """
        Make user logins case-insensitive, which works because you can't sign up
        with the same email with different capitalization anyway.
        """
        return self.get(email__iexact=username)


class User(EditTrackedModel, TimestampedModel, PermissionsMixin, AbstractBaseUser):
    email = models.EmailField(
        max_length=254,
        unique=True,
        db_index=True,
        error_messages={'unique': "A user with that email address already exists."}
    )

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    deactivated_date = models.DateTimeField(blank=True, null=True)
    email_confirmed = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'User'

    tracked_fields = ['is_active', 'email_confirmed']

    def __str__(self):
        return f"User {self.pk}: {self.email}"

    def save(self, *args, **kwargs):
        """
        You get an API key when you confirm your email address.

        >>> unconfirmed_user = getfixture('unconfirmed_user')
        >>> assert not unconfirmed_user.email_confirmed
        >>> with assert_raises(ObjectDoesNotExist):
        ...     unconfirmed_user.auth_token.key
        >>> unconfirmed_user.email_confirmed = True
        >>> unconfirmed_user.save(update_fields=['email_confirmed'])
        >>> assert unconfirmed_user.auth_token.key

        If you programmatically create a user with `email_confirmed=True`,
        for instance...

          -  in the Django admin
          -  manually via `User.object.create_[super]user`
          -  User().save()
          -  via test fixture factories

        ...an API key will automatically be created.
        >>> fixture_user = getfixture('user')
        >>> manager_user = User.objects.create_user(email='test@api_key.com', password='pass', email_confirmed=True)
        >>> manual_user = User(email_confirmed=True); manual_user.save()
        >>> for user in [fixture_user, manager_user, manual_user]:
        ...     assert user.auth_token.key
        """
        create_token = (not self.pk or self.has_changed('email_confirmed')) and self.email_confirmed
        if self.has_changed('is_active') and not self.is_active:
            self.deactivated_date = timezone.now()
        super().save(*args, **kwargs)
        if create_token:
            self.get_new_token()

    def get_new_token(self):
        try:
            self.auth_token.delete()
        except ObjectDoesNotExist:
            pass
        return Token.objects.create(user=self)

    def get_short_name(self):
        return self.email.split('@')[0]

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.get_short_name()

    def send_confirmation_email(self, request):
        # Send verify-email-address email.
        # This uses the forgot-password flow; logic is borrowed from auth_forms.PasswordResetForm.save()
        confirmation_link = request.build_absolute_uri(reverse('password_reset_confirm', args=[
            urlsafe_base64_encode(force_bytes(self.pk)),
            default_token_generator.make_token(self),
        ]))
        send_template_email(
            'Please confirm your email address',
            'email/confirm_email.txt',
            {'confirmation_link': confirmation_link},
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
        )
