from django.urls import path

from .views import logout_view, login_view, employee_dashboard

urlpatterns = [
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("employee_dashboard/", employee_dashboard, name="employee_dashboard"),
]
