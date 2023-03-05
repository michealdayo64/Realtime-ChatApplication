from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
from friend.utils import get_friend_request_or_false
from account.forms import RegistrationForm, AccountAuthenticationForm, AccountUpdateForm
from .models import Account
from friend.models import FriendRequest, FriendsList
from friend.friendRequestStatus import FriendRequestStatus
import cv2
from django.core import files
import os
from django.core.files.storage import FileSystemStorage
import json
import base64


TEMP_PROFILE_IMAGE_NAME = "temp_profile_image.png"


# Create your views here.
def register_view(request, *args, **kwargs):
    user = request.user
    if user.is_authenticated:
        return HttpResponse(f"You are already authenticated as {user.email}")
    context = {}

    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email').lower()
            raw_password = form.cleaned_data.get('password1')
            account = authenticate(email = email, password = raw_password)
            login(request, account)
            destination = get_redirect_if_exist(request)
            if destination:
                return redirect(destination)
            return redirect('home')
        else:
            context['registration_form'] = form

    return render(request, "account/register.html", context)


def logout_view(request):
    logout(request)
    return redirect("home")

def login_view(request, *args, **kwargs):
    context = {}
    user = request.user
    if user.is_authenticated:
        return redirect("home")

    if request.POST:
        form = AccountAuthenticationForm(request.POST)
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(email = email, password = password)
            if user:
                login(request, user)
                destination = get_redirect_if_exist(request)
                if destination:
                    return redirect(destination)
                return redirect("home")
        else:
            context['login_form'] = form
    return render(request, 'account/login.html', context)


def get_redirect_if_exist(request):
    redirect = None
    if request.GET:
        if request.GET.get("next"):
            redirect = str(request.GET.get('next'))
    return redirect

def account_view(request, *args, **kwargs):
    context = {}
    user_id = kwargs.get("user_id")
    try:
        account = Account.objects.get(pk = user_id)
    except Account.DoesNotExist:
        return HttpResponse("That user does not exist")
    if account:
        context['id'] = account.id
        context['username'] = account.username
        context['email'] = account.email
        context['profile_image'] = account.profile_image.url
        context['hide_email'] = account.hide_email

        try:
            friend_list = FriendsList.objects.get(user = account)
        except FriendsList.DoesNotExist:
            friend_list = FriendsList(user = account)
            friend_list.save()
        friends = friend_list.friends.all()
        context['friends'] = friends
        # Define state template variables
        is_self = True
        is_friend = False
        request_sent = FriendRequestStatus.NO_REQUEST_SENT.value
        friend_requests = None
        user = request.user
        if user.is_authenticated and user != account:
            is_self = False
            if friends.filter(pk = user.id):
                is_friend = True
            else:
                is_friend = False
                #CASE1: Request has been sent from THEM to YOU:
                #FriendRequestStatus.THEM_SENT_TO_YOU
                if get_friend_request_or_false(sender = account, reciever = user) != False:
                    request_sent = FriendRequestStatus.THEM_SENT_TO_YOU.value
                    context['pending_friend_request_id'] = get_friend_request_or_false(
                        sender = account, reciever = user
                    ).id
                #CASE1: Request has been sent from YOU to THEM:
                #FriendRequestStatus.YOU_SENT_TO_THEM
                elif get_friend_request_or_false(sender = user, reciever = account) != False:
                    request_sent = FriendRequestStatus.YOU_SENT_TO_THEM.value
                #CASE1: No Request has been sent. FriendRequestStatus.NO_REQUEST_SENT
                else:
                    request_sent = FriendRequestStatus.NO_REQUEST_SENT.value
        elif not user.is_authenticated:
            is_self = False
        else:
            try:
                friend_requests = FriendRequest.objects.filter(reciever = user, is_active = True)
            except:
                pass

        context['is_self'] = is_self
        context['is_friend'] = is_friend
        context['BASE_URL'] = settings.BASE_URL
        context['request_sent'] = request_sent
        context['friend_requests'] = friend_requests

        return render(request, "account/account.html", context)

