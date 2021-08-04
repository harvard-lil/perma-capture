import base64
import boto3
from collections import defaultdict
from contextlib import contextmanager
from datetime import timezone as tz, timedelta
from distutils.sysconfig import get_python_lib
import docker
import factory
from faker import Faker
import humps
import inspect
import os
import pytest
import random
import requests
import re

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models import signals
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from django.db.backends import utils as django_db_utils

from main.models import User, WebhookSubscription, Archive, CaptureJob, Profile, ProfileCaptureJob


# This file defines test fixtures available to all tests.
# To see available fixtures run pytest --fixtures

TEST_FILE_DIR = os.path.abspath(os.path.join(settings.BASE_DIR, '../main/test/files'))

fake = Faker()

### pytest configuration ###

def pytest_addoption(parser):
    """
    Custom command line options.
    """
    parser.addoption(
        "--write-files",
        default=False,
        action='store_true',
        help="Tests that compare to files on disk should instead update those files"
    )


### internal helpers ###

# functions used within this file to set up fixtures

def register_factory(cls):
    """
    Decorator to take a factory class and inject test fixtures. For example,
        @register_factory
        class UserFactory
    will inject the fixtures "user_factory" (equivalent to UserFactory) and "user" (equivalent to UserFactory()).
    This is basically the same as the @register decorator provided by the pytest_factoryboy package,
    but because it's simpler it seems to work better with RelatedFactory and SubFactory.
    """
    snake_case_name = humps.decamelize(cls.__name__)

    @pytest.fixture
    def factory_fixture(db):
        return cls

    @pytest.fixture
    def instance_fixture(db):
        return cls()

    globals()[snake_case_name] = factory_fixture
    globals()[snake_case_name.rsplit('_factory', 1)[0]] = instance_fixture

    return cls


### non-model fixtures ###

@pytest.fixture(autouse=True, scope='function')
def cleanup_storage():
    """
    Empty the configured storage after each test, so that it's fresh each time, just like the test database.
    """
    yield
    storage = boto3.resource('s3',
        endpoint_url=settings.DEFAULT_S3_STORAGE['endpoint_url'],
        aws_access_key_id=settings.DEFAULT_S3_STORAGE['access_key'],
        aws_secret_access_key=settings.DEFAULT_S3_STORAGE['secret_key']
    ).Bucket(settings.DEFAULT_S3_STORAGE['bucket_name'])
    storage.objects.delete()


@pytest.fixture(scope='function')
def assert_num_queries(pytestconfig, monkeypatch):
    """
    Fixture based on django_assert_num_queries, but modified to specify query type and print the line of code
    that triggered the query.
    Provide a context manager to assert which queries will be run by a block of code. Example:
        def test_foo(assert_num_queries):
            with assert_num_queries(select=1, update=2):
                # run one select and two updates
    Suggestions for adding this to existing tests: start by running with counts empty:
        with assert_num_queries():
    Run the test as:
        pytest -k test_foo -v
    Ensure that the queries run are as expected, then insert the correct counts based on the error message.
    """
    python_lib_path = get_python_lib()

    class TracingDebugWrapper(django_db_utils.CursorDebugWrapper):
        def log_message(self, message):
            django_db_utils.logger.debug(message)

        def get_userland_stack_frame(self, stack):
            for stack_frame in stack[2:]:
                if stack_frame.code_context and not stack_frame.filename.startswith(python_lib_path):
                    return stack_frame
            return None

        def capture_stack(self):
            stack = inspect.stack()
            userland_stack_frame = self.get_userland_stack_frame(stack)

            self.db.queries_log[-1].update({
                'stack': stack,
                'userland_stack_frame': userland_stack_frame,
            })

            if userland_stack_frame:
                self.log_message("Previous SQL query called by %s:%s:\n%s" % (
                    userland_stack_frame.filename,
                    userland_stack_frame.lineno,
                    userland_stack_frame.code_context[0].rstrip()))

        def execute(self, *args, **kwargs):
            try:
                return super().execute(*args, **kwargs)
            finally:
                self.capture_stack()

        def executemany(self, *args, **kwargs):
            try:
                return super().executemany(*args, **kwargs)
            finally:
                self.capture_stack()

    monkeypatch.setattr(BaseDatabaseWrapper, 'make_debug_cursor', lambda self, cursor: TracingDebugWrapper(cursor, self))

    @contextmanager
    def _assert_num_queries(db='default', **expected_counts):
        conn = connections[db]
        with CaptureQueriesContext(conn) as context:
            yield
            query_counts = defaultdict(int)
            for q in context.captured_queries:
                query_type = q['sql'].split(" ", 1)[0].lower()
                if query_type not in ('savepoint', 'release', 'set', 'show'):
                    query_counts[query_type] += 1
            if expected_counts != query_counts:
                msg = "Unexpected queries: expected %s, got %s" % (expected_counts, dict(query_counts))
                if pytestconfig.getoption('verbose') > 0:
                    msg += '\n\nQueries:\n========\n\n'
                    for q in context.captured_queries:
                        stack_frames = q['stack'] if pytestconfig.getoption("verbose") > 1 else [q['userland_stack_frame']] if q['userland_stack_frame'] else []
                        for stack_frame in stack_frames:
                            msg += "%s:%s:\n%s\n" % (stack_frame.filename, stack_frame.lineno, stack_frame.code_context[0].rstrip())
                        short_sql = re.sub(r'\'.*?\'', "'<str>'", q['sql'], flags=re.DOTALL)
                        msg += "%s\n\n" % short_sql
                else:
                    msg += " (add -v option to show queries, or -v -v to show queries with full stack trace)"
                pytest.fail(msg)

    return _assert_num_queries


