from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import ThreadDetailSerializer, ThreadMessagesSerializer
from .models import Thread, Message
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class Threads(APIView):
   permission_classes = [IsAuthenticated]

   def get(self, request):
      threads = Thread.objects.filter(participants=request.user)
      serializer = ThreadDetailSerializer(instance=threads, many=True, context={'request': request})
      return Response(serializer.data)

   def post(self, request):
      serializer = ThreadDetailSerializer(data=request.data, context={'request': request})
      if serializer.is_valid():
         serializer.save()

         channel_layer = get_channel_layer()

         async_to_sync(channel_layer.group_send)(
            f"user_{request.user.id}",
            {
               "type": "thread.event",
               "event": "thread.created",
               "thread": serializer.data,
            }
         )
         return Response(serializer.data)
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   def patch(self, request, thread_id=None):
      thread = get_object_or_404(Thread, id=thread_id)

      serializer = ThreadDetailSerializer(
         data=request.data,
         instance=thread,
         partial=True,
         context={'request': request}
      )

      if serializer.is_valid():
         updated_thread = serializer.save()

         update_message = Message.objects.filter(
            thread=updated_thread,
            sender=request.user
         ).latest('created_at')

         message_serialized = ThreadMessagesSerializer(
            update_message,
            context={'request': request}
         )

         thread_serialized = ThreadDetailSerializer(
            updated_thread,
            context={'request': request}
         )

         channel_layer = get_channel_layer()

         async_to_sync(channel_layer.group_send)(
            f"thread_{updated_thread.id}",
            {
               "type": "thread.event",
               "thread": thread_serialized.data,
            }
         )

         return Response({
               "thread": thread_serialized.data,
               "message": message_serialized.data,
         })

      return Response(serializer.errors, status=400)

   def delete(self, request, thread_id=None):
      thread = get_object_or_404(Thread, id=thread_id)
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

         return Response(serializer.data, status=status.HTTP_201_CREATED)
      
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)