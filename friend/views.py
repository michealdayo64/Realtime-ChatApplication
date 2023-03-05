import json
from django.shortcuts import render, redirect
from account.models import Account
from django.http import HttpResponse
from .models import FriendsList, FriendRequest

# Create your views here.
def friend_list_view(request, *args, **kwargs):
    context = {}
    user = request.user
    if user.is_authenticated:
        user_id = kwargs.get("user_id")
        if user_id:
            try:
                this_user = Account.objects.get(pk = user_id)
                context["this_user"] = this_user
            except Account.DoesNotExist:
                return HttpResponse("This user does not exist")
            
            try:
                friend_list = FriendsList.objects.get(user = this_user)
            except FriendsList.DoesNotExist:
                return HttpResponse(f"Could not find a friends list for {this_user.username}")
            
            # Must be friend to view a friend list
            if user != this_user:
                if not user in friend_list.friends.all():
                    return HttpResponse("You must e a friend to view their friends list")

            friends = [] # [(account1, True), (account2, False)]
            auth_user_friend_list = FriendsList.objects.get(user = user)
            for friend in friend_list.friends.all():
                friends.append((friend, auth_user_friend_list.is_mutual_friend(friend)))
            context['friends'] = friends
    else:
        return HttpResponse("You must be authenticted to view their friends list")
    return render(request, 'friend/friend_list.html', context)

def friend_requests(request, *args, **kwargs):
    context = {}
    user = request.user
    if user.is_authenticated:
        user_id = kwargs.get("user_id")
        account = Account.objects.get(pk = user_id)
        if account == user:
            friend_request_list = FriendRequest.objects.filter(reciever = account, is_active = True)
            context['friend_request_list'] = friend_request_list
        else:
            return HttpResponse("You can't view someone elses friend requests")
    else:
        redirect("login")
    return render(request, "friend/friend_request_list.html", context)

def send_frend_request(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == 'POST':
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            reciever = Account.objects.get(pk = user_id)
            try:
                # Get any friend requests (active and not-active)
                friend_requests = FriendRequest.objects.filter(sender = user, reciever = reciever)
                # find if any of them are active
                try:
                    for request in friend_requests:
                        if request.is_active:
                            raise Exception("You already sent them a friend request")
                    # If none is active, then create a new friend request
                    friend_request = FriendRequest(sender = user, reciever = reciever)
                    friend_request.save()
                    payload['response'] = "Friend request sent."
                except Exception as e:
                    payload['response'] = str(e)
            except FriendRequest.DoesNotExist:
                # There are no friend requests so create one
                friend_request = FriendRequest(sender = user, reciever = reciever)
                friend_request.save()
                payload['response'] = "Friend request sent."
            
            if payload['response'] == None:
                payload['response'] = "Something went wrong."
        else:
            payload['response'] = "Unable to send a friend request."
    else:
        payload['response'] = "You must be aunthenticated to send a friend request."
    return HttpResponse(json.dumps(payload), content_type="application/json")


def accept_friend_request(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "GET" and user.is_authenticated:
        friend_request_id = kwargs.get("friend_request_id")
        if friend_request_id:
            friend_request = FriendRequest.objects.get(pk = friend_request_id)
            # confirm that is the correct request
            if friend_request.reciever == user:
                if friend_request:
                    # found the request. Not accept it.
                    friend_request.accept()
                    payload['response'] = "Friend request accepted"
                else:
                    payload['response'] = "Something went wrong"
            else:
                payload['response'] = "This is not your request to accept"
        else:
            payload['response'] = "Unable to accept friend request"
    else:
        payload['response'] = "You must be authenticated to accept a friend request"
    return HttpResponse(json.dumps(payload), content_type = "application/json")


def remove_friend(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            try:
                removee = Account.objects.get(pk = user_id)
                friend_list = FriendsList.objects.get(user = user)
                friend_list.unfriend(removee)
                payload['response'] = "Succesfully removed that friend"
            except Exception as e:
                payload['response'] = f"Something went wrong: {str(e)}"
        else:
            payload['response'] = "There was an error. Unable to remove that friend"
    else:
        payload['response'] = "You must be authenticated to remove a friend"
    return HttpResponse(json.dumps(payload), content_type = "application/json")         


def decline_friend_request(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "GET" and user.is_authenticated:
        friend_request_id = kwargs.get("friend_request_id")
        if friend_request_id:
            friend_request = FriendRequest.objects.get(pk = friend_request_id)
            # Confirm that it is the corect request
            if friend_request.reciever == user:
                if friend_request:
                    # foud the request. Now decline it.
                    friend_request.decline()
                    payload['response'] = "Friend request decline"
                else:
                    payload['response'] = "Something went wrong"
            else:
                payload['response'] = "This is not ypur friend request to decline"
        else:
            payload['response'] = "Unable to decline that friend request"
    else:
        payload['response'] = "You must be authenticated to remove a friend"
    return HttpResponse(json.dumps(payload), content_type="application/json")

def cancel_friend_request(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            receiver = Account.objects.get(pk = user_id)
            try:
                friend_requests = FriendRequest.objects.filter(sender = user, reciever = receiver, is_active = True)
            except Exception as e:
                payload['response'] = "Nothing to cancel. Friend request deos not exist"
            
            # There should only be a single active friend request at any giving time.
            # Cancel them all just in case.
            if len(friend_requests) > 1:
                for request in friend_requests:
                    request.cancel()
                payload['response'] = "Friend request cancelled"
            else:
                # found the request. Now cancel it.
                friend_requests.first().cancel()
                payload['response'] = "Friend request cancelled"
        else:
            payload['response'] = "Unble to cancel friend request"
    else:
        payload['response'] = "ou must be authenticated to cancel a friend"
    return HttpResponse(json.dumps(payload), content_type="application/json")