@pytest.fixture
def reset_sequences(django_db_reset_sequences):
    """
    Reset database IDs and Factory sequence IDs. Use this if you need to have predictable IDs between runs.
    This fixture must be included first (before other fixtures that use the db).
    """
    for factory_class in globals().values():
        if inspect.isclass(factory_class) and issubclass(factory_class, factory.Factory):
            factory_class.reset_sequence(force=True)


@pytest.fixture
def client():
    """
    A version of the Django test client that allows us to specify a user login for a particular request with an
    `as_user` parameter, like `client.get(url, as_user=user).
    """
    from django.test import Client
    session_key = settings.SESSION_COOKIE_NAME
    class UserClient(Client):
        def request(self, *args, **kwargs):
            as_user = kwargs.pop('as_user', None)
            if as_user:
                # If as_user is provided, store the current value of the session cookie, call force_login, and then
                # reset the current value after the request is over.
                previous_session = self.cookies.get(session_key)
                self.force_login(as_user)
                try:
                    return super().request(*args, **kwargs)
                finally:
                    if previous_session:
                        self.cookies[session_key] = previous_session
                    else:
                        self.cookies.pop(session_key)
            else:
                return super().request(*args, **kwargs)
    return UserClient()


@pytest.fixture(scope='session')
def celery_config():
    # NOTE:
    #
    # The `celery_worker` fixture appears to like to be included first...
    # otherwise DB-related weirdness happens during teardown.
    #
    # Also, when the `celery_worker` fixture is included, peculiar
    # (and seemingly spurious) DB-related warnings are sometimes
    # printed when tests fail... Very confusing when debugging!
    # Be sure to read all the way up, for the original assertion
    # failure, before wasting time investigating fixtures' DB access.
    return {
        'broker_url': settings.CELERY_BROKER_URL
    }


@pytest.fixture(scope='session')
def docker_client():
    image_details = settings.BROWSERTRIX_IMAGE.split(':')
    client = docker.from_env()
    client.images.pull(image_details[0], tag=image_details[1] if len(image_details) == 2 else None)
    yield client
    client.close()


### model factories ###

@register_factory
class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Sequence(lambda n: 'user%s@example.com' % n)
    is_active = True
    email_confirmed=True

    password = factory.PostGenerationMethodCall('set_password', 'pass')


@register_factory
class UnconfirmedUserFactory(UserFactory):
    email_confirmed=False


@register_factory
class DeactivatedUserFactory(UserFactory):
    is_active = False


@register_factory
class AdminUserFactory(UserFactory):
    is_staff = True
    is_superuser = True


@register_factory
class WebhookSubscriptionFactory(factory.DjangoModelFactory):
    class Meta:
        model = WebhookSubscription

    user = factory.SubFactory(UserFactory)
    callback_url = factory.Faker('url')


@pytest.fixture
def random_webhook_event():
    return random.choice(list(WebhookSubscription.EventType))


@pytest.fixture
def webhook_callback_factory(db, requests_mock):
    """
    Given:
    >>> webhook_callback_factory = getfixture('webhook_callback_factory')

    By default, mock the callback to return HTTP 200.
    >>> webhook, _ = webhook_callback_factory()
    >>> assert requests.post(webhook.callback_url).status_code == 200

    Status code can be customized.
    >>> webhook, _ = webhook_callback_factory(400)
    >>> assert requests.post(webhook.callback_url).status_code == 400
    """
    def func(status_code=200, **kwargs):
        webhook = WebhookSubscriptionFactory(**kwargs)
        mock = requests_mock.post(webhook.callback_url, status_code=status_code)
        return (webhook, mock)
    return func


