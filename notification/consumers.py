#from django.conf import settings
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.paginator import Paginator
#from django.core.serializers import serialize
from channels.db import database_sync_to_async
from django.contrib.contenttypes.models import ContentType

import json
from datetime import datetime

#from chat.models import UnreadChatRoomMessages
from friend.models import FriendRequest, FriendsList
from notification.models import Notification
from notification.utils import LazyNotificationEncoder
from notification.constant import *
from chat.exceptions import ClientError



class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection
        """
        print("PublicChatConsumer: connect: " + str(self.scope['user']))
        await self.accept()

        self.room_id = None

    async def receive_json(self, content):
        """
        Called when we get a tex frame. Channels will json-decode the payload for us
        and pass it as the first argument
        """
        command = content.get("command", None)
        print("PublicChatConsumer: receive_json: " + str(command))
        try:
            if command == "get_general_notifications":
                payload = await get_general_notifications(self.scope["user"], content.get("page_number", None))
                #print(payload)
                if payload == None:
                    raise ClientError(204, "Something went wrong retrieving the notifications.")
                else:
                    payload = json.loads(payload)
                    await self.send_general_notifications_payload(payload['notifications'], payload['new_page_number'])
        except ClientError as e:
            print("Exception: Notification: " + str(e))
            pass


    async def disconnect(self, code):
        """
        Called when the websockect closes for any reason
        """
        print("PublicChatConsumer: diconnect")
        


    async def handle_client_error(self, e):
        """
        Called when a clienterror is raised.
        Sends error data to the UI
        """
        errorData = {}
        errorData['error'] = e.code
        if e.message:
            errorData['message'] = e.message
        return

    async def display_progress_bar(self, is_displayed):
        '''
            1. is_displayed = True
                - Display the progress bar on UI
            2. is_displayed = False
                - Hide the progress bar UI
        '''
        print("DISPLAY PROGRESS BAR: " + str(is_displayed))
        await self.send_json({
            "display_progress_bar": is_displayed
        })

    async def send_general_notifications_payload(self, notifications, new_page_number):
        """
        Called by receive_json when ready to send a json array of the notifications
        """
        #print("NotificationConsumer: send_general_notifications_payload")
        await self.send_json(
            {
                "general_msg_type": GENERAL_MSG_TYPE_NOTIFICATIONS_PAYLOAD,
                "notifications": notifications,
                "new_page_number": new_page_number,
            },
        )


@database_sync_to_async
def get_general_notifications(user, page_number):
    """
    Get General Notifications with Pagination (next page of results).
    This is for appending to the bottom of the notifications list.
    General Notifications are:
    1. FriendRequest
    2. FriendList
    """
    if user.is_authenticated:
        friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
        friend_list_ct = ContentType.objects.get_for_model(FriendsList)
        notifications = Notification.objects.filter(target=user, content_type__in=[friend_request_ct, friend_list_ct]).order_by('-timestamp')
        p = Paginator(notifications, DEFAULT_NOTIFICATION_PAGE_SIZE)

        payload = {}
        if len(notifications) > 0:
            if int(page_number) <= p.num_pages:
                s = LazyNotificationEncoder()
                serialized_notifications = s.serialize(p.page(page_number).object_list)
                payload['notifications'] = serialized_notifications
                new_page_number = int(page_number) + 1
                payload['new_page_number'] = new_page_number
        else:
            return None
    else:
        raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")

    return json.dumps(payload)