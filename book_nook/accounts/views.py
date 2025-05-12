from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Friendship
from .serializers import FriendshipSerializer
from django.shortcuts import get_object_or_404

class FriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Send a friend request."""
        serializer = FriendshipSerializer(data=request.data)
        if serializer.is_valid():
            to_user = serializer.validated_data['to_user']
            if to_user == request.user:
                return Response({"error": "You cannot send a friend request to yourself."}, status=400)
            friendship, created = Friendship.objects.get_or_create(
                from_user=request.user, to_user=to_user,
                defaults={"status": "pending"}
            )
            if not created:
                return Response({"error": "Friend request already sent."}, status=400)
            return Response(FriendshipSerializer(friendship).data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        """Accept or decline a friend request."""
        friendship = get_object_or_404(Friendship, id=pk, to_user=request.user)
        action = request.data.get("action")

        if action == "accept":
            friendship.status = "accepted"
            friendship.save()
            return Response({"message": "Friend request accepted."})
        elif action == "decline":
            friendship.status = "declined"
            friendship.save()
            return Response({"message": "Friend request declined."})
        else:
            return Response({"error": "Invalid action."}, status=400)

    def delete(self, request, pk):
        """Cancel a friend request (only sender can cancel)."""
        friendship = get_object_or_404(Friendship, id=pk, from_user=request.user)
        friendship.delete()
        return Response({"message": "Friend request canceled."}, status=204)