@register_factory
class CaptureJobFactory(factory.DjangoModelFactory):
    class Meta:
        model = CaptureJob
        exclude = ('create_archive',)

    create_archive = True
    user = factory.SubFactory(UserFactory)


@register_factory
class InvalidCaptureJobFactory(CaptureJobFactory):
    requested_url = 'not-a-valid-url'
    status = CaptureJob.Status.INVALID
    message = {'url': ['Not a valid URL.']}


@register_factory
class PendingCaptureJobFactory(CaptureJobFactory):
    requested_url = factory.Faker('url')
    status = CaptureJob.Status.PENDING


@register_factory
class InProgressCaptureJobFactory(PendingCaptureJobFactory):
    status = CaptureJob.Status.IN_PROGRESS
    capture_start_time = factory.Faker('future_datetime', end_date='+1m', tzinfo=tz.utc)
    step_count = factory.Faker('pyfloat', min_value=1, max_value=10)
    step_description = factory.Faker('text', max_nb_chars=15)
    validated_url = factory.LazyAttribute(
        lambda o: o.requested_url
    )


@register_factory
class CompletedCaptureJobFactory(InProgressCaptureJobFactory):
    status = CaptureJob.Status.COMPLETED
    capture_end_time = factory.LazyAttribute(
        lambda o: o.capture_start_time + timedelta(seconds=factory.Faker('random_int', min=0, max=settings.CELERY_TASK_TIME_LIMIT).generate())
    )
    archive = factory.Maybe(
        'create_archive',
        yes_declaration=factory.RelatedFactory(
            'conftest.ArchiveFactory',
            factory_related_name='capture_job',
            create_capture_job=False,
            expired=factory.Faker('boolean', chance_of_getting_true=70)
        ),
        no_declaration=None
    )


@register_factory
class FailedCaptureJobFactory(CompletedCaptureJobFactory):
    status = CaptureJob.Status.FAILED
    message = {'error': ['Failed during capture.']}
    archive = None


@register_factory
class ArchiveFactory(factory.DjangoModelFactory):
    class Meta:
        model = Archive
        exclude = ('create_capture_job', 'user', 'expired')

    create_capture_job = True
    user = factory.Maybe(
        'create_capture_job',
        yes_declaration=factory.SubFactory(UserFactory),
        no_declaration=None
    )
    capture_job = factory.Maybe(
        'create_capture_job',
        yes_declaration=factory.SubFactory(
            CompletedCaptureJobFactory,
            user=factory.SelfAttribute('..user'),
            create_archive=False
        ),
        no_declaration=None
    )
    expired = False
    hash_algorithm = 'sha256'
    hash = factory.Faker('sha256')
    warc_size = factory.Faker('random_int', min=5000, max=200000000)
    download_expiration_timestamp = factory.Maybe(
        'expired',
        yes_declaration= factory.LazyFunction(
            lambda:  timezone.now() - timedelta(minutes=factory.Faker('random_int', min=1, max=60).generate())
        ),
        no_declaration=factory.LazyFunction(
            lambda:  timezone.now() + timedelta(minutes=settings.ARCHIVE_EXPIRES_AFTER_MINUTES)
        ),
    )
    download_url = factory.Maybe(
        'expired',
        yes_declaration=None,
        no_declaration=factory.LazyAttribute(
            lambda o: f"https://our-cloud-storage.com/{factory.Faker('uuid4').generate()}.wacz?params=for-presigned-download"
        )
    )
    created_with_profile = None


@register_factory
@factory.django.mute_signals(signals.post_save)
class NoSignalsArchiveFactory(ArchiveFactory):
    """
    So that we can test manually.
    """
    pass


# I'm defining this at the top-level scope so that it can be imported and used
# outside of the contexts of tests, for instance, in local development.
def create_capture_job(status=None, **kwargs):
    if status is None:
        status = random.choices(CaptureJob.Status.values)[0]
    if status not in CaptureJob.Status.values:
        raise ValueError(f"Status must be one of {CaptureJob.Status.values}")
    return globals()[f"{humps.pascalize(status)}CaptureJobFactory"](**kwargs)


