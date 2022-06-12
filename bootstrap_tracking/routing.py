
from channels.routing import ProtocolTypeRouter, URLRouter
import channels.staticfiles
from channels.auth import AuthMiddlewareStack
import core.routing


application = ProtocolTypeRouter({
        'websocket': AuthMiddlewareStack(
            URLRouter(
                core.routing.websocket_urlpatterns
            )
        ),
    })

