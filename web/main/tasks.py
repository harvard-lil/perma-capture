from celery import shared_task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded, Retry
from celery.signals import task_failure
from datetime import timedelta
import docker
import json
import re
import requests
import socket
import threading
from time import sleep
import zipfile

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.mail import mail_admins
from django.utils import timezone

from .models import CaptureJob, Archive, WebhookSubscription
from .serializers import ReadOnlyCaptureJobSerializer, SimpleWebhookSubscriptionSerializer
from .storages import get_archive_storage
from .utils import (validate_and_clean_url, extract_file_from_container, extract_files_from_container,
    get_file_hash, parse_querystring, datetime_from_timestamp, format_scoop_option, sign_data,
    is_valid_signature, send_template_email
)

from pytest import raises as assert_raises
from unittest.mock import call

from test.test_helpers import raise_on_call

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

    Patch the task so that it errors, and then run it:
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

class NoArchiveProduced(Exception):
    pass


class ScoopLifeCycleThread(threading.Thread):
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
        except requests.exceptions.ConnectionError:
            self.timedout = True
            # For now, just kill the container. We likely want something gentler,
            # that politely requests Browsertrix stop and finish up what it's doing,
            # and then a second timeout, so we can, for instance, preserve partial capture results.
            self.container.stop(timeout=0)
            self.result = self.container.wait(timeout=1)
        finally:
            try:
                # If the container has been forceably shut down by the main thread,
                # these calls will fail.
                self.container.reload()
                self.stderr = str(self.container.logs(stdout=False), 'utf-8')
            except requests.exceptions.RequestException:
                pass
            self.exit_code = self.result.get('StatusCode')
            self.status = self.container.status