@pytest.fixture
def capture_job_factory(db):
    """
    Return a factory function that makes a capture job for a user.

    Given:
    >>> capture_job_factory, user = [getfixture(f) for f in ['capture_job_factory', 'user']]

    You can create a capture job for a user with a specific status...
    >>> cj1 = capture_job_factory(user=user, status='in_progress')
    >>> cj2 = capture_job_factory(user=user, status='failed')
    >>> assert cj1.user == cj2.user == user
    >>> assert cj1.status == CaptureJob.Status.IN_PROGRESS
    >>> assert cj2.status == CaptureJob.Status.FAILED

    ...or, just let the code pick a random status.
    >>> cj3 = capture_job_factory(user=user)
    >>> assert cj3.user == user
    >>> assert cj3.status

    You can also let the code generate a new user.
    >>> existing_users = list(User.objects.all())
    >>> capture_job_with_new_user = capture_job_factory()
    >>> assert capture_job_with_new_user.user not in existing_users
    >>> assert User.objects.filter(pk=capture_job_with_new_user.user.pk).exists()
    """
    def func(status=None, **kwargs):
        return create_capture_job(status, **kwargs)
    return func


@pytest.fixture
def user_with_capture_jobs_factory(db):
    """
    Given:
    >>> user_capturejob_factory = getfixture('user_with_capture_jobs_factory')

    Generate a user with a random number of capture jobs.
    >>> user = user_capturejob_factory()
    >>> assert user.capture_jobs.exists()

    Generate a user with a specific number of capture jobs.
    >>> other_user = user_capturejob_factory(job_count=5)
    >>> assert other_user.capture_jobs.count() == 5
    """
    def func(user=None, job_count=None, **kwargs):
        if user is None:
            user = UserFactory()
        if job_count is None:
            job_count = factory.Faker('random_int', min=3, max=15).generate()
        for _ in range(job_count):
            create_capture_job(user=user, **kwargs)
        return user
    return func


@register_factory
@factory.django.mute_signals(signals.post_save)  # mute so that, if a profile capture job is created, the job isn't launched!
class ProfileFactory(factory.DjangoModelFactory):
    class Meta:
        model = Profile
        exclude = ('create_capture_job', 'obsolete')

    netloc = factory.LazyFunction(
        lambda: random.choice(list(settings.PROFILE_SECRETS.keys()))
    )
    headless = factory.Faker('boolean', chance_of_getting_true=50)
    username = factory.LazyAttribute(
        lambda o: settings.PROFILE_SECRETS[o.netloc]['user']
    )
    verified = factory.Faker('boolean', chance_of_getting_true=50)
    obsolete = False
    marked_obsolete = factory.Maybe(
        'obsolete',
        yes_declaration=factory.LazyFunction(
            lambda:  timezone.now() - timedelta(minutes=factory.Faker('random_int', min=1, max=60).generate())
        ),
        no_declaration=None
    )
    profile = factory.django.FileField(
        filename='profile.tar.gz',
        from_path=os.path.abspath(os.path.join(TEST_FILE_DIR, 'example-profile.tar.gz'))
    )
    create_capture_job = True
    profile_capture_job = factory.Maybe(
        'create_capture_job',
        yes_declaration=factory.SubFactory(
            'conftest.CompletedProfileCaptureJobFactory',
            netloc=factory.SelfAttribute('..netloc'),
            headless=factory.SelfAttribute('..headless'),
            profile__create_new=False
        ),
        no_declaration=None
    )


@register_factory
class UnverifiedProfileFactory(ProfileFactory):
    verified = False
    obsolete = False


@register_factory
class ActiveProfileFactory(ProfileFactory):
    verified = True
    obsolete = False


@register_factory
class ObsoleteProfileFactory(ProfileFactory):
    verified = True
    obsolete = True


@pytest.fixture()
def target_domains(settings, db):
    assert len(settings.TEST_CAPTURE_TARGET_DOMAINS) == 4
    for domain in settings.TEST_CAPTURE_TARGET_DOMAINS[1:]:
        settings.PROFILE_SECRETS[domain] = {
            'log_in_url': '',
            'user': fake.user_name(),
            'password': fake.password(length=12),
        }
    return {
        'no_profile': settings.TEST_CAPTURE_TARGET_DOMAINS[0],
        'unverified_profile': (settings.TEST_CAPTURE_TARGET_DOMAINS[1], UnverifiedProfileFactory(netloc=settings.TEST_CAPTURE_TARGET_DOMAINS[1])),
        'active_profile': (settings.TEST_CAPTURE_TARGET_DOMAINS[2], ActiveProfileFactory(netloc=settings.TEST_CAPTURE_TARGET_DOMAINS[2])),
        'obsolete_profile': (settings.TEST_CAPTURE_TARGET_DOMAINS[3], ObsoleteProfileFactory(netloc=settings.TEST_CAPTURE_TARGET_DOMAINS[3])),
    }


