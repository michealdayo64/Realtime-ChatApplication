from django.urls import path
from friend import views

app_name = "friend"

urlpatterns = [
    path('list/<user_id>/', views.friend_list_view, name = "list"),
    path('friend_request/', views.send_frend_request, name = "friend-request"),
    path('friend_request_list/<user_id>/', views.friend_requests, name = "friend-request-list"),
    path('accept_friend_request/<friend_request_id>/', views.accept_friend_request, name = "accept-friend-request"),
    path('remove_friend/', views.remove_friend, name = "remove-friend"),
    path('decline_friend_request/<friend_request_id>/', views.decline_friend_request, name = "decline_friend_request"),
    path('cancel_friend_request/', views.cancel_friend_request, name = "cancel_friend_request"),
]