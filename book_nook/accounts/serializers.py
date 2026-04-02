from djoser.serializers import UserCreateSerializer
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import NookUser, Friendship


class NookUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = NookUser
        fields = ("id", "username", "email", "password")


class NookUserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    class Meta:
        model = NookUser
        fields = ['id', 'username', 'email', 'is_active', 'date_joined', 'avatar']
        read_only_fields = fields

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        if request:
            return request.build_absolute_uri('/media/avatars/default-avatar.jpg')
        return '/media/avatars/default-avatar.jpg' 


class FriendshipSerializer(serializers.ModelSerializer):
    to_user = NookUserSerializer(read_only=True)
    from_user = NookUserSerializer(read_only=True)
    from_user_id = serializers.PrimaryKeyRelatedField(queryset=NookUser.objects.all(), write_only=True, source='from_user')
    to_user_id = serializers.PrimaryKeyRelatedField(queryset=NookUser.objects.all(), write_only=True, source='to_user')

    class Meta:
        model = Friendship
        fields = [
            'id',
            'to_user',
            'from_user',
            'from_user_id',
            'to_user_id',
            'accepted',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'id']

    def validate(self, attrs):
        instance = Friendship(**attrs)
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return attrs
