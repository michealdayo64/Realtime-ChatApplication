import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from Chatapp.asgi import my_application
from django.urls import path
from public_chat.consumers import PublicChatConsumer
from chat.consumers import ChatConsumer
from notification.consumers import NotificationConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
#django_asgi_app = application

application = ProtocolTypeRouter({
    "http": my_application,
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