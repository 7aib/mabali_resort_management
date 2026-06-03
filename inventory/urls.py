"""Inventory app URL configuration."""
from django.urls import path

from inventory.views import inventory_dashboard

urlpatterns = [
    path("", inventory_dashboard, name='inventory_dashboard'),
]