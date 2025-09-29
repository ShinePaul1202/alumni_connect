# alumni_connect/alumni_connect/asgi.py

import os
from django.core.asgi import get_asgi_application

# --- THIS IS THE FIX ---
# Import WhiteNoise for serving static files
from whitenoise import WhiteNoise
# --- END OF FIX ---

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import messaging.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumni_connect.settings')

# This is the base Django app
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # --- THIS IS THE FIX ---
    # Wrap the Django app with WhiteNoise for static file serving.
    # This is ONLY for development when running Daphne directly.
    "http": WhiteNoise(django_asgi_app),
    # --- END OF FIX ---

    # WebSocket chat handler
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                messaging.routing.websocket_urlpatterns
            )
        )
    ),
})