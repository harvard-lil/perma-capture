from django.apps import AppConfig
from django.db.models.signals import post_save


class MainConfig(AppConfig):
    name = 'main'

    def ready(self):
        from .signals import dispatch_webhook_receiver
        post_save.connect(dispatch_webhook_receiver, sender='main.Archive', dispatch_uid="dispatch_webhook_signal")
