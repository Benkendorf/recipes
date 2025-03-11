import base64
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

from djoser.serializers import UserCreateSerializer

from rest_framework import serializers

from .models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    image = Base64ImageField(required=False)

    class Meta:
        fields = '__all__'
        model = User

    def get_is_subscribed(self, obj):
        return Subscription.objects.get(
            subscriber=self.context['request'].user,
            subscribed_to=obj
        ).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = UserCreateSerializer.Meta.fields + ('username',)
