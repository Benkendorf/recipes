from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Subscription

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = '__all__'
        model = User

    def get_is_subscribed(self, obj):
        return Subscription.objects.get(
            subscriber=self.context['request'].user,
            subscribed_to=obj
        ).exists()
