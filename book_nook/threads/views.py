from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import ThreadDetailSerializer, ThreadMessagesSerializer
from .models import Thread, Message
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Max, DateTimeField
from django.db.models.functions import Coalesce


class Threads(APIView):
   permission_classes = [IsAuthenticated]

   def get(self, request):
      threads = Thread.objects.filter(
         participants=request.user
      ).annotate(
         latest_message=Max('messages__created_at'),
         last_active=Coalesce(
            'latest_message',
            'created_at',
            output_field=DateTimeField()
         )
      ).order_by('-last_active')

      serializer = ThreadDetailSerializer(instance=threads, many=True, context={'request': request})
      return Response(serializer.data)

   def post(self, request):
      serializer = ThreadDetailSerializer(data=request.data, context={'request': request})
      if serializer.is_valid():
         serializer.save()

         channel_layer = get_channel_layer()

         participant_ids = [
            p["id"] for p in serializer.data['participants_detail']
         ]

         for id in participant_ids:
            async_to_sync(channel_layer.group_send)(
               f"user_{id}",
                  {
                     "type": "user.event",
                     "event": "add_thread",
                     "data": serializer.data,
                  }
            )

         return Response({"status": "ok"}, status=status.HTTP_201_CREATED)
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   def patch(self, request, thread_id=None):
      thread = get_object_or_404(Thread, id=thread_id)

      thread_serialized = ThreadDetailSerializer(
         data=request.data,
         instance=thread,
         partial=True,
         context={'request': request}
      )

      if thread_serialized.is_valid():
         updated_thread = thread_serialized.save()

         # re-serialize after save to get fresh data from signal driven changes
         fresh_thread_serialized = ThreadDetailSerializer(
            updated_thread,
            context={'request': request}
         )

         update_message = Message.objects.filter(
            thread=updated_thread,
            sender=request.user
         ).latest('created_at')

         message_serialized = ThreadMessagesSerializer(
            update_message,
            context={'request': request}
         )

         channel_layer = get_channel_layer()

         async_to_sync(channel_layer.group_send)(
            f"thread_{fresh_thread_serialized.data['id']}",
            {
               "type": "thread.event",
               "message": message_serialized.data
            }
         )

         participant_ids = [
            p["id"] for p in fresh_thread_serialized.data['participants_detail']
         ]

         if request.data.get("name"):
            for id in participant_ids:
               async_to_sync(channel_layer.group_send)(
                  f"user_{id}",
                  {
                     "type": "user.event",
                     "event": "update_thread",
                     "data": fresh_thread_serialized.data,
                  }
               )

         if request.data.get("participants"):
            # get temporary removed or added participant data from the serializer
            removed_ids = getattr(updated_thread, 'removed_participant', [])
            removed_id = removed_ids[0] if removed_ids else None

            added_ids = getattr(updated_thread, 'added_participant', [])
            added_id = added_ids[0] if added_ids else None

            # broadcast the remove_thread event to the kicked user and the update_thread event to the rest
            if removed_id:
               async_to_sync(channel_layer.group_send)(
                  f"user_{removed_id}",
                  {
                     "type": "user.event",
                     "event": "remove_thread",
                     "data": fresh_thread_serialized.data["id"],
                  }
               )

               for id in participant_ids:
                  async_to_sync(channel_layer.group_send)(
                     f"user_{id}",
                     {
                        "type": "user.event",
                        "event": "update_thread",
                        "data": fresh_thread_serialized.data,
                     }
                  )

            # broadcast the add_thread event to the added user and the update_thread event to the rest
            if added_id:
               async_to_sync(channel_layer.group_send)(
                  f"user_{added_id}",
                  {
                     "type": "user.event",
                     "event": "add_thread",
                     "data": fresh_thread_serialized.data,
                  }
               )

               participant_ids.remove(added_id)
               for id in participant_ids:
                  async_to_sync(channel_layer.group_send)(
                     f"user_{id}",
                     {
                        "type": "user.event",
                        "event": "update_thread",
                        "data": fresh_thread_serialized.data,
                     }
                  )
         return Response({"status": "ok"}, status=status.HTTP_200_OK)
      return Response(thread_serialized.errors, status=400)

   def delete(self, request, thread_id=None):
      thread = get_object_or_404(Thread, id=thread_id)
      user_ids = list(thread.participants.values_list('id', flat=True))

      channel_layer = get_channel_layer()

      for id in user_ids:
         async_to_sync(channel_layer.group_send)(
            f"user_{id}",
            {
               "type": "user.event",
               "event": "remove_thread",
               "data": thread.id,
            }
         )
      thread.delete()
      
      return Response({"status": "Thread deleted."}, status=status.HTTP_204_NO_CONTENT)


class ThreadMessages(APIView):
   def get(self, request, thread_id):
      thread = get_object_or_404(Thread, id=thread_id)
      messages = thread.messages.all()
      serializer = ThreadMessagesSerializer(instance=messages, many=True, context={'request': request})
      return Response(serializer.data)
   
   def post(self, request, thread_id):
      thread = get_object_or_404(Thread, id=thread_id)

      serializer = ThreadMessagesSerializer(data=request.data, context={'request': request, 'thread': thread})

      if serializer.is_valid():
         message = serializer.save()
         serializer = ThreadMessagesSerializer(message, context={'request': request})

         channel_layer = get_channel_layer()
         async_to_sync(channel_layer.group_send)(
            f"thread_{thread.id}",
            {
               "type": "thread.event",
               "message": serializer.data
            }
         )
            
         for participant in thread.participants.all():
            async_to_sync(channel_layer.group_send)(
               f"user_{participant.id}",
               {
                  "type": "user.event",
                  "event": "reconcile_thread",
                  "data": {
                     "last_active": serializer.data['created_at'],
                     "message_hint": thread.hint,
                     "thread_id": thread.id,
                  }
               }
            )

         return Response(serializer.data, status=status.HTTP_201_CREATED)
      
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)