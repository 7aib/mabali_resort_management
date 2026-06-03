from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from authentication.models import User
from authentication.choices import UserRoles

from .forms import LoginForm


def login_view(request: HttpResponse) -> HttpResponse:
    """Handle user login with form validation and authentication."""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})


def logout_view(request: HttpResponse) -> HttpResponse:
    """Log out the current user and redirect to login page."""
    logout(request)
    return redirect("login")

@login_required
def employee_dashboard(request: HttpResponse) -> HttpResponse:
    """Display a list of employees excluding CEO users."""
    employees = User.objects.exclude(role=UserRoles.CEO)
    return render(request, "employee_dashboard.html", {"employees": employees})