import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from .models import Thread, ThreadBookmark
from accounts.serializers import NookUserSerializer



class ThreadMessagesConsumer(AsyncWebsocketConsumer):
    active_users = {}

    async def connect(self):
        self.thread_id = self.scope["url_route"]["kwargs"]["thread_id"]
        self.group_name = f"thread_{self.thread_id}"
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        allowed = await self.user_in_thread()
        if not allowed:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        if self.thread_id not in self.active_users:
            self.active_users[self.thread_id] = {}
        self.active_users[self.thread_id][self.user.id] = await self.get_user_data()

        print("connect method active users: ", self.active_users)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "thread.event",
                "event": "active_users",
                "data": list(self.active_users[self.thread_id].values()),
            }
        )

    async def disconnect(self, close_code):
        await self.update_bookmark(self.scope['user'], self.thread_id)

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        if self.thread_id in self.active_users:
            self.active_users[self.thread_id].pop(self.user.id, None)
            if not self.active_users[self.thread_id]:
                del self.active_users[self.thread_id]

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "thread.event",
                "event": "active_users",
                "data": list(self.active_users[self.thread_id].values()),
            }
        )

    async def thread_event(self, event):
        print("thread event triggered")
        await self.send(text_data=json.dumps({
            "event": event["event"],
            "data": event["data"],
        }))

    @database_sync_to_async
    def get_user_data(self):
        data = dict(NookUserSerializer(instance=self.user).data)
        avatar = self.user.avatar.url if self.user.avatar else '/media/avatars/default-avatar.jpg'
        data['avatar'] = f"{settings.BASE_URL}{avatar}"
        return data

    @database_sync_to_async
    def user_in_thread(self):
        return Thread.objects.filter(
            id=self.thread_id,
            participants=self.user
        ).exists()
    
    @database_sync_to_async
    def update_bookmark(self, user, thread_id):
        thread = Thread.objects.get(id=thread_id)
        ThreadBookmark.objects.update_or_create(
            user=user,
            thread=thread,
        )