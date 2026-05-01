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
    ids = request.data.get("ids")
    Notification.objects.filter(id__in=ids, recipient=request.user).delete()
    
    return Response(status=status.HTTP_204_NO_CONTENT)
