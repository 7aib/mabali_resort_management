"""Inventory app URL configuration."""
from django.urls import path

from inventory.views import inventory_dashboard, generator_log_view, inventory_item_create_view, inventory_item_list_view, ambulance_log_view, fuel_entry_view, ammo_entry_view

app_name = 'inventory'

urlpatterns = [
    path("", inventory_dashboard, name='inventory_dashboard'),
    path("items/", inventory_item_list_view, name='item_list'),
    path("items/create/", inventory_item_create_view, name='item_create'),
    path("generator-log/", generator_log_view, name='generator_log'),
    path("ambulance-log/", ambulance_log_view, name='ambulance_log'),
    path("fuel-entry/", fuel_entry_view, name='fuel_entry'),
    path("ammo-entry/", ammo_entry_view, name='ammo_entry'),
]