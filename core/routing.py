from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/stateupdates',consumers.StateUpdateConsumer.as_asgi()),
    re_path(r'ws/manager',consumers.ManagerConsumer.as_asgi()),
    #re_path(r'ws/stateupdates',consumers.StateUpdateConsumer),
]
