from rest_framework import serializers

from main.models import WebhookSubscription, Archive


class WebhookSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = WebhookSubscription
        fields = '__all__'
        read_only_fields = ['id', 'user', 'signing_key', 'signing_key_algorithm']


class ArchiveSerializer(serializers.ModelSerializer):

    class Meta:
        model = Archive
        fields = '__all__'
