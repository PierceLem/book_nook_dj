from threads.routing import websocket_urlpatterns as thread_ws
from accounts.routing import websocket_urlpatterns as account_ws

websocket_urlpatterns = thread_ws + account_ws