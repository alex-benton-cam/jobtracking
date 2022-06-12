"""
ASGI config for bootstrap_tracking project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os
import channels.staticfiles
import shoestring_wrapper.wrapper
import core.routing
from channels.routing import get_default_application
from channels.layers import get_channel_layer
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bootstrap_tracking.settings")
asgi_application = get_asgi_application()


application = ProtocolTypeRouter(
    {
        "http": asgi_application,
        "websocket": AuthMiddlewareStack(URLRouter(core.routing.websocket_urlpatterns)),
    }
)


shoestring_wrapper.wrapper.Wrapper.start({"channel_layer": get_channel_layer()})
