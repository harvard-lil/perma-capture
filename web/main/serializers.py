import humps
from rest_framework import serializers

from django.conf import settings

from .models import WebhookSubscription, CaptureJob, Archive
from .utils import override_storage_netloc


class ArchiveSerializer(serializers.ModelSerializer):

    download_url = serializers.SerializerMethodField()
    screenshot_url = serializers.SerializerMethodField()

    wacz_version = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    target_url_content_type = serializers.SerializerMethodField()
    entrypoints = serializers.SerializerMethodField()
    noarchive_urls = serializers.SerializerMethodField()

    class Meta:
        model = Archive
        read_only_fields = fields = ('id', 'hash', 'hash_algorithm', 'size', 'download_url', 'download_expiration_timestamp', 'created_at', 'updated_at', 'partial_capture', 'target_url_content_type', 'entrypoints', 'noarchive_urls', 'title', 'description',  'wacz_version', 'capture_software', 'screenshot_url')

    def get_download_url(self, archive):
        if archive.download_url:
            return override_storage_netloc(archive.download_url) if settings.OVERRIDE_STORAGE_NETLOC else archive.download_url

    def get_screenshot_url(self, archive):
        if archive.screenshot:
            return override_storage_netloc(archive.screenshot.url) if settings.OVERRIDE_STORAGE_NETLOC else archive.screenshot

    def get_wacz_version(self, archive):
        return archive.datapackage['wacz_version']

    def get_title(self, archive):
        title = archive.datapackage['title']
        if title != archive.capture_job.requested_url:
            return title

    def get_description(self, archive):
        description = archive.datapackage['description']
        if not description.startswith('Captured by Scoop'):
            return description

    def get_target_url_content_type(self, archive):
        return archive.summary['targetUrlContentType']

    def get_entrypoints(self, archive):
        """
        Convert attachment filenames into a format that can be targeted directly by replayweb.page,
        like Perma presently does with screenshots:
        https://github.com/harvard-lil/perma/blob/develop/perma_web/replay/views.py#L27
        https://github.com/harvard-lil/perma/blob/develop/perma_web/replay/templates/iframe.html#L132
        """
        entrypoints = {}
        entrypoints['web_capture'] = archive.summary['exchangeUrls'][0]
        attachments = archive.summary['attachments']
        for attachment_type in attachments:

            if attachment_type == 'certificates':
                # There can be a lot of these, and it seems unlikely
                # upstream will want to expose them individually.
                continue

            # append "file:///" to each attachment filename
            if isinstance(attachments[attachment_type], list):
                entrypoints[humps.decamelize(attachment_type)] = []
                for attachment in attachments[attachment_type]:
                    entrypoints[humps.decamelize(attachment_type)].append(f"file:///{attachment}")
            else:
                entrypoints[humps.decamelize(attachment_type)] = f"file:///{attachments[attachment_type]}"

        return entrypoints

    def get_noarchive_urls(self, archive):
        return archive.summary['noArchiveUrls']


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
