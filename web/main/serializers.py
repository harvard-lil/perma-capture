from rest_framework import serializers

from main.models import WebhookSubscription


class WebhookSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = WebhookSubscription
        fields = '__all__'
        read_only_fields = ['id', 'user', 'signing_key', 'signing_key_algorithm']
