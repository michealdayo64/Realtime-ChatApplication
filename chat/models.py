from django.db import models
from django.conf import settings
# Create your models here.


class PrivateChatRoom(models.Model):
    """
    A private room for people to chat
    """
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE, related_name = "user1")
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE, related_name = "user2", null = True, blank = True)

    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"A chat between {self.user1} and {self.user2}"

    @property
    def group_name(self):
        """
        Returns the channels group name that socket shoup subscribe to so they get sent 
        messages as they are generated
        """
        return f"PrivateChatRoom-{self.id}"


class RoomChatMessageManager(models.Manager):
    def by_room(self, room):
        qs = RoomChatMessage.objects.filter(room = room).order_by("-timestamp")
        return qs

class RoomChatMessage(models.Model):
    """
    Chat message created by a user inside a room
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE)
    room = models.ForeignKey(PrivateChatRoom, on_delete = models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add = True)
    content = models.TextField(unique = False, blank = False)

    objects = RoomChatMessageManager()

    def __str__(self):
        return self.content
