from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .decorators import ceo_or_hr_required
from authentication.models import User

from .forms import LoginForm, UserForm, UserUpdateForm


def login_view(request):
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


def logout_view(request):
    from django.contrib.auth import logout

    logout(request)
    return redirect("login")

@login_required
@ceo_or_hr_required
def employee_list_view(request):
    users = User.objects.all()
    return render(request, "user_list.html", {"users": users})

@login_required
@ceo_or_hr_required
def employee_create_view(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect("employee_list")
    else:
        form = UserForm()
    return render(request, "user_form.html", {"form": form, "title": "Create User"})

@login_required
@ceo_or_hr_required
def employee_update_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect("employee_list")
    else:
        form = UserUpdateForm(instance=user)
    return render(request, "user_form.html", {"form": form, "title": "Update User"})

@login_required
@ceo_or_hr_required
def employee_delete_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        user.delete()
        messages.success(request, "User deleted successfully.")
        return redirect("employee_list")
    return render(request, "user_confirm_delete.html", {"user": user})