from django.urls import path

from .views import (
    change_password_view,
    employee_create,
    employee_dashboard,
    employee_delete,
    employee_detail,
    employee_edit,
    login_view,
    logout_view,
    profile_view,
)

urlpatterns = [
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),
    path("change-password/", change_password_view, name="change_password"),
    path("employee_dashboard/", employee_dashboard, name="employee_dashboard"),
    path("employee_create/", employee_create, name="employee_create"),
    path("employee/<int:pk>/", employee_detail, name="employee_detail"),
    path("employee/<int:pk>/edit/", employee_edit, name="employee_edit"),
    path("employee/<int:pk>/delete/", employee_delete, name="employee_delete"),
]
