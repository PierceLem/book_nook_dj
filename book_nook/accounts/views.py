from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import Friendship
from .serializers import NookUserSerializer, FriendshipSerializer
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q
from google.oauth2 import id_token
from google.auth.transport import requests


User = get_user_model()


class FetchFriends(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        friends = Friendship.objects.filter(
            Q(from_user=user) | Q(to_user=user),
            status=Friendship.ACCEPTED
        )
        friends_serialized = FriendshipSerializer(friends, many=True, context={'request': request})

        sent_requests = Friendship.objects.filter(from_user=user, status=Friendship.PENDING)
        sent_requests_serialized = FriendshipSerializer(sent_requests, many=True, context={'request': request})

        received_requests = Friendship.objects.filter(to_user=user, status=Friendship.PENDING)
        received_requests_serialized = FriendshipSerializer(received_requests, many=True, context={'request': request})

        return Response({
            "friends": friends_serialized.data,
            "sent_requests": sent_requests_serialized.data,
            "received_requests": received_requests_serialized.data
        })
    

class FriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = FriendshipSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        id = request.data.get('id')
        friendship = get_object_or_404(Friendship, id=id, to_user=request.user)
        action = request.data.get("action")

        if action == "accept":
            friendship.status = "accepted"
            friendship.save()
            serializer = FriendshipSerializer(instance=friendship, context={'request': request})
            return Response({'friendship': serializer.data})
        elif action == "decline":
            friendship.status = "declined"
            friendship.delete()
        else:
            return Response({"error": "Invalid action."}, status=400)

    def delete(self, request):
        id = request.data.get('id')
        friendship = get_object_or_404(Friendship, id=id, from_user=request.user)
        friendship.delete()
        return Response({"message": "Friend request canceled."}, status=204)
    

class UploadAvatar(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        avatar = request.FILES.get('avatar')

        if not avatar:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.avatar = avatar
        user.save()

        avatar_url = request.build_absolute_uri(user.avatar.url)

        return Response({"detail": "Avatar uploaded successfully.", "avatar_url": avatar_url}, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user

        avatar_url = request.build_absolute_uri('/media/avatars/default-avatar.jpg')

        if user.avatar:
            user.avatar.delete(save=True)
            return Response({"detail": "Avatar deleted.", "avatar_url": avatar_url}, status=status.HTTP_200_OK)

        return Response({"error": "No avatar to delete."}, status=status.HTTP_400_BAD_REQUEST)
    

class GoogleLoginView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        id_token_str = request.data.get('id_token')
        try:
            idinfo = id_token.verify_oauth2_token(id_token_str, requests.Request(), "1433398408-7ae0hp432t01si9s30igmsehaojkhokb.apps.googleusercontent.com")

            email = idinfo.get('email').lower()

            if not email:
                return Response({'detail': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)

            user, created = User.objects.get_or_create(email=email, defaults={'email': email, 'uername': email})
            serializer = NookUserSerializer(user, context={'request': request})

            token, _ = Token.objects.get_or_create(user=user)

            return Response({'token': token.key, 'user': serializer.data})

        except Exception as e:
            return Response({'detail': 'Google token verification failed', 'error': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)

