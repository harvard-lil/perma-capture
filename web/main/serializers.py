from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator

from rest_framework import serializers

from main.models import WebhookSubscription, CaptureJob, Archive
from main.utils import contains_control_characters

class WebhookSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = WebhookSubscription
        fields = '__all__'
        read_only_fields = ('id', 'user', 'signing_key', 'signing_key_algorithm')


class ArchiveSerializer(serializers.ModelSerializer):

    class Meta:
        model = Archive
        read_only_fields = fields = ('id', 'hash', 'hash_algorithm', 'warc_size', 'download_url', 'download_expiration_timestamp', 'created_at', 'updated_at')


class CaptureJobSerializer(serializers.ModelSerializer):

    archive = ArchiveSerializer(read_only=True)

    class Meta:
        model = CaptureJob
        fields =  ('id', 'requested_url', 'capture_oembed_view', 'headless', 'human', 'label', 'webhook_data', 'status', 'message', 'order', 'step_count', 'step_description', 'created_at', 'updated_at', 'capture_start_time', 'capture_end_time', 'archive')
        read_only_fields =  ('user', 'id', 'status', 'message', 'order', 'step_count', 'step_description', 'created_at', 'updated_at', 'capture_start_time', 'capture_end_time')

    def validate_requested_url(self, url):
        url = url.strip()
        if not url:
            raise serializers.ValidationError("URL cannot be empty.")
        if url[:4] != 'http':
            url = 'http://' + url

        # Our past experience shows it is possible for control characters to make
        # it through and cause problems down the line. Reject them explicitly.
        if contains_control_characters(url):
            raise serializers.ValidationError("URL contains invalid characters.")

        validate = URLValidator()
        try:
            validate(url)
        except DjangoValidationError:
            raise serializers.ValidationError("Not a valid URL.")

        return url


class ReadOnlyCaptureJobSerializer(CaptureJobSerializer):

    class Meta(CaptureJobSerializer.Meta):
        read_only_fields =  ('user', 'id', 'requested_url', 'capture_oembed_view', 'headless', 'human', 'label', 'webhook_data', 'status', 'message', 'order', 'step_count', 'step_description', 'created_at', 'updated_at', 'capture_start_time', 'capture_end_time')

