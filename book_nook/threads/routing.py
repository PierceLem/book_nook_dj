from django.urls import re_path
from .consumers import ThreadMessagesConsumer

websocket_urlpatterns = [
    re_path(r"ws/threads/(?P<thread_id>\d+)/$", ThreadMessagesConsumer.as_asgi()),
]