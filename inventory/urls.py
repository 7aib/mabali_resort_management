from django.urls import path

from inventory.views import inventory_dashboard

urlpatterns = [
    path("inventory/", inventory_dashboard, name='inventory_dashboard'),
]