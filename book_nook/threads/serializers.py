import hashlib
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from accounts.serializers import NookUserSerializer
from .models import Thread
from accounts.models import NookUser


def compute_participants_hash(participants):
    ids = sorted([str(user.id) for user in participants])
    joined = "-".join(ids)
    return hashlib.sha256(joined.encode()).hexdigest()

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
        
    def validate(self, attrs):
        participants = attrs.get("participants", [])
        hash_val = compute_participants_hash(participants)
        if Thread.objects.filter(participants_hash=hash_val).exists():
            print('validate method constraint failed')
            raise serializers.ValidationError({"participants": "A thread with these participants already exists."})
        attrs["participants_hash"] = hash_val
        return attrs