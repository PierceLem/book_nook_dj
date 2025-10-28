from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import ThreadDetailSerializer, ThreadMessagesSerializer
from .models import Thread

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
         return Response(serializer.data)
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   def patch(self, request):
      pass

   def delete(self, request):
      pass


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
         return Response(
            ThreadMessagesSerializer(message, context={'request': request}).data,
            status=status.HTTP_201_CREATED
         )
      
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)