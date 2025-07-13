from djoser.serializers import UserCreateSerializer
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
    from_user = NookUserSerializer(read_only=True)
    to_user = NookUserSerializer(read_only=True)
    from_user_id = serializers.PrimaryKeyRelatedField(queryset=NookUser.objects.all(), write_only=True, source='from_user')
    to_user_id = serializers.PrimaryKeyRelatedField(queryset=NookUser.objects.all(), write_only=True, source='to_user')

    class Meta:
        model = Friendship
        fields = [
            'id',
            'from_user',
            'to_user',
            'from_user_id',
            'to_user_id',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['status', 'created_at', 'updated_at', 'id']

    def validate(self, data):
        from_user = data['from_user']
        to_user = data['to_user']
        if from_user == to_user:
            raise serializers.ValidationError("You cannot send a friend request to yourself.")
        if Friendship.objects.filter(from_user=from_user, to_user=to_user).exists():
            raise serializers.ValidationError("Friend request already sent.")
        return data
