from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.db import IntegrityError
import re

from authentication.models import User
from authentication.choices import UserRoles
from mabali_resort_management.decorators import roles_required

from .forms import LoginForm


def _validate_phone_number(phone_number: str) -> tuple[bool, str]:
    """
    Validate phone number format.

    Args:
        phone_number: Phone number in +92XXXXXXXXXX format (13 chars)

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not phone_number or not phone_number.strip():
        # Phone number is optional
        return True, ""

    phone_number = phone_number.strip()

    # Enforce +92 prefix pattern: +92 followed by 10 digits
    if not re.match(r'^\+92[0-9]{10}$', phone_number):
        return False, "Phone number must be in +92XXXXXXXXXX format (e.g. +9230112345678)"

    return True, ""


def _check_phone_number_exists(phone_number: str, exclude_user_id: int = None) -> bool:
    """
    Check if phone number is already used by another employee.
    
    Args:
        phone_number: Phone number to check
        exclude_user_id: User ID to exclude from check (for editing)
    
    Returns:
        True if phone number exists for another user, False otherwise
    """
    if not phone_number or not phone_number.strip():
        return False
    
    query = User.objects.filter(phone_number=phone_number.strip())
    if exclude_user_id:
        query = query.exclude(id=exclude_user_id)
    
    return query.exists()


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
@roles_required(UserRoles.CEO, UserRoles.ACCOUNTANT, UserRoles.HR_MANAGER)
def employee_dashboard(request: HttpResponse) -> HttpResponse:
    """Display a list of employees excluding CEO users."""
    employees = User.objects.exclude(role=UserRoles.CEO)
    return render(request, "employee_dashboard.html", {"employees": employees})


@login_required
def profile_view(request: HttpResponse) -> HttpResponse:
    """Display the current user's profile."""
    return render(request, "profile.html")

from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from django.shortcuts import render, redirect

@login_required
@roles_required(UserRoles.CEO, UserRoles.HR_MANAGER)
def employee_create(request):
    """Create a new employee."""

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        role = request.POST.get("role", UserRoles.CUSTOMER).strip()
        password = request.POST.get("password", "")
        phone_number = request.POST.get("phone_number", "").strip()

        # Create an unsaved user object so entered data is retained on errors
        employee = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            role=role,
            phone_number=phone_number if phone_number else None,
            is_active=True,
        )

        # Validate phone number
        is_valid, error_msg = _validate_phone_number(phone_number)
        if not is_valid:
            messages.error(request, f"Phone Number Error: {error_msg}")
            return render(
                request,
                "employee_create.html",
                {"employee": employee, "roles": UserRoles.choices},
            )

        # Check phone number uniqueness
        if phone_number and _check_phone_number_exists(phone_number):
            messages.error(
                request,
                "Phone Number Error: This phone number is already registered to another user.",
            )
            return render(
                request,
                "employee_create.html",
                {"employee": employee, "roles": UserRoles.choices},
            )

        try:
            employee.password = make_password(password)
            employee.save()

            messages.success(
                request,
                f"Employee '{employee.username}' created successfully."
            )
            return redirect("employee_detail", pk=employee.id)

        except IntegrityError:
            messages.error(
                request,
                "Error: Username, email, or phone number already exists."
            )
            return render(
                request,
                "employee_create.html",
                {"employee": employee, "roles": UserRoles.choices},
            )

    return render(
        request,
        "employee_create.html",
        {"roles": UserRoles.choices},
    )

@login_required
def employee_detail(request: HttpResponse, pk: int) -> HttpResponse:
    """Display details for a specific employee."""
    employee = get_object_or_404(User, pk=pk)
    return render(request, "employee_detail.html", {"employee": employee})


@login_required
@roles_required(UserRoles.CEO, UserRoles.ACCOUNTANT, UserRoles.HR_MANAGER)
def employee_edit(request: HttpResponse, pk: int) -> HttpResponse:
    """Edit a specific employee's details. Only CEO and HR Manager can edit."""
    employee = get_object_or_404(User, pk=pk)
    
    if request.method == "POST":
        # Update employee object with submitted data so the form retains it on error
        employee.first_name = request.POST.get("first_name", "")
        employee.last_name = request.POST.get("last_name", "")
        employee.email = request.POST.get("email", "")
        employee.role = request.POST.get("role", employee.role)
        employee.is_active = request.POST.get("is_active") == "on"
        
        phone_number = request.POST.get("phone_number", "").strip()
        employee.phone_number = phone_number if phone_number else None

        # Validate phone number format
        is_valid, error_msg = _validate_phone_number(phone_number)
        
        if not is_valid:
            messages.error(request, f"Phone Number Error: {error_msg}")
            return render(request, "employee_edit.html", {"employee": employee, "roles": UserRoles.choices})
            
        # Check if phone number is already taken
        if phone_number and _check_phone_number_exists(phone_number, exclude_user_id=employee.id):
            messages.error(request, "Phone Number Error: This phone number is already registered to another user.")
            return render(request, "employee_edit.html", {"employee": employee, "roles": UserRoles.choices})
        
        try:
            employee.save()
            messages.success(request, f"Employee '{employee.username}' updated successfully.")
            return redirect("employee_detail", pk=employee.id)
        except IntegrityError as e:
            messages.error(request, "Error: Another employee might already be using this email or username.")
            return render(request, "employee_edit.html", {"employee": employee, "roles": UserRoles.choices})
    
    return render(request, "employee_edit.html", {"employee": employee, "roles": UserRoles.choices})


@login_required
@roles_required(UserRoles.CEO, UserRoles.ACCOUNTANT, UserRoles.HR_MANAGER)
def employee_delete(request: HttpResponse, pk: int) -> HttpResponse:
    """Delete a specific employee. Only CEO and HR Manager can delete."""
    employee = get_object_or_404(User, pk=pk)
    
    if request.method == "POST":
        username = employee.username
        employee.delete()
        messages.success(request, f"Employee '{username}' deleted successfully.")
        return redirect("employee_dashboard")
    
    return render(request, "employee_delete.html", {"employee": employee})
