from contextlib import contextmanager
from functools import wraps
import os
import signal
import subprocess
import sys

from fabric.decorators import task
from fabric.operations import local

import django

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


@task(alias='run')
@setup_django
def run_django(port=None):  # pragma: no cover
    if port is None:
        port = "0.0.0.0:8000" if os.environ.get('DOCKERIZED') else "127.0.0.1:8000"

    from django.conf import settings
    if settings.CELERY_TASK_ALWAYS_EAGER:
        local(f'python manage.py runserver {port}')
    else:
        with open_subprocess("watchmedo auto-restart -d ./ -p '*.py' -R -- celery worker --app config.celery.app --loglevel=info -Q celery,background -B -n w1@%h"):
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
def run_fullstack(django_port=None):
    frontend_proc = subprocess.Popen("yarn && yarn dev", cwd="./frontend", shell=True, stdout=sys.stdout, stderr=sys.stderr)
    try:
        run_django(django_port)
    finally:
        os.kill(frontent_proc.pid, signal.SIGKILL)
