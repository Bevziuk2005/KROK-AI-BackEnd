from rest_framework import serializers


class MicrosoftLoginSerializer(serializers.Serializer):
    redirect = serializers.URLField(required=False)


class RefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
