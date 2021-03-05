from celery import shared_task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from celery.signals import task_failure
import os
import requests
import socket
import threading
from time import sleep
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import mail_admins

from .models import CaptureJob, Archive, WebhookSubscription
from .serializers import ReadOnlyCaptureJobSerializer, SimpleWebhookSubscriptionSerializer
from .storages import get_storage
from .utils import (validate_and_clean_url, get_file_hash, parse_querystring,
    datetime_from_timestamp, sign_data, send_template_email
)

import logging
logger = logging.getLogger(__name__)


### ERROR REPORTING ###

@task_failure.connect()
def celery_task_failure_email(**kwargs):
    """
    Celery 4.0+ has no method to send emails on failed tasks.
    This event handler provides equivalent functionality to Celery < 4.0,
    and reports truly failed tasks, like those terminated after CELERY_TASK_TIME_LIMIT
    and those that throw uncaught exceptions.
    From https://github.com/celery/celery/issues/3389

    Given:
    >>> _, mocker = [getfixture(i) for i in ['celery_worker', 'mocker']]
    >>> sleep = mocker.patch('main.tasks.sleep')
    >>> mailer = mocker.patch('main.tasks.mail_admins')

    Patch the task so that it errors, and then run in:
    >>> sleep.side_effect = lambda seconds: 1/0
    >>> _ = demo_scheduled_task.apply_async(kwargs={'pause_for_seconds': 1})

    Wait for the task to execute and return (without using the patched copy of sleep)
    >>> import time; time.sleep(1)

    Observe that an error email was sent, as expected.
    >>> mailer.assert_called_once()
    """
    subject = "[{queue_name}@{host}] Error: Task {sender.name} ({task_id}): {exception}".format(
        queue_name='celery',
        host=socket.gethostname(),
        **kwargs
    )

    message = """Task {sender.name} with id {task_id} raised exception:
{exception!r}
Task was called with args: {args} kwargs: {kwargs}.
The contents of the full traceback was:
{einfo}
    """.format(
        **kwargs
    )
    mail_admins(subject, message)


### CAPTURE HELPERS ###

class HaltCaptureException(Exception):
    """
    An exception we can trigger to halt capture and release all involved resources.
    """
    pass


class BrowsertrixLifeCycleThread(threading.Thread):
    """
    """
    def __init__(self, container, timeout, *args, **kwargs):
        self.container = container
        self.timeout = timeout
        self.timedout = False
        self.result = {}
        self.status = None
        self.exit_code = None
        self.stderr = None
        super().__init__(*args, **kwargs)

    def run(self):
        try:
            self.result = self.container.wait(timeout=self.timeout)
        except requests.exceptions.ReadTimeout:
            self.timedout = True
            # For now, just kill the container. We likely want something gentler,
            # that requests Browsertrix stop recording and finalize the record,
            # and then a second timeout, so as to preserve partial capture results.
            self.container.stop(timeout=0)
            self.result = self.container.wait(timeout=1)
        finally:
            self.container.reload()
            self.status = self.container.status
            self.exit_code = self.result.get('StatusCode')
            self.stderr = self.container.logs(stdout=False)


def inc_progress(capture_job, inc, description):
    capture_job.inc_progress(inc, description)
    logger.info(f"{capture_job} step {capture_job.step_count}: {capture_job.step_description}")


def clean_up_failed_captures():
    """
    Clean up any existing jobs that are marked in_progress but must have timed out by now, based on our hard timeout
    setting.
    """
    # use database time with a custom where clause to ensure consistent time across workers
    for capture_job in CaptureJob.objects.filter(status=CaptureJob.Status.IN_PROGRESS).extra(
            where=[f"capture_start_time < now() - make_interval(secs => {settings.CELERY_TASK_TIME_LIMIT})"]
    ):
        capture_job.mark_failed("Timed out.")


### TASKS ###

@shared_task
def demo_scheduled_task(pause_for_seconds=0):
    """
    A demo task, scheduled to run once a minute dev. To see it in action,
    set CELERY_TASK_ALWAYS_EAGER = False in setting.py before running `fab-run`.
    """
    if pause_for_seconds:
        sleep(pause_for_seconds)
    return "Celerybeat is working!"


