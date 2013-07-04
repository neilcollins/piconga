"""PiConga server JSON API"""

from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max, Count
from conga.models import CongaUser, Conga, Message, CongaMember
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

            # Original POST also needs a mac address.
            if request.method == "POST":
                mac = params["mac"]
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
                cu.host = request.META.get('HTTP_X_FORWARDED_FOR') or \
                          request.META.get('REMOTE_ADDR')
                cu.mac = mac
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
                # Create the user.
                u = User.objects.create(username=username)
                u.set_password(password)
                cu = CongaUser.objects.create(user=u, host=request.get_host())
                cu.save()
                u.save()

                # Now authenticate the user we just created.
                user = authenticate(username=username, password=password)
                login(request, user)
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

    # Default processing at this point is to return as per a "GET" request.
    # Find the user
    u = User.objects.get(username__iexact=username)

    # Build up the resulting JSON for the user
    d = {
        "username": u.username,
        "host": u.congauser.host,
        "mac": u.congauser.mac,
    }
    return HttpResponse(json.dumps(d))

@csrf_exempt
def conga(request, name):
    """Handle details for a single conga"""

    # All requests must have a valid session
    if not request.user.is_authenticated():
        return HttpResponse(status=403)

    # POST/PUT - i.e. create/modify- requests also need a password
    if request.method in ("POST", "PUT"):
        try:
            params = json.loads(request.body)
            name = params["name"]
            password = params["password"]
        except:
            return HttpResponse(status=400)

    # Handle request specific processing.
    if request.method == "POST":
        # POST - i.e. conga creation.
        try:
            c = Conga.objects.create(owner = request.user,
                                     name=name, 
                                     password=password)
            c.save()
            cm = CongaMember.objects.create(conga=c,
                                            member=request.user,
                                            index=0)
            cm.save()
        except IntegrityError, e:
            # This is trying to claim an existing conga.
            print e
            return HttpResponse(status=409)
    elif request.method == "PUT":
        # PUT - i.e. add to the end of the conga.
        try:
            c = Conga.objects.get(name__iexact=name, password__iexact=password)
            i = CongaMember.objects.filter(conga__exact=c).count()
            cm = CongaMember.objects.create(conga=c,
                                            member=request.user,
                                            index=i)
            cm.save()
        except ObjectDoesNotExist, e:
            # This is trying to add to a conga with bad credentials
            return HttpResponse(status=409)
    elif request.method == "DELETE":
        # DELETE - i.e. conga deletion
        # Delete the conga and return blank page.
        c = Conga.objects.get(name__iexact=name)
        c.delete()
        return HttpResponse(status=200)

    # Default processing at this point is to return as per a "GET" request.
    # Find the conga
    try:
        c = Conga.objects.get(name__iexact=name)
    except ObjectDoesNotExist, e:
        # Object not found - return an error
        return HttpResponse(status=404)

    # Build up the resulting JSON for the conga
    d = {
        "name": c.name,
        "owner": c.owner.username
    }
    return HttpResponse(json.dumps(d))

@csrf_exempt
def status(request):
    """Return summary data about the system"""

    # Reject unathorized users
    if not request.user.is_authenticated():
        return HttpResponse(status=403)

    # Find all the high-level snapshots of the system.
    users = CongaUser.objects.all().count()
    congas = Conga.objects.all().count()
    messages = Message.objects.all().count()
    longest = Conga.objects.annotate(
        num=Count('congamember')).aggregate(Max('num'))["num__max"]
    if longest is None:
        longest = 0

    # Build up the resulting JSON for the user
    d = {
        "users": users,
        "congas": congas,
        "messages": messages,
        "longest": longest,
    }
    return HttpResponse(json.dumps(d))

