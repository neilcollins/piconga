"""PiConga central administration server"""

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

def error(request):
    """Generic error handler for the conga server"""
    return render(request, "conga/error.html")

def index(request):
    """Simple redirect to main or request login"""
    if request.user.is_authenticated():
        return redirect("main")
    else:
        return render(request, "conga/login.html")

def signin(request):
    """Login processing for the conga GUI"""

    # Extract credentials from the POST
    username = request.POST['username']
    password = request.POST['password']

    # Authenticate against the user DB in django
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            if user.is_staff:
                # All OK - accept the user and redirect to main page.
                login(request, user)
                return redirect("main")
            else:
                # The account is just a user - reject the login
                return render(request,
                              "conga/login.html",
                              {"error": "Insufficient privileges"})
        else:
            # The account is disabled - reject the login.
            return render(request,
                          "conga/login.html",
                          {"error": "Account deactivated"})
    else:
        # No such account - reject he login
        return render(request,
                      "conga/login.html",
                      {"error": "Bad login credentials"})

def signout(request):
    """Logout processing for the conga GUI"""

    # Logout and redirect to start.
    logout(request)
    return redirect("index")

@login_required
def main(request):
    """Main page for the conga GUI"""
    return render(request, "conga/main.html", {"user": request.user})