@shared_task
def run_next_capture():
    """
    """
    clean_up_failed_captures()

    capture_job = CaptureJob.get_next_job(reserve=True)
    if not capture_job:
        logger.debug('No jobs waiting!')
        return

    try:
        inc_progress(capture_job, 0, "Validating.")
        try:
            capture_job.validated_url = validate_and_clean_url(capture_job.requested_url)
        except ValidationError as e:
            capture_job.mark_invalid({"requested_url": e.messages})
            raise HaltCaptureException
        capture_job.save()

        # basic setup
        client = None
        container = None
        browsertrix_life_cycle_thread = None
        have_archive = False
        filename = f'{uuid.uuid4()}.wacz'
        browsertrix_outputfile = f'{settings.SERVICES_DIR}/browsertrix/data/{filename}'

        inc_progress(capture_job, 1, "Connecting to Docker.")
        import docker  # noqa: import docker here, so that it only needs to be running on capture workers
        client = docker.from_env()

        inc_progress(capture_job, 1, "Creating browsertrix container.")
        container = client.containers.create(
            settings.BROWSERTRIX_IMAGE,
            environment=[
                f'DATA_DIR={settings.BROWSERTRIX_INTERNAL_DATA_DIR}'
            ],
            volumes={
                settings.BROWSERTRIX_HOST_DATA_DIR : {
                    'bind': settings.BROWSERTRIX_INTERNAL_DATA_DIR,
                },
                settings.BROWSERTRIX_ENTRYPOINT : {
                    'bind': '/entrypoint.sh'
                }
            },
            entrypoint='/entrypoint.sh',
            command=f'for i in 1 2 3 4 5; do (echo status $i; sleep 1); done; cp {settings.BROWSERTRIX_INTERNAL_DATA_DIR}/examples/$(ls {settings.BROWSERTRIX_INTERNAL_DATA_DIR}/examples | shuf -n 1) {settings.BROWSERTRIX_INTERNAL_DATA_DIR}/{filename}',
            detach=True
        )

        inc_progress(capture_job, 1, "Starting browsertrix.")
        container.start()
        browsertrix_life_cycle_thread = BrowsertrixLifeCycleThread(container, settings.BROWSERTRIX_TIMEOUT_SECONDS, name="browsertrix_return")
        browsertrix_life_cycle_thread.start()
        stdout_stream = container.logs(stderr=False, stream=True)
        for msg in stdout_stream:
            # the life cycle thread should take care of killing browsertrix, so this isn't infinite...
            # but let's definitely ensure that's the case, including in weird hanging conditions.
            # should also look into whether the browsertrix container needs init, and whether it passes signals correctly, etc.
            # see also https://github.com/moby/moby/issues/37663.
            msg = str(msg, 'utf-8').strip()
            if True:
                # if the msg matches some expectation (I'm presuming output will be noisy),
                # indicate we've reached the next step of the capture
                inc_progress(capture_job, 1, f"Browsertrix: {msg}.")
            else:
                logger.debug(msg)

        browsertrix_life_cycle_thread.join()
        if browsertrix_life_cycle_thread.exit_code != 0:
            # see there's anything we can salvage
            if os.path.isfile(browsertrix_outputfile):
                # should probably also make sure its a valid wacz?
                # a likely advantage of warcs over wacz is that you can still play back a truncated warc
                have_archive = True
            # this is NOT how we want to handle the verbose output of stderr. What's the best way to log?
            # send a special error email?
            logger.error(f"Browsertrix exited with {browsertrix_life_cycle_thread.exit_code}: {browsertrix_life_cycle_thread.stderr}")
            raise HaltCaptureException
        have_archive = True

    except HaltCaptureException:
        logger.info("HaltCaptureException thrown.")
    except SoftTimeLimitExceeded:
        logger.warning(f"Soft timeout while capturing job {capture_job.id}.")
        # might include code here for politely asking Browsertrix to stop recording.
    except:  # noqa
        logger.exception(f"Exception while capturing job {capture_job.id}:")
    finally:
        try:
            if container:
                # For now, just kill the container. We might want something gentler.
                container.remove(force=True)
            if client:
                client.close()
            if have_archive:
                archive = Archive(capture_job=capture_job)
                with open(browsertrix_outputfile , 'rb') as file:
                    inc_progress(capture_job, 1, "Processing archive.")
                    archive.hash, archive.hash_algorithm = get_file_hash(file)
                    assert not file.read()
                    archive.warc_size = file.tell()

                    inc_progress(capture_job, 1, "Saving archive.")
                    file.seek(0)
                    storage = get_storage()
                    filename = storage.save(filename, file)
                    archive.download_url = storage.url(filename)
                    archive.download_expiration_timestamp = datetime_from_timestamp(parse_querystring(archive.download_url)['Expires'][0])
                archive.save()
                capture_job.mark_completed()
                logger.info("Capture succeeded.")
            else:
                logger.info("Capture failed.")
        except:  # noqa
            logger.exception(f"Exception while finishing job {capture_job.id}:")
        finally:
            if capture_job.status == CaptureJob.Status.IN_PROGRESS:
                capture_job.mark_failed('Failed during capture.')
    run_next_capture.apply_async()

@shared_task(bind=True, max_retries=settings.WEBHOOK_MAX_RETRIES)
def dispatch_webhook(self, subscription_id, capture_job_id):
    """
    """
    if not settings.DISPATCH_WEBHOOKS:
        logger.debug(f'Webhooks notifications are disabled: not sending POST for subscription {subscription_id}, capture job {capture_job_id}.')
        return

    subscription = WebhookSubscription.objects.get(id=subscription_id)
    capture_job = CaptureJob.objects.filter(id=capture_job_id).select_related('archive').first()

    payload = {
        "webhook": SimpleWebhookSubscriptionSerializer(subscription).data,
        "capture_job": ReadOnlyCaptureJobSerializer(capture_job).data
    }
    try:
        response = requests.post(
            url=subscription.callback_url,
            json=payload,
            headers={'x-hook-signature': sign_data(payload, subscription.signing_key, subscription.signing_key_algorithm)},
            timeout=20,
            allow_redirects=False
        )
        assert response.status_code in [200, 204], response.status_code
    except (requests.RequestException, AssertionError):
        logger.info(f'Delivery of webhook notification for subscription {subscription_id}, capture job {capture_job_id} failed ({self.request.retries}/{self.max_retries}).')
        try:
            # retry with exponential backoff, up to settings.WEBHOOK_MAX_RETRIES times
            self.retry(countdown=2**self.request.retries)
        except MaxRetriesExceededError:
            logger.warning(f'Delivery of webhook notification for subscription {subscription_id}, capture job {capture_job_id} permanently failed.')
            send_template_email(
                f"[ALERT] Your {settings.APP_NAME} webhook notification failed.",
                'email/webhook_failed.txt',
                {"subscription": subscription, "capture_job": capture_job},
                settings.DEFAULT_FROM_EMAIL,
                [subscription.user.email],
            )
