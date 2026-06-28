"""Reservations app URL configuration."""
from django.urls import path

from .views import reservation_create_view, reservation_list_view, customer_lookup_api, room_status_view

app_name = 'reservations'

urlpatterns = [
    path("", reservation_list_view, name='reservation_list'),
    path("create/", reservation_create_view, name='reservation_create'),
    path("room-status/", room_status_view, name='room_status'),
    path("api/customer-lookup/", customer_lookup_api, name='customer_lookup'),
]
