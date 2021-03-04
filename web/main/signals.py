from .models import WebhookSubscription
from .tasks import dispatch_webhook

def dispatch_webhook_receiver(sender, **kwargs):
    """
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
