from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import Friendship
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from accounts.models import NookUser
from .serializers import NookUserSerializer, FriendshipSerializer
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q
from google.oauth2 import id_token
from google.auth.transport import requests
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


User = get_user_model()


class FetchFriends(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        friends = Friendship.objects.filter(
            Q(from_user=user) | Q(to_user=user),
            accepted = True
        )
        friends_serialized = FriendshipSerializer(friends, many=True, context={'request': request})

        outgoing_requests = Friendship.objects.filter(from_user=user, accepted=False)
        outgoing_requests_serialized = FriendshipSerializer(outgoing_requests, many=True, context={'request': request})

        incoming_requests = Friendship.objects.filter(to_user=user, accepted=False)
        incoming_requests_serialized = FriendshipSerializer(incoming_requests, many=True, context={'request': request})

        return Response({
            "friends": friends_serialized.data,
            "outgoing_requests": outgoing_requests_serialized.data,
            "incoming_requests": incoming_requests_serialized.data
        })
    

class SearchUsers(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([])
        
        users = User.objects.filter(
            is_active=True
        ).filter(
            username__icontains=query
        ) | User.objects.filter(
            email__icontains=query
        ).exclude(id=request.user.id)

        users_serialized = NookUserSerializer(users, many=True, context={'request': request})
        return Response({'users': users_serialized.data})
    

class FriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = FriendshipSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()

            id = serializer.data['to_user']['id']

            notif = Notification.objects.create(
                recipient=get_object_or_404(NookUser, id=id),
                type='success',
                title='New Friend Request',
                content=f"{serializer.data['from_user']['username']} sent you a friend request.",
                friendship=serializer.instance
            )

            notif_serialized = NotificationSerializer(instance=notif)

            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                f"user_{id}",
                {
                "type": "user.event",
                "event": "incoming_request",
                "data": serializer.data,
                }
            )

            async_to_sync(channel_layer.group_send)(
                f"user_{id}",
                {
                "type": "user.event",
                "event": "new_notification",
                "data": notif_serialized.data,
                }
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        id = request.data.get('id')
        friendship = get_object_or_404(Friendship, id=id)
        friendship.accepted = True
        friendship.save()
        friendship_serialized = FriendshipSerializer(instance=friendship, context={'request': request})

        Notification.objects.filter(friendship=friendship).delete()

        notif = Notification.objects.create(
            recipient=get_object_or_404(NookUser, id=friendship_serialized.data['from_user']['id']),
            type='success',
            title='Friend Request Accepted',
            content=f"{friendship_serialized.data['to_user']['username']} accepted your friend request.",
            friendship=friendship_serialized.instance
        )

        notif_serialized = NotificationSerializer(instance=notif)

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"user_{friendship_serialized.data['from_user']['id']}",
            {
            "type": "user.event",
            "event": "request_accepted",
            "data": friendship_serialized.data,
            }
        )

        async_to_sync(channel_layer.group_send)(
            f"user_{friendship_serialized.data['from_user']['id']}",
            {
            "type": "user.event",
            "event": "new_notification",
            "data": notif_serialized.data,
            }
        )

        return Response(friendship_serialized.data)

    def delete(self, request):
        id = request.data.get('id')
        friendship = get_object_or_404(Friendship, id=id)
        other_user = friendship.get_other_user(request.user)
        notif = {}

        if friendship.accepted:
            event = "friend_removed"

            notif = Notification.objects.create(
                recipient=other_user,
                type='error',
                title='Unfriended',
                content=f"{request.user.username} unfriended you.",
            )

        else:
            if request.user.id == friendship.from_user.id:
                event = "request_cancelled"

            else:
                event = "request_declined"

                notif = Notification.objects.create(
                    recipient=other_user,
                    type='error',
                    title='Friend Request Declined',
                    content=f"{friendship.to_user.username} declined your friend request.",
                )

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"user_{other_user.id}",
            {
            "type": "user.event",
            "event": event,
            "data": friendship.id,
            }
        )

        if notif:
            notif_serialized = NotificationSerializer(instance=notif)

            async_to_sync(channel_layer.group_send)(
                f"user_{other_user.id}",
                {
                "type": "user.event",
                "event": 'new_notification',
                "data": notif_serialized.data,
                }
            )

        friendship.delete()

        return Response(other_user.id)
    

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
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                requests.Request(),
                "1433398408-7ae0hp432t01si9s30igmsehaojkhokb.apps.googleusercontent.com"
            )
        except Exception as e:
            return Response(
                {'detail': 'Google token verification failed', 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = idinfo.get('email')
        if not email:
            return Response({'detail': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)
        email = email.lower()

        user, created = User.objects.get_or_create(
            email=email,
            defaults={'email': email, 'username': email}
        )
        serializer = NookUserSerializer(user, context={'request': request})
        token, _ = Token.objects.get_or_create(user=user)

        return Response({'token': token.key, 'user': serializer.data})

