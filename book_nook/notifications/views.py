from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Notification
from .serializers import NotificationSerializer


class NotificationsView(APIView):
  def get(self, request):
    notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    serializer = NotificationSerializer(instance=notifs, many=True)

    return Response(serializer.data)
  
  def delete(self, request):
    id = request.data.get('id')

    if id:
      Notification.objects.filter(id=id).delete()
    else:
      Notification.objects.filter(recipient=request.user).delete()
    
    return Response(status=status.HTTP_204_NO_CONTENT)
