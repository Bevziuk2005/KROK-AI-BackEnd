from rest_framework import serializers
from apps.users.models import User


class MicrosoftLoginSerializer(serializers.Serializer):
    redirect = serializers.URLField(required=False)


class RefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='id')

    class Meta:
        model = User
        fields = ('id', 'email', 'email_verified')


class MeUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    email_verified = serializers.BooleanField(required=False)

    def update(self, instance, validated_data):
        if 'email' in validated_data:
            instance.email = validated_data['email']
        if 'email_verified' in validated_data:
            instance.email_verified = validated_data['email_verified']
        instance.save()
        return instance
