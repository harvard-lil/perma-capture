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
