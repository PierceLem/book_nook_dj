from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import Friendship
from .serializers import NookUserSerializer
"""from .serializers import FriendshipSerializer"""
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from google.oauth2 import id_token
from google.auth.transport import requests


User = get_user_model()

"""class FriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
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
        friendship = get_object_or_404(Friendship, id=pk, from_user=request.user)
        friendship.delete()
        return Response({"message": "Friend request canceled."}, status=204)"""
    

class GoogleLoginView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        id_token_str = request.data.get('id_token')
        try:
            idinfo = id_token.verify_oauth2_token(id_token_str, requests.Request(), "1433398408-7ae0hp432t01si9s30igmsehaojkhokb.apps.googleusercontent.com")

            email = idinfo.get('email')

            if not email:
                return Response({'detail': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)

            user, created = User.objects.get_or_create(username=email, defaults={'email': email})
            serializer = NookUserSerializer(user)

            token, _ = Token.objects.get_or_create(user=user)

            return Response({'token': token.key, 'user': serializer.data})

        except Exception as e:
            return Response({'detail': 'Google token verification failed', 'error': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)

