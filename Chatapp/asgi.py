"""
ASGI config for Chatapp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
from public_chat.consumers import PublicChatConsumer
from chat.consumers import ChatConsumer
from notification.consumers import NotificationConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Chatapp.settings')

my_application = get_asgi_application()


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # WebSocket chat handler
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path("", NotificationConsumer.as_asgi()),
                path("chat/<room_id>/", ChatConsumer.as_asgi()),
                path("public_chat/<room_id>/", PublicChatConsumer.as_asgi())
            ])
        )
    ),
})
