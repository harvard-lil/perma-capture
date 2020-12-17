from collections import defaultdict
from contextlib import contextmanager
from datetime import timezone as tz
from distutils.sysconfig import get_python_lib
import factory
import inspect
from io import BytesIO
from json.decoder import JSONDecodeError
import pytest
import random
import requests
import re

from django.conf import settings
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from django.db.backends import utils as django_db_utils

from main.models import User, WebhookSubscription


# This file defines test fixtures available to all tests.
# To see available fixtures run pytest --fixtures


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
    camel_case_name = re.sub('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))', r'_\1', cls.__name__).lower()

    @pytest.fixture
    def factory_fixture(db):
        return cls

    @pytest.fixture
    def instance_fixture(db):
        return cls()

    globals()[camel_case_name] = factory_fixture
    globals()[camel_case_name.rsplit('_factory', 1)[0]] = instance_fixture

    return cls


### non-model fixtures ###

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


### capture service mocks ###

@register_factory
class CaptureJobData(factory.Factory):
    class Meta:
        model = dict
        exclude = ('user',)

    jobid = factory.Faker('uuid4')
    user = factory.SubFactory(UserFactory)
    userid = factory.LazyAttribute(lambda o: str(o.user.id))
    capture_url = factory.Faker('url')
    use_embeds = factory.Faker('boolean')
    user_tag = factory.Faker('text', max_nb_chars=15)
    start_time = factory.Faker('iso8601', tzinfo=tz.utc)
    elapsed_time = factory.Faker('iso8601', tzinfo=tz.utc)
    access_url = factory.LazyAttribute(
        lambda o: factory.Faker('url').generate() if o.status == 'Complete' else None
    )
    status = factory.Faker('random_element', elements=('In progress', 'Failed', 'Complete', 'Unknown'))


@register_factory
class CaptureRequestData(factory.Factory):
    class Meta:
        model = dict
        exclude = ('user',)

    user = factory.SubFactory(UserFactory)
    urls = factory.LazyAttribute(lambda o: len(o.jobids))
    jobids = factory.LazyAttribute(lambda o: [job['jobid'] for job in CaptureJobData.create_batch(
        factory.Faker('random_digit_not_null').generate(),
        user=o.user
    )])


@register_factory
class CaptureListData(factory.Factory):
    class Meta:
        model = dict
        exclude = ('user',)

    user = factory.SubFactory(UserFactory)
    jobs = factory.LazyAttribute(lambda o: CaptureJobData.create_batch(
        factory.Faker('random_digit_not_null').generate(),
        user=o.user
    ))


@register_factory
class WebhookCallbackFactory(factory.Factory):
    class Meta:
        model = dict
        exclude = ('user', 'capture_job')

    user = factory.SubFactory(UserFactory)
    capture_job = factory.SubFactory(
        CaptureJobData,
        user=factory.SelfAttribute('..user')
    )
    jobid = factory.LazyAttribute(lambda o: o.capture_job['jobid'])
    userid = factory.LazyAttribute(lambda o: str(o.user.id))
    url = factory.Faker('url')
    access_url = factory.Faker('url')
    user_data_field = factory.LazyFunction(lambda: str(timezone.now().timestamp()))


class MockResponse:

    def __init__(self, *args, **kwargs):
        self.code = kwargs.get('code', 200)
        self.generate_data = kwargs.get('generate_data', lambda: {'key': 'value'})

    @property
    def status_code(self):
        return self.code

    def json(self):
        return self.generate_data()

    def iter_content(self, chunk_size=1, decode_unicode=False):
        """
        Adapted from https://github.com/psf/requests/blob/8149e9fe54c36951290f198e90d83c8a0498289c/requests/models.py#L732
        """
        file = BytesIO(b'Some file')
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            yield chunk


@pytest.fixture()
def mock_create_captures(mocker):
    def response(*args, **kwargs):
        return MockResponse(
            *args,
            code=201,
            generate_data=CaptureRequestData,
            **kwargs
        )
    mock_request = mocker.patch('requests.request', auto_spec=True)
    mock_request.side_effect = response
    return mock_request


@pytest.fixture()
def mock_list_captures(mocker):
    def response(*args, **kwargs):
        return MockResponse(
            *args,
            generate_data=CaptureListData,
            **kwargs
        )
    mock_request = mocker.patch('requests.request', auto_spec=True)
    mock_request.side_effect = response
    return mock_request


@pytest.fixture()
def mock_delete_capture(mocker):
    def raise_expected_json_exception():
        raise JSONDecodeError('Expected value', '', 0)

    def response(*args, **kwargs):
        return MockResponse(
            *args,
            code=204,
            generate_data=raise_expected_json_exception,
            **kwargs
        )
    mock_request = mocker.patch('requests.request', auto_spec=True)
    mock_request.side_effect = response
    return mock_request


@pytest.fixture()
def mock_download(monkeypatch):
    def response(*args, **kwargs):
        return MockResponse(*args, **kwargs)
    monkeypatch.setattr(requests, 'get', response)