def account_search_view(request, *args, **kwargs):
    context = {}

    if request.method == 'GET':
        search_query = request.GET.get("q")
        if len(search_query) > 0:
            search_results = Account.objects.filter(email__icontains=search_query).filter(
                username__icontains=search_query).distinct()

            user = request.user
            accounts = []
            if user.is_authenticated:
                auth_user_friend_list = FriendsList.objects.get(user = user)
                for account in search_results:
                    accounts.append((account, auth_user_friend_list.is_mutual_friend(account)))
                context['accounts'] = accounts
            else:
                for account in search_results:
                    accounts.append((account, False))
                context['accounts'] = accounts

    return render(request, 'account/search_results.html', context)

def edit_account_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect("login")
    user_id = kwargs.get("user_id")
    try:
        account = Account.objects.get(pk = user_id)
    except Account.DoesNotExist:
        return HttpResponse("Something went wrong")
    if account.pk != request.user.pk:
        return HttpResponse("You cannot edit someone elses profile")
    context = {}
    if request.POST:
        form = AccountUpdateForm(request.POST, request.FILES, instance = request.user)
        if form.is_valid():
            # delete the old profile image so the name is preserved
            #account.profile_image.delete()
            form.save()
            return redirect("account:view", user_id=account.pk)
        else:
            form = AccountUpdateForm(request.POST, instance = request.user,
                initial = {
                    "id": account.pk,
                    "email": account.email,
                    "username": account.username,
                    "profile_image": account.profile_image,
                    "hide_email": account.hide_email
                }
            )
            context['form'] = form
    else:
        form = AccountUpdateForm( 
                initial = {
                    "id": account.pk,
                    "email": account.email,
                    "username": account.username,
                    "profile_image": account.profile_image,
                    "hide_email": account.hide_email
                }
            )
        context['form'] = form 
    context['DATA_UPLOAD_MAX_MEMORY_SIZE'] = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    return render(request, 'account/edit_account.html', context)

def save_temp_profile_image_from_base64String(imageString, user):
    INCORRECT_PADDING_EXCEPTION = "incorrect padding"
    try:
        if not os.path.exists(settings.TEMP):
            os.mkdir(settings.TEMP)
        if not os.path.exists(f"{settings.TEMP}/{user.pk}"):
            os.mkdir(f"{settings.TEMP}/{user.pk}")
        url = os.path.join(f"{settings.TEMP}/{user.pk}", TEMP_PROFILE_IMAGE_NAME)
        storage = FileSystemStorage(location = url)
        img = base64.b64decode(imageString)
        with storage.open("", "wb+") as destination:
            destination.write(img)
            destination.close()
        return url
    except Exception as e:
        if str(e) == INCORRECT_PADDING_EXCEPTION:
            imageString += "=" * ((4 - len(imageString) % 4) % 4)
            return save_temp_profile_image_from_base64String(imageString, user)
    return None

def crop_image(request, *args, **kwargs):
    payload = {}
    user = request.user
    if request.POST and user.is_authenticated:
        try:
            imageString = request.POST.get("image")
            url = save_temp_profile_image_from_base64String(imageString, user)
            img = cv2.imread(url)

            cropX = int(float(str(request.POST.get("cropX"))))
            cropY = int(float(str(request.POST.get("cropY"))))
            cropWidth = int(float(str(request.POST.get("cropWidth"))))
            cropHeight = int(float(str(request.POST.get("cropHeight"))))

            if cropX < 0:
                cropX = 0
            if cropY < 0:
                cropY = 0

            crop_img = img[cropY:cropY + cropHeight, cropX:cropX + cropWidth]
            cv2.imwrite(url, crop_img)
            user.profile_image.delete()
            user.profile_image.save("profile_image.png", files.File(open(url, "rb")))
            user.save()

            payload['result'] = "success"
            payload['cropped_profile_image'] = user.profile_image.url
            os.remove(url)
        except Exception as e:
            payload["result"] = "error"
            payload["exception"] = str(e)
    return HttpResponse(json.dumps(payload), content_type="application/json")