@register_factory
@factory.django.mute_signals(signals.post_save)  # mute so that the job isn't launched!
class ProfileCaptureJobFactory(factory.DjangoModelFactory):
    class Meta:
        model = ProfileCaptureJob
        exclude = ('has_screenshot',)

    netloc = factory.LazyFunction(
        lambda: random.choice(list(settings.PROFILE_SECRETS.keys()))
    )
    headless = factory.Faker('boolean', chance_of_getting_true=50)
    has_screenshot = False


@register_factory
class PendingProfileCaptureJobFactory(ProfileCaptureJobFactory):
    status = CaptureJob.Status.PENDING


@register_factory
class InProgressProfileCaptureJobFactory(ProfileCaptureJobFactory):
    status = CaptureJob.Status.IN_PROGRESS
    capture_start_time = factory.Faker('future_datetime', end_date='+1m', tzinfo=tz.utc)
    step_count = factory.Faker('pyfloat', min_value=1, max_value=10)
    step_description = factory.Faker('text', max_nb_chars=15)


@register_factory
class CompletedProfileCaptureJobFactory(InProgressProfileCaptureJobFactory):
    status = CaptureJob.Status.COMPLETED
    capture_end_time = factory.LazyAttribute(
        lambda o: o.capture_start_time + timedelta(seconds=factory.Faker('random_int', min=0, max=settings.CELERY_TASK_TIME_LIMIT).generate())
    )
    has_screenshot = factory.Faker('boolean', chance_of_getting_true=90)
    screenshot = factory.Maybe(
        'has_screenshot ',
        yes_declaration=factory.django.FileField(
            filename='screenshot.png',
            # 1 pixel transparent PNG
            data=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=')
        ),
        no_declaration=None
    )

    @factory.post_generation
    def profile(self, create, extracted, **kwargs):
        """
        Create profiles as a post-generation hook instead of a RelatedFactory so that the CaptureJob
        always exists in the actual DB before the Profile is generated, working around some weirdness
        otherwise encountered by Factory Boy apropos of the FileField and profile_job_directory.
        """

        if not create:
            # Simple build, do nothing.
            return

        # Use a passed-in profile, if passed in,
        # Otherwise, check to see if a profile is required, and create as necessary.
        self.refresh_from_db()
        if extracted:
            self.profile = extracted
        if 'create_new' not in kwargs or kwargs.get('create_new'):
            try:
                self.profile
            except ObjectDoesNotExist:
                ProfileFactory(
                    profile_capture_job_id=self.id,
                    create_capture_job=False,
                    obsolete=factory.Faker('boolean', chance_of_getting_true=70)
                )
        self.refresh_from_db()

@register_factory
class FailedProfileCaptureJobFactory(CompletedProfileCaptureJobFactory):
    status = CaptureJob.Status.FAILED
    message = {'error': ['Failed during capture.']}
    profile = None


# I'm defining this at the top-level scope so that it can be imported and used
# outside of the contexts of tests, for instance, in local development.
def create_profile_capture_job(status=None, **kwargs):
    if status is None:
        status = random.choices([status for status in ProfileCaptureJob.Status.values if status != 'invalid'])[0]
    if status not in ProfileCaptureJob.Status.values:
        raise ValueError(f"Status must be one of {ProfileCaptureJob.Status.values}")
    return globals()[f"{humps.pascalize(status)}ProfileCaptureJobFactory"](**kwargs)


@pytest.fixture
def profile_capture_job_factory(target_domains):
    """
    Return a factory function that makes a profile capture job.

    Given:
    >>> [profile_capture_job_factory] = [getfixture(f) for f in ['profile_capture_job_factory']]

    You can create a capture job with a specific status...
    >>> cj1 = profile_capture_job_factory(status='in_progress')
    >>> cj2 = profile_capture_job_factory(status='failed')
    >>> cj3 = profile_capture_job_factory(status='completed')
    >>> assert cj1.status == CaptureJob.Status.IN_PROGRESS
    >>> assert cj2.status == CaptureJob.Status.FAILED
    >>> assert cj3.status == CaptureJob.Status.COMPLETED

    ...or, just let the code pick a random status.
    >>> cj4 = profile_capture_job_factory()
    >>> assert cj4.status

    The capture jobs all target supported domains:
    >>> try:
    ...     cj1.full_clean() and cj2.full_clean() and cj3.full_clean()
    ... except ValidationError:
    ...     assert False

    Only successful jobs have associated profile objects.
    >>> for job in (cj1, cj2):
    ...     with pytest.raises(ObjectDoesNotExist):
    ...         job.profile
    >>> assert cj3.profile
    """
    def func(status=None, **kwargs):
        return create_profile_capture_job(status, **kwargs)
    return func
