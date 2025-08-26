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
            return request.build_absolute_uri(obj.avatar.url)
        return request.build_absolute_uri('/media/avatars/default-avatar.jpg')


class FriendshipSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    from_user = NookUserSerializer(read_only=True)
    to_user = NookUserSerializer(read_only=True)
    from_user_id = serializers.PrimaryKeyRelatedField(queryset=NookUser.objects.all(), write_only=True, source='from_user')
    to_user_id = serializers.PrimaryKeyRelatedField(queryset=NookUser.objects.all(), write_only=True, source='to_user')

    class Meta:
        model = Friendship
        fields = [
            'id',
            'other_user',
            'from_user',
            'to_user',
            'from_user_id',
            'to_user_id',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['status', 'created_at', 'updated_at', 'id']

    def get_other_user(self, obj):
        request_user = self.context["request"].user
        other_user = obj.get_other_user(request_user)
        serializer = NookUserSerializer(other_user, context=self.context)
        return serializer.data

    def create(self, validated_data):
        instance = Friendship(**validated_data)
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError({"non_field_errors": e.messages})
        instance.save()
        return instance
