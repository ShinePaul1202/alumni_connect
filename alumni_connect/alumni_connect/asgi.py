import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import messaging.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumni_connect.settings')

application = ProtocolTypeRouter({
    # Just use the default Django ASGI app for HTTP
    "http": get_asgi_application(),

    # And our websocket router
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                messaging.routing.websocket_urlpatterns
            )
        )
    ),
})