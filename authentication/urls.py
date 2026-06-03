from django.urls import path

from .views import (
    logout_view, 
    login_view, 
    employee_dashboard, 
    profile_view, 
    employee_detail,
    employee_edit,
    employee_delete
)

urlpatterns = [
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),
    path("employee_dashboard/", employee_dashboard, name="employee_dashboard"),
    path("employee/<int:pk>/", employee_detail, name="employee_detail"),
    path("employee/<int:pk>/edit/", employee_edit, name="employee_edit"),
    path("employee/<int:pk>/delete/", employee_delete, name="employee_delete"),
]
