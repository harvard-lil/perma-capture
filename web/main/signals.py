from .models import WebhookSubscription
from .tasks import dispatch_webhook

from unittest.mock import call

def dispatch_webhook_receiver(sender, **kwargs):
    """
    This receiver is notified when Archive objects are saved. (See apps.py)

    Given:
    >>> webhook_subscription_factory, archive_factory, mocker = [getfixture(i) for i in ['webhook_subscription_factory', 'archive_factory', 'mocker']]
    >>> dispatch_webhook = mocker.patch('main.signals.dispatch_webhook')
    >>> webhook_subscription1 = webhook_subscription_factory()
    >>> webhook_subscription2 = webhook_subscription_factory(user=webhook_subscription1.user)

    Upon the creation of a new Archive, we send one webhook notification to each callback.
    >>> archive = archive_factory(user=webhook_subscription1.user)
    >>> assert dispatch_webhook.mock_calls == [
    ...    call.apply_async(args=[webhook_subscription1.id, archive.capture_job.id]),
    ...    call.apply_async(args=[webhook_subscription2.id, archive.capture_job.id])
    ... ]

    We do NOT send a duplicate notification if the Archive is subsequently updated.
    >>> dispatch_webhook.reset_mock()
    >>> archive.hash = 'updated_hash'
    >>> archive.save()
    >>> assert not dispatch_webhook.mock_calls

    If a user hasn't subscribed to receive any webhook notifications, this is a noop.
    >>> another_archive = archive_factory()
    >>> assert not another_archive.capture_job.user.webhook_subscriptions.exists()
    >>> assert not dispatch_webhook.mock_calls
    """
    created = kwargs['created']
    instance = kwargs['instance']
    if created:
        subscriptions = WebhookSubscription.objects.filter(
            user_id=instance.capture_job.user_id,
            event_type=WebhookSubscription.EventType.ARCHIVE_CREATED
        )
        for subscription_id in subscriptions.values_list('id', flat=True):
            dispatch_webhook.apply_async(args=[subscription_id, instance.capture_job.id])

