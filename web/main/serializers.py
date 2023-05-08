from rest_framework import serializers

from django.conf import settings

from .models import WebhookSubscription, CaptureJob, Archive
from .utils import override_storage_netloc


class ArchiveSerializer(serializers.ModelSerializer):

    download_url = serializers.SerializerMethodField()
    screenshot_url = serializers.SerializerMethodField()

    class Meta:
        model = Archive
        read_only_fields = fields = ('id', 'hash', 'hash_algorithm', 'size', 'download_url', 'download_expiration_timestamp', 'created_at', 'updated_at', 'summary', 'screenshot_url')

    def get_download_url(self, archive):
        if archive.download_url:
            return override_storage_netloc(archive.download_url) if settings.OVERRIDE_STORAGE_NETLOC else archive.download_url

    def get_screenshot_url(self, archive):
        if archive.screenshot:
            return override_storage_netloc(archive.screenshot.url) if settings.OVERRIDE_STORAGE_NETLOC else archive.screenshot


class CaptureJobSerializer(serializers.ModelSerializer):

    archive = ArchiveSerializer(read_only=True)

    class Meta:
        model = CaptureJob
        fields =  (
            'id',
            'requested_url',
            'validated_url',
            'human',
            'include_raw_exchanges',
            'include_screenshot',
            'include_pdf_snapshot',
            'include_dom_snapshot',
            'include_videos_as_attachment',
            'include_certificates_as_attachment',
            'run_site_specific_behaviors',
            'headless',
            'label',
            'webhook_data',
            'status',
            'message',
            'queue_position',
            'step_count',
            'step_description',
            'created_at',
            'updated_at',
            'capture_start_time',
            'capture_end_time',
            'archive'
        )
        read_only_fields =  ('user', 'id', 'status', 'message', 'queue_position', 'step_count', 'step_description', 'created_at', 'updated_at', 'capture_start_time', 'capture_end_time')


class ReadOnlyCaptureJobSerializer(CaptureJobSerializer):

    class Meta(CaptureJobSerializer.Meta):
        read_only_fields =  (
            'user',
            'id',
            'requested_url',
            'validated_url',
            'include_raw_exchanges',
            'include_screenshot',
            'include_pdf_snapshot',
            'include_dom_snapshot',
            'include_videos_as_attachment',
            'include_certificates_as_attachment',
            'run_site_specific_behaviors',
            'headless',
            'human',
            'label',
            'webhook_data',
            'status',
            'message',
            'queue_position',
            'step_count',
            'step_description',
            'created_at',
            'updated_at',
            'capture_start_time',
            'capture_end_time'
        )


class WebhookSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = WebhookSubscription
        fields = ('id', 'created_at', 'updated_at', 'event_type', 'callback_url', 'signing_key', 'signing_key_algorithm')
        read_only_fields = ('id', 'created_at', 'updated_at', 'user', 'signing_key', 'signing_key_algorithm')


class SimpleWebhookSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = WebhookSubscription
        read_only_fields = fields = ('id', 'event_type')
