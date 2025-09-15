from rest_framework import serializers
from accounts.serializers import NookUserSerializer
from .models import Thread
from accounts.models import NookUser


class ThreadSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=NookUser.objects.all(),
        write_only=True
    )
    participants_detail = NookUserSerializer(
        source='participants',
        many=True,
        read_only=True
    )
    thread_avatar = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = [
            'name',
            'participants',
            'participants_detail',
            'thread_avatar',
            'created_at',
        ]
        read_only_fields = ['created_at', 'thread_avatar']

    def get_thread_avatar(self, obj):
        request = self.context.get('request')
        if obj.participants.count() <= 2:
          participants = obj.participants.exclude(id=request.user.id)
          avatar_url = participants[0].avatar
          if avatar_url:
              return request.build_absolute_uri(avatar_url.url)
          return request.build_absolute_uri('/media/avatars/default-avatar.jpg')
        return request.build_absolute_uri('/media/avatars/group_chat_avatar_2.png')
    
    def get_name(self, obj):
        request = self.context.get('request')
        participants = obj.participants.exclude(id=request.user.id)
        if obj.name:
            return obj.name
        else:
            return participants[0].username