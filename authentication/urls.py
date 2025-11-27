from django.urls import path

from .views import logout_view, login_view, employee_list_view, employee_create_view, employee_update_view, employee_delete_view

urlpatterns = [
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("employees/", employee_list_view, name="employee_list"),
    path("employees/create/", employee_create_view, name="employee_create"),
    path("employees/<int:pk>/update/", employee_update_view, name="employee_update"),
    path("employees/<int:pk>/delete/", employee_delete_view, name="employee_delete"),
]
