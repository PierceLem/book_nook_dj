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
    name = serializers.CharField(required=False, allow_blank=True, write_only=True)
    participants_detail = NookUserSerializer(
        source='participants',
        many=True,
        read_only=True
    )
    thread_avatar = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = [
            'id',
            'name',
            'display_name',
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
    
    def get_display_name(self, obj):
        user = self.context.get('request').user
        return obj.get_display_name(user)
        
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

        old_name = instance.name
        old_participants = set(instance.participants.all())

        name = validated_data.get("name", None)
        participants = validated_data.get("participants", None)

        instance = super().update(instance, validated_data)

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
                Message.objects.create(
                    thread=instance,
                    sender=user,
                    thread_update=f"{user.username} added {p.username} to the thread."
                )

            for p in removed:
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

        instance.save()
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
    is_owner = serializers.SerializerMethodField()
    class Meta:
        model = Message
        fields = [
            'sender',
            'content',
            'book',
            'thread_update',
            'created_at',
            'is_owner',
            'book_id',
        ]
        read_only_fields = ['sender', 'book', 'thread_update', 'created_at', 'is_owner']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request.user == obj.sender:
            return True
        return False
    
    def create(self, validated_data):
        request = self.context.get('request')
        thread = self.context.get('thread')

        book_data = request.data.get('book_data')
        book = None
        if book_data:
            book = get_or_create_book(book_data)

        validated_data['sender'] = request.user
        validated_data['thread'] = thread
        validated_data['book'] = book

        return super().create(validated_data)
    

