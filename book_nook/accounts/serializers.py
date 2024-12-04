from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from .models import NookUser


class NookUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = NookUser
        fields = ("id", "username", "email", "password")


class RequestUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = NookUser
        fields = ['id', 'username', 'email', 'is_active', 'date_joined']


class NookUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = NookUser
        fields = ['id', 'username', 'email', 'is_active', 'date_joined']