def handle_scoop_msg(capture_job, msg, milestones='', info_events=''):
    """
    Reformat a logline from Scoop and log at the desired level, incrementing
    the process of the capture job if a "milestone" has been reached.
    """
    def tidy_message(message):
        cleaned = message
        remove_patterns = [
            r'^\[.*?\]',
            r'\s*INFO\s*',
            r'\s*STEP \[.*?\]:\s*'
        ]
        for pattern in remove_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        return cleaned

    # the docker library returns stdout as bytes
    msg = str(msg, 'utf-8')
    if msg:
        if any(milestone in msg for milestone in milestones):
            inc_progress(capture_job, 1, f"[Scoop] {tidy_message(msg)}.")
        elif any(event in msg for event in info_events):
            logger.info(f"{capture_job}: [Scoop] {tidy_message(msg)}")
        else:
            logger.debug(tidy_message(msg))


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
    Given:
    >>> target_domains, pending_capture_job_factory, docker_client, django_settings, mocker, caplog = [getfixture(i) for i in ['target_domains', 'pending_capture_job_factory', 'docker_client', 'settings', 'mocker', 'caplog']]
    >>> output_dir = f'{settings.SERVICES_DIR}/browsertrix/data/'
    >>> basic_domain = target_domains['basic_domain']

    Helpers:
    >>> orig_clean_up_failed = clean_up_failed_captures
    >>> mock_clean_up_failed = mocker.patch('main.tasks.clean_up_failed_captures')
    >>> mock_clean_up_failed.side_effect = orig_clean_up_failed

    >>> orig_inc_progress = inc_progress
    >>> mock_inc_progress = mocker.patch('main.tasks.inc_progress')
    >>> def run_test_capture(url, stop_before_step=None, capture_job_extra_kwargs=None):
    ...     if stop_before_step:
    ...         mock_inc_progress.side_effect = raise_on_call(orig_inc_progress, stop_before_step + 1, HaltCaptureException)
    ...     else:
    ...         mock_inc_progress.side_effect = orig_inc_progress
    ...     job = pending_capture_job_factory(requested_url=url, **capture_job_extra_kwargs if capture_job_extra_kwargs else {})
    ...     _ = run_next_capture.apply()
    ...     job.refresh_from_db()
    ...     return job

    >>> def assert_succeeded(job):
    ...     assert job.status == CaptureJob.Status.COMPLETED
    ...     assert job.step_description == 'Saving screenshot.'
    ...     assert job.capture_end_time
    ...     assert job.archive.size
    ...     assert job.archive.hash and job.archive.hash_algorithm
    ...     assert requests.get(job.archive.download_url).status_code == 200

    NO JOBS

    If there are no pending capture jobs, the task simply returns.
    >>> _ = run_next_capture.apply()
    >>> assert "No jobs" in caplog.text
    >>> caplog.clear()

    VALIDATION

    We perform some simple validation on the submitted URL.
    >>> invalid_urls = [
    ...     '',
    ...     'examplecom',
    ...     'https://www.ntanet.org/some-article.pdf\x01',
    ...     'file:///etc/passwd',
    ... ]
    >>> for url in invalid_urls:
    ...     job = run_test_capture(url)
    ...     assert job.status == CaptureJob.Status.INVALID
    ...     assert job.message['requested_url']
    ...     assert job.step_count == 0
    ...     assert job.step_description == 'Validating.'
    ...     assert job.capture_end_time


    We tidy up submitted URLs: stripping whitespace...
    >>> job = run_test_capture('   http://example.com   ', stop_before_step=1)
    >>> assert job.validated_url == 'http://example.com'

    ...and add http if the protocol is omitted.
    >>> job = run_test_capture('example.com', stop_before_step=1)
    >>> assert job.validated_url == 'http://example.com'

    SUCCESS

    A domain where logged-in capture is not supported:

    >>> job = run_test_capture(f'http://{basic_domain}')
    >>> assert_succeeded(job)

    FAILURE

    If an exception is thrown in the main thread while Scoop is working, we stop and clean up.
    >>> caplog.clear()
    >>> job = run_test_capture(basic_domain, stop_before_step=5)
    >>> assert job.status == CaptureJob.Status.FAILED
    >>> assert job.step_count == 4
    >>> assert '[Scoop]' in job.step_description
    >>> assert job.capture_end_time
    >>> assert caplog.records[-1].message == 'No jobs waiting!'
    >>> assert not docker_client.containers.list(all=True, filters={'ancestor': settings.SCOOP_IMAGE})

    If Scoop exceeds the maximum permitted time limit, we stop and clean up.
    >>> caplog.clear()
    >>> django_settings.SCOOP_FATAL_TIMEOUT_SECONDS = 1
    >>> job = run_test_capture('example.com')
    >>> assert job.status == CaptureJob.Status.FAILED
    >>> assert 'Scoop exited with 137' or 'Scoop exited with 143' in caplog.text  #  137 means SIGKILL, 143 means SIGTERM
    >>> assert not docker_client.containers.list(all=True, filters={'ancestor': settings.SCOOP_IMAGE})

    We clean up failed jobs before we get started.
    >>> assert mock_clean_up_failed.call_count > 0
    """

    # First, clean up failed captures, because their presence might affect the queue order.
    clean_up_failed_captures()

    # Retrieve the next job in the queue
    capture_job = CaptureJob.get_next_job(reserve=True)
    if not capture_job:
        logger.info('No jobs waiting!')
        return

    # Basic Setup
    client = None
    container = None
    scoop_life_cycle_thread = None

    try:
        inc_progress(capture_job, 0, "Validating.")
        try:
            capture_job.validated_url = validate_and_clean_url(capture_job.requested_url)
        except ValidationError as e:
            capture_job.mark_invalid({"requested_url": e.messages})
            raise HaltCaptureException
        capture_job.save()

        inc_progress(capture_job, 1, "Connecting to Docker.")
        client = docker.from_env()

        inc_progress(capture_job, 1, "Creating Scoop container.")
        archive = Archive(capture_job=capture_job)
        scoop_output_directory = "/tmp"
        scoop_capture_filename = archive.filename
        scoop_capture_full_path = f'/tmp/{scoop_capture_filename}'
        scoop_summary_filename = "summary.json"
        scoop_summary_full_path = f'/tmp/{scoop_summary_filename}'
        scoop_kwargs = {
            "output": scoop_capture_full_path,
            "json-summary-output": scoop_summary_full_path,
            "export-attachments-output": scoop_output_directory,
            "format": "wacz-with-raw" if capture_job.include_raw_exchanges else "wacz",
            "screenshot": capture_job.include_screenshot,
            "pdf-snapshot": capture_job.include_pdf_snapshot,
            "dom-snapshot": capture_job.include_dom_snapshot,
            "capture-video-as-attachment": capture_job.include_videos_as_attachment if settings.SCOOP_ALLOW_VIDEO_AS_ATTACHMENT else "false",
            "capture-certificates-as-attachment": capture_job.include_certificates_as_attachment,
            "provenance-summary": "true",
            "attachments-bypass-limits": "true",  # under discussion: splitting this into metadata attachments (always allowed) and contentful attachments (can be disallowed)
            "capture-timeout": settings.SCOOP_MAX_RECORDING_MILLISECONDS or "60000",
            "load-timeout": settings.SCOOP_MAX_PAGE_LOAD_MILLISECONDS or "20000",
            "network-idle-timeout": settings.SCOOP_MAX_NETWORK_IDLE_MILLISECONDS or "20000",
            "behaviors-timeout": settings.SCOOP_MAX_BROWSER_BEHAVIORS_MILLISECONDS or "20000",
            "capture-video-as-attachment-timeout": settings.SCOOP_MAX_VIDEO_AS_ATTACHMENT_MILLISECONDS or "30000",
            "capture-certificates-as-attachment-timeout": settings.SCOOP_MAX_CERTS_AS_ATTACHMENT_MILLISECONDS or "10000",
            "capture-window-x": "1600",
            "capture-window-y": "900",
            "max-capture-size": settings.SCOOP_MAX_RECORDING_SIZE or "209715200",
            "auto-scroll": "true",
            "auto-play-media": "true",
            "grab-secondary-resources": "true",
            "run-site-specific-behaviors": capture_job.run_site_specific_behaviors,
            "headless": capture_job.headless if settings.SCOOP_ALLOW_HEADFUL else "true",
            "user-agent-suffix": settings.SCOOP_USER_AGENT_SUFFIX,
            "blocklist": settings.SCOOP_CUSTOM_BLOCKLIST,
            "proxy-port": settings.SCOOP_PROXY_PORT,
            "log-level": settings.SCOOP_LOG_LEVEL
        }
        command = f'npx scoop "{capture_job.validated_url}" ' + " ".join(f"--{key} {format_scoop_option(value)}" for key, value in scoop_kwargs.items() if value)
        logger.info(f"Scoop command: '{command}'")

        container = client.containers.create(
            settings.SCOOP_IMAGE,
            shm_size='1GB',
            mem_limit='4GB',
            init=True,
            command=command,
            detach=True,
            network=settings.SCOOP_DOCKER_NETWORK or ''
        )

        inc_progress(capture_job, 1, "Starting Scoop.")
        container.start()
        scoop_life_cycle_thread = ScoopLifeCycleThread(container, settings.SCOOP_FATAL_TIMEOUT_SECONDS, name="scoop")
        scoop_life_cycle_thread.start()
        stdout_stream = container.logs(stderr=False, stream=True)
        for msg in stdout_stream:
            handle_scoop_msg(capture_job, msg,
                milestones=(
                    'STEP',
                    'Exporting capture',
                    'saved to disk'
                ),
                info_events=(
                    'WARN',
                    'ERROR',
                    'User Agent'
                    'captureTimeout',
                    'Indexing WARCS',
                    'Writing',
                    'Finalizing WACZ',
                    'WACZ was finalized',
                )
            )

        scoop_life_cycle_thread.join()
        if scoop_life_cycle_thread.exit_code != 0:
            # this is NOT how we want to handle the verbose output of stderr. What's the best way to log?
            # send a special error email?
            logger.error(f"Scoop exited with {scoop_life_cycle_thread.exit_code}: {scoop_life_cycle_thread.stderr}")
            raise HaltCaptureException

    except HaltCaptureException:
        logger.info("HaltCaptureException thrown.")
    except SoftTimeLimitExceeded:
        logger.warning(f"Soft timeout while capturing job {capture_job.id}.")
        # might include code here for politely asking Scoop to stop recording.
    except:  # noqa
        logger.exception(f"Exception while capturing job {capture_job.id}:")
    finally:
        try:
            if container:

                # For now, just kill the container. We might want something gentler.
                container.stop()

                try:
                    to_extract = [scoop_capture_filename, scoop_summary_filename]
                    with extract_files_from_container(to_extract, scoop_output_directory, container) as file_handles:

                        archive_file = file_handles[scoop_capture_filename]
                        summary_file = file_handles[scoop_summary_filename]

                        if not archive_file:
                            raise NoArchiveProduced(f"{scoop_capture_filename} not found.")

                        inc_progress(capture_job, 1, "Processing archive.")
                        archive.hash, archive.hash_algorithm = get_file_hash(archive_file)
                        assert not archive_file.read()
                        archive.size = archive_file.tell()
                        # Should we do validity checks of any kind? Save regardless? TBD.
                        archive_file.seek(0)
                        assert zipfile.is_zipfile(archive_file), "Invalid WACZ"
                        wacz = zipfile.ZipFile(archive_file)
                        with wacz.open('datapackage.json') as datapackage:
                            metadata = json.load(datapackage)
                            library = metadata['extras']['provenanceInfo']['software']
                            version = metadata['extras']['provenanceInfo']['version']
                            archive.datapackage = metadata
                            archive.capture_software = f"{library}: {version}"
                        with wacz.open('datapackage-digest.json') as datapackage_digest:
                            metadata = json.load(datapackage_digest)
                            archive.datapackage_digest = metadata['hash']

                        inc_progress(capture_job, 1, "Saving archive.")
                        archive_file.seek(0)
                        storage = get_archive_storage()
                        real_filename = storage.save(archive.filename, archive_file)
                        try:
                            assert real_filename == archive.filename
                        except AssertionError:
                            # This would only happen if we accidentally produce duplicate filenames, which
                            # shouldn't happen, since we include the capture job id. But, if it does, we'll
                            # want to know about it, so we can manually clean up the file after it expires.
                            logger.error(f'The archive for capture job {capture_job.id} has been saved as {real_filename}, not {archive.filename}.')

                        inc_progress(capture_job, 1, "Saving summary metadata.")
                        archive.summary = json.load(summary_file)
                        scoop_state = archive.summary['states'][archive.summary['state']]
                        if scoop_state == 'COMPLETE':
                            archive.partial_capture = False
                        elif scoop_state == 'PARTIAL':
                            archive.partial_capture = True
                        else:
                            logger.error(f"Capture Job {capture_job.id} produced artifacts but reports state '{scoop_state}': how did we find ourselves here?")

                    archive.download_url = storage.url(real_filename)
                    archive.download_expiration_timestamp = datetime_from_timestamp(parse_querystring(archive.download_url)['Expires'][0])
                    archive.save()

                    if capture_job.include_screenshot:
                        inc_progress(capture_job, 1, "Saving screenshot.")
                        screenshot_filename = archive.summary["attachments"].get("screenshot")
                        if screenshot_filename:
                            try:
                                with extract_file_from_container(screenshot_filename, f"{scoop_output_directory}/{screenshot_filename}", container) as screenshot_file:
                                    screenshot_file.seek(0)
                                    archive.screenshot = File(screenshot_file, screenshot_filename)
                                    archive.save(update_fields=["screenshot"])
                            except docker.errors.NotFound:
                                logger.info("No screenshot available.")
                        else:
                            logger.info("No screenshot available.")

                    capture_job.mark_completed()
                    logger.info("Capture succeeded.")
                except NoArchiveProduced:
                    logger.info("Capture failed.")

                container.remove(force=True)

            if client:
                client.close()

        except:  # noqa
            logger.exception(f"Exception while finishing job {capture_job.id}:")
        finally:
            if capture_job.status == CaptureJob.Status.IN_PROGRESS:
                capture_job.mark_failed('Failed during capture.')
    run_next_capture.apply_async()


@shared_task(bind=True, max_retries=settings.WEBHOOK_MAX_RETRIES)
def dispatch_webhook(self, subscription_id, capture_job_id):
    """
    Send a webhook notification to the requested callback.

    Given:
    >>> archive, webhook_callback_factory, django_settings, mocker, mailoutbox, caplog = [getfixture(i) for i in ['no_signals_archive', 'webhook_callback_factory', 'settings', 'mocker', 'mailoutbox', 'caplog']]

    We send a serialization of the webhook subscription and the capture job, and we
    include a signature of the payload in the HTTP headers. We expect a response with
    a status code of 200 or 204.

    >>> for status in [200, 204]:
    ...     webhook, mock = webhook_callback_factory(status)
    ...     _ = dispatch_webhook.apply([webhook.id, archive.capture_job.id])
    ...     payload =  mock.last_request.json()
    ...     assert all(key in payload for key in ['webhook', 'capture_job'])
    ...     assert is_valid_signature(mock.last_request.headers['x-hook-signature'], payload, webhook.signing_key, webhook.signing_key_algorithm)
    ...     assert f'Webhook notification for subscription {webhook.id}, capture job {archive.capture_job.id} delivered.' in caplog.text
    ...     caplog.clear()

    We retry if the callback sends an unexpected status code.

    >>> for status in [301, 302, 400, 401, 413, 500, 502]:
    ...     webhook, mock = webhook_callback_factory(status)
    ...     with assert_raises(Retry):
    ...         dispatch_webhook.apply([webhook.id, archive.capture_job.id])
    ...     assert mock.called

    If we hit the retry limit, we email the user to let them know their hook is
    failing, including the ID of the archive, so that they can use the API to
    retrieve its info and recover.

    >>> retry = mocker.patch.object(dispatch_webhook, 'retry')
    >>> retry.side_effect = MaxRetriesExceededError()
    >>> webhook, mock = webhook_callback_factory(502)
    >>> _ = dispatch_webhook.apply([webhook.id, archive.capture_job.id])
    >>> [email] = mailoutbox
    >>> assert "webhook notification failed" in email.subject
    >>> assert f"capture job {archive.capture_job.id}" in email.body
    >>> mock.reset()
    >>> caplog.clear()

    If necessary, the sendind of webhook notifications can be disabled via a Django setting.

    >>> django_settings.DISPATCH_WEBHOOKS = False
    >>> _ = dispatch_webhook.apply([webhook.id, archive.capture_job.id])
    >>> assert 'Webhooks notifications are disabled' in caplog.text
    >>> assert not mock.called
    """
    if not settings.DISPATCH_WEBHOOKS:
        logger.info(f'Webhooks notifications are disabled: not sending POST for subscription {subscription_id}, capture job {capture_job_id}.')
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
            return
    logger.info(f'Webhook notification for subscription {subscription_id}, capture job {capture_job_id} delivered.')


@shared_task(acks_late=True)
def clean_up_all_expired_archives(limit=None):
    """
    Launch jobs to clean up expired archives.

    Given:
    >>> archive_factory, mocker, caplog = [getfixture(i) for i in ['no_signals_archive_factory', 'mocker', 'caplog']]
    >>> fresh = archive_factory()
    >>> already_cleaned_up = archive_factory(expired=True)
    >>> ready_to_clean_up1 = archive_factory(expired=False, download_expiration_timestamp=timezone.now() - timedelta(seconds=5))
    >>> ready_to_clean_up2 = archive_factory(expired=False, download_expiration_timestamp=timezone.now() - timedelta(hours=1))
    >>> mock_clean_up = mocker.patch('main.tasks.clean_up_archive')

    Launch one job per expired archive....
    >>> _ = clean_up_all_expired_archives.apply()
    >>> assert 'Queued 2 expired archives' in caplog.text
    >>> assert mock_clean_up.mock_calls == [call.apply_async([ready_to_clean_up1.id]), call.apply_async([ready_to_clean_up2.id])]
    >>> caplog.clear()
    >>> mock_clean_up.reset_mock()

    ... optionally limiting the total number.
    >>> _ = clean_up_all_expired_archives.apply(kwargs={"limit": 1})
    >>> assert 'Queued 1 expired archive' in caplog.text
    >>> assert mock_clean_up.mock_calls == [call.apply_async([ready_to_clean_up1.id])]
    """
    archives = Archive.objects.expired()
    if limit:
        archives = archives[:limit]
    queued = 0
    for archive_id in archives.values_list('id', flat=True).iterator():
        clean_up_archive.apply_async([archive_id])
        queued = queued + 1
    logger.info(f"Queued {queued} expired archives for cleanup.")


@shared_task(acks_late=True)
def clean_up_archive(archive_id):
    """
    Delete the archive from storage and unset its download_url.

    Given:
    >>> archive_factory, mocker, caplog = [getfixture(i) for i in ['no_signals_archive_factory', 'mocker', 'caplog']]
    >>> archive = archive_factory()
    >>> already_cleaned_up_archive = archive_factory(expired=True)
    >>> mock_storage = mocker.patch('main.tasks.get_archive_storage')

    Delete the archive from storage and unset its download_url.
    >>> _ = clean_up_archive.apply([archive.id])
    >>> archive.refresh_from_db()
    >>> assert mock_storage.mock_calls[-1] ==  ('().delete', (archive.filename,), {})
    >>> assert not archive.download_url
    >>> mock_storage.reset_mock()
    >>> caplog.clear()

    If the archive has already been cleaned up, this is a noop.
    >>> _ = clean_up_archive.apply([already_cleaned_up_archive.id])
    >>> assert 'already cleaned up' in caplog.text
    >>> assert mock_storage.call_count == 0
    """
    archive = Archive.objects.get(id=archive_id)
    if not archive.download_url:
        logger.info(f"Archive {archive_id} already cleaned up.")
        return

    storage = get_archive_storage()
    storage.delete(archive.filename)

    archive.download_url = None
    archive.save()
