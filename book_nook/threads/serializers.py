import hashlib
from rest_framework import serializers
from django.core.exceptions import ValidationError
from accounts.serializers import NookUserSerializer
from books.models import Book
from .models import Thread, Message
from accounts.models import NookUser


def compute_participants_hash(participants):
    ids = sorted([str(user.id) for user in participants])
    joined = "-".join(ids)
    return hashlib.sha256(joined.encode()).hexdigest()

class ThreadDetailSerializer(serializers.ModelSerializer):
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
            'id',
            'name',
            'participants',
            'participants_detail',
            'thread_avatar',
            'created_at',
        ]
        read_only_fields = ['created_at', 'thread_avatar', 'id']

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
            raise serializers.ValidationError({"participants": "A thread with these participants already exists."})
        attrs["participants_hash"] = hash_val
        return attrs
    

class BookMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'title',
            'authors',
            'description',
            'thumbnail',
        ]
        read_only_fields = fields
    

class ThreadMessagesSerializer(serializers.ModelSerializer):
    sender = NookUserSerializer()
    book = BookMessageSerializer()
    is_owner = serializers.SerializerMethodField()
    class Meta:
        model = Message
        fields = [
            'sender',
            'content',
            'book',
            'created_at',
            'is_owner',
        ]
        read_only_fields = ['sender', 'content', 'book', 'created_at', 'is_owner']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request.user == obj.sender:
            return True
        return False
    

