from rest_framework import serializers
from accounts.serializers import NookUserSerializer
from books.models import Book
from books.utils import get_or_create_book
from .models import Thread, Message
from accounts.models import NookUser


class ThreadDetailSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=NookUser.objects.all(),
        write_only=True
    )
    name = serializers.CharField(required=False, allow_blank=True)
    participants_detail = NookUserSerializer(
        source='participants',
        many=True,
        read_only=True
    )
    thread_avatar = serializers.SerializerMethodField()
    last_active = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = [
            'id',
            'name',
            'participants',
            'participants_detail',
            'thread_avatar',
            'created_at',
            'last_active',
            'hint',
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
    
    def get_last_active(self, obj):
        latest = obj.messages.order_by('-created_at').first()
        date = latest.created_at if latest else obj.created_at
        return date.isoformat()
            
    def validate(self, attrs):
        if 'participants' in attrs:
            participants = attrs.get("participants", [])
            ids = [p.id if hasattr(p, "id") else p for p in participants]

            if len(ids) != len(set(ids)):
                raise serializers.ValidationError({"participants": "This user is already a part of this thread."})
            
            if len(ids) < 2:
                raise serializers.ValidationError({"participants": "Threads must contain at least 2 members."})
        return attrs
    
    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user 

        # Capture current state before update for comparison
        old_name = instance.name
        old_participants = set(instance.participants.all())

        name = validated_data.get("name", None)
        participants = validated_data.get("participants", None)

        # update and save validated data fields
        instance = super().update(instance, validated_data)

        # Refresh the instance from the database to pick up any signal changes
        instance.refresh_from_db()

        # track added/removed participant after refresh_from_db since it wipes
        # non database fields
        instance.removed_participant = []
        instance.added_participant = []

        if name and name != old_name:
            Message.objects.create(
                thread=instance,
                sender=user,
                thread_update=f"{user.username} renamed the thread to '{name}'."
            )

        if participants is not None:
            new_participants = set(participants)
            added = new_participants - old_participants
            removed = old_participants - new_participants

            for p in added:
                instance.added_participant.append(p.id)
                Message.objects.create(
                    thread=instance,
                    sender=user,
                    thread_update=f"{user.username} added {p.username} to the thread."
                )

            for p in removed:
                instance.removed_participant.append(p.id)

                if p.id != user.id:
                    Message.objects.create(
                        thread=instance,
                        sender=user,
                        thread_update=f"{user.username} removed {p.username} from the thread."
                    )
                else:
                    Message.objects.create(
                        thread=instance,
                        sender=user,
                        thread_update=f"{p.username} has left the thread."
                    )

        # No instance.save() here — super().update() already saved the instance
        # and calling save() again would overwrite signal-driven changes
        return instance
    

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
    sender = NookUserSerializer(read_only=True)
    book = BookMessageSerializer(read_only=True)
    thread_id = serializers.SerializerMethodField()
    class Meta:
        model = Message
        fields = [
            'sender',
            'content',
            'book',
            'thread_update',
            'created_at',
            'thread_id',
        ]
        read_only_fields = ['sender', 'book', 'thread_update', 'created_at']
        
    def get_thread_id(self, obj):
        return obj.thread.id
    
    def create(self, validated_data):
        request = self.context.get("request")
        if request is None:
            raise RuntimeError("Request is required to create a message")

        thread = self.context.get("thread")
        if thread is None:
            raise RuntimeError("Thread is required to create a message")

        content = validated_data.get("content")
        book_data = request.data.get("book_data")

        book = None
        if book_data:
            book = get_or_create_book(book_data)
            validated_data["content"] = None

        if content:
            validated_data["book"] = None

        validated_data["sender"] = request.user
        validated_data["thread"] = thread
        validated_data["book"] = book

        return super().create(validated_data)
    

