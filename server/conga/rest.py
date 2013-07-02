"""PiConga server JSON API"""

from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.contrib.auth.models import User
from conga.models import CongaUser, Conga, Message
import json



@csrf_exempt
def user(request, username):
    """Handle details for a single user"""

    # All requests apart from a POST (to create the user) must have a valid
    # session
    if request.method != "POST" and not request.user.is_authenticated():
        return HttpResponse(status=403)

    # All but get requests need username and password to complete.
    if request.method != "GET":
        try:
            params = json.loads(request.body)
            username = params["username"]
            password = params["password"]
        except:
            return HttpResponse(status=400)

        if username is None or password is None:
            return HttpResponse(status=400)

    # Handle request specific processing.
    if request.method == "POST":
        # POST - i.e. user creation.
        # Authenticate against the user DB in django
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                # All OK - add the user and fall out to return current user.
                cu = CongaUser.objects.get(user__username__iexact=username)
                cu.host=request.get_host()
                cu.save()
                login(request, user)
            else:
                # The account is disabled - reject the login.
                return HttpResponse(status=403)
        else:
            # Failed authentication - either create user or reject duplicate.
            if User.objects.filter(username__iexact=username).count() >= 1:
                return HttpResponse(status=403)
            else:
                u = User.objects.create(username=username)
                u.set_password(password)
                cu = CongaUser.objects.create(user=u, host=request.get_host())
                cu.save()
                u.save()
    elif request.method == "DELETE":
        # DELETE - i.e. user deletion
        # Find the user
        user = authenticate(username=username, password=password)
        if user is None:
            return HttpResponse(status=403)

        # Logout and delete the account and return blank page.
        u = User.objects.get(username__iexact=username)
        if u.congauser is not None:
            u.congauser.delete()
        u.delete()
        logout(request)
        return HttpResponse(status=200)

    # Default processing at this point is to retun as per a "GET" request.
    # Find the user
    u = User.objects.get(username__iexact=username)

    # Build up the resulting JSON for the user
    d = {
        "username": u.username,
        "host": u.congauser.host,
    }
    return HttpResponse(json.dumps(d))

@csrf_exempt
def status(request):
    """Return summary data about the system"""

    # Reject unathorized users
    if not request.user.is_authenticated():
        return HttpResponse(status=403)

    # Find all the users
    users = CongaUser.objects.all().count()
    congas = Conga.objects.all().count()
    messages = Message.objects.all().count()

    # Build up the resulting JSON for the user
    d = {
        "users": users,
        "congas": congas,
        "messages": messages,
    }
    return HttpResponse(json.dumps(d))

