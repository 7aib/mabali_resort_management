from django.urls import path

from django.contrib.auth import views as auth_views
from .views import (
    logout_view,
    login_view,
    employee_list_view,
    employee_create_view,
    employee_update_view,
    employee_delete_view,
    register_view,
    profile_view,
    change_password_view,
)

urlpatterns = [
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("employees/", employee_list_view, name="employee_list"),
    path("employees/create/", employee_create_view, name="employee_create"),
    path("employees/<int:pk>/update/", employee_update_view, name="employee_update"),
    path("employees/<int:pk>/delete/", employee_delete_view, name="employee_delete"),
    path("register/", register_view, name="register"),
    path("profile/", profile_view, name="profile"),
    path("change-password/", change_password_view, name="change_password"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(template_name="password_reset.html"),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
