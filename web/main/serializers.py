from rest_framework import serializers

from django.conf import settings

from .models import WebhookSubscription, CaptureJob, Archive
from .utils import override_access_url_netloc


class ArchiveSerializer(serializers.ModelSerializer):

    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Archive
        read_only_fields = fields = ('id', 'hash', 'hash_algorithm', 'warc_size', 'download_url', 'download_expiration_timestamp', 'created_at', 'updated_at')

    def get_download_url(self, archive):
        if archive.download_url:
            return override_access_url_netloc(archive.download_url) if settings.OVERRIDE_DOWNLOAD_URL_NETLOC else archive.download_url


class CaptureJobSerializer(serializers.ModelSerializer):

    archive = ArchiveSerializer(read_only=True)

    class Meta:
        model = CaptureJob
        fields =  ('id', 'requested_url', 'capture_oembed_view', 'headless', 'human', 'label', 'webhook_data', 'status', 'message', 'queue_position', 'step_count', 'step_description', 'created_at', 'updated_at', 'capture_start_time', 'capture_end_time', 'archive')
        read_only_fields =  ('user', 'id', 'status', 'message', 'queue_position', 'step_count', 'step_description', 'created_at', 'updated_at', 'capture_start_time', 'capture_end_time')


class ReadOnlyCaptureJobSerializer(CaptureJobSerializer):

    class Meta(CaptureJobSerializer.Meta):
        read_only_fields =  ('user', 'id', 'requested_url', 'capture_oembed_view', 'headless', 'human', 'label', 'webhook_data', 'status', 'message', 'queue_position', 'step_count', 'step_description', 'created_at', 'updated_at', 'capture_start_time', 'capture_end_time')


class WebhookSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = WebhookSubscription
        fields = ('id', 'created_at', 'updated_at', 'event_type', 'callback_url', 'signing_key', 'signing_key_algorithm')
        read_only_fields = ('id', 'created_at', 'updated_at', 'user', 'signing_key', 'signing_key_algorithm')


class SimpleWebhookSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = WebhookSubscription
        read_only_fields = fields = ('id', 'event_type')
