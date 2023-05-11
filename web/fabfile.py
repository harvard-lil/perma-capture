from contextlib import contextmanager
import docker
from fabric.context_managers import shell_env
from functools import wraps
import os
import signal
import subprocess
import sys

from fabric.decorators import task
from fabric.operations import local

import django

import logging
logger = logging.getLogger(__name__)

### Helpers ###

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
_django_setup = False
def setup_django(func):  # pragma: no cover
    """
        For speed, avoid setting up django until we need it. Attach @setup_django to any tasks that rely on importing django packages.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        global _django_setup
        if not _django_setup:
            sys.path.insert(0, '')
            django.setup()
            _django_setup = True
        return func(*args, **kwargs)
    return wrapper


@contextmanager
def open_subprocess(command):  # pragma: no cover
    """ Call command as a subprocess, and kill when with block exits. """
    print("Starting: %s" % command)
    proc = subprocess.Popen(command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    try:
        yield
    finally:
        print("Killing: %s" % command)
        os.kill(proc.pid, signal.SIGKILL)


### Tasks ###

@task(alias='pip-compile')
def pip_compile(args=''):
    # run pip-compile
    # Use --allow-unsafe because pip --require-hashes needs all requirements to be pinned, including those like
    # setuptools that pip-compile leaves out by default.
    #
    # Example: fab pip-compile:args="--upgrade-package djangorestframework"
    command = ['pip-compile', '--generate-hashes', '--allow-unsafe']+args.split()
    print("Calling %s" % " ".join(command))
    subprocess.check_call(command, env=dict(os.environ, CUSTOM_COMPILE_COMMAND='fab pip-compile'))


def prepare_scoop(docker_client, path, tag, testing=False):
    def print_or_log(msg):
        """
        Unexpected print statements cause our doctests to fail,
        but are preferred in other contexts.
        """
        if testing:
            logger.info(msg)
        else:
            print(msg)

    try:
        docker_client.images.get(tag)
    except docker.errors.ImageNotFound:
        try:
            print_or_log(f"\n\n!!!! Attempting to pull {tag} from registry: may take a minute or two !!!\n\n")
            docker_client.images.pull("registry.lil.tools", tag=tag)
        except docker.errors.APIError:
            print_or_log(f"\n\n!!!! Pull unsuccessful. Building {tag}: may take a minute or two !!!\n\n")
            _image, _build_logs = docker_client.images.build(
                path=path,
                tag=tag,
                forcerm=True
            )
            print_or_log(f"\n\nFinished building {tag}.\n\n")


@task()
def set_up_scoop(path, tag, testing=False):
    docker_client = docker.from_env()
    prepare_scoop(docker_client, path, tag, testing)
    docker_client.close()


@task(alias='run')
@setup_django
def run_django(port=None):  # pragma: no cover
    if port is None:
        port = "0.0.0.0:8000" if os.environ.get('DOCKERIZED') else "127.0.0.1:8000"

    from django.conf import settings

    set_up_scoop(settings.SCOOP_BUILD_CONTEXT, settings.SCOOP_IMAGE)

    if settings.CELERY_TASK_ALWAYS_EAGER:
        local(f'python manage.py runserver {port}')
    else:
        with open_subprocess("watchmedo auto-restart -d ./ -p '*.py' -R -- celery -A config.celery.app worker --loglevel=info -Q celery,background -B -n w1@%h"):
            local(f'python manage.py runserver {port}')

@task()
@setup_django
def load_sample_capture_jobs(email=None, status=None, jobs=20):  # pragma: no cover
    """
    Using our test fixtures, load some sample capture jobs into the database.
    You may optionally specify the associated user, the desired status of the jobs,
    and the number of capture jobs to create.

    If you do not specify a user, one will be selected at random: you must create at least
    one user before running.

    Sample Invocations:
    fab load_sample_capture_jobs
    fab load_sample_capture_jobs:email=test_admin_user@example.com
    fab load_sample_capture_jobs:email=test_admin_user@example.com,status=completed,jobs=3
    """
    from conftest import create_capture_job
    from main.models import User

    if not User.objects.exists():
        raise Exception('You must create at least one user before loading sample capture jobs.')

    kwargs = {}
    if email:
        kwargs['user'] = User.objects.get(email=email)
    else:
        kwargs['user'] = User.objects.order_by("?").first()
    if status:
        kwargs['status'] = status
    for _ in range(int(jobs)):
        print(create_capture_job(**kwargs))

@task
@setup_django
def run_fullstack(django_port=None):
    from django.conf import settings
    frontend_proc = subprocess.Popen(f'yarn && yarn dev --port {settings.VITE_PORT}', cwd="./frontend", shell=True, stdout=sys.stdout, stderr=sys.stderr)
    try:
        with shell_env(VITE_DONT_USE_MANIFEST='true'):
            run_django(django_port)
    finally:
        os.kill(frontend_proc.pid, signal.SIGKILL)
