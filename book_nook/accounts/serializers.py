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
    friends_count = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    saved_books_count = serializers.SerializerMethodField()

    class Meta:
        model = NookUser
        fields = [
            "id",
            "username",
            "email",
            "is_active",
            "date_joined",
            "avatar",
            "bio",
            "friend_request_notifications",
            "message_notifications",
            "auto_accept_friend_requests",
            "friends_count",
            "reviews_count",
            "saved_books_count",
        ]
        read_only_fields = fields

    def get_avatar(self, obj):
        request = self.context.get("request")

        if obj.avatar:
            url = obj.avatar.url
        else:
            url = "/media/avatars/default-avatar.jpg"

        if request:
            return request.build_absolute_uri(url)

        return url

    def get_friends_count(self, obj):
        return obj.friend_requests_sent.filter(accepted=True).count() + obj.friend_requests_received.filter(accepted=True).count()

    def get_reviews_count(self, obj):
        return obj.reviews.filter().count()

    def get_saved_books_count(self, obj):
        return obj.saved_books.count()


class NookUserUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = NookUser
        fields = [
            "avatar",
            "bio",
            "friend_request_notifications",
            "message_notifications",
            "auto_accept_friend_requests",
        ]

    def validate_avatar(self, value):
        if value and value.content_type not in {
            "image/jpeg",
            "image/png",
            "image/webp",
        }:
            raise serializers.ValidationError(
                "Avatar must be a JPEG, PNG, or WebP image."
            )

        elif not value:
            raise serializers.ValidationError(
                "Avatar cannot be empty."       
            )

        return value


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
