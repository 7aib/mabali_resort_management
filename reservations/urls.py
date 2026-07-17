"""Reservations app URL configuration."""

from django.urls import path

from .views import (
    customer_lookup_api,
    reservation_create_view,
    reservation_edit_view,
    reservation_list_view,
    room_create_view,
    room_delete_view,
    room_edit_view,
    room_list_view,
    room_status_view,
)

app_name = "reservations"

urlpatterns = [
    path("", reservation_list_view, name="reservation_list"),
    path("create/", reservation_create_view, name="reservation_create"),
    path("<int:pk>/edit/", reservation_edit_view, name="reservation_edit"),
    path("room-status/", room_status_view, name="room_status"),
    path("api/customer-lookup/", customer_lookup_api, name="customer_lookup"),
    # Room management
    path("rooms/", room_list_view, name="room_list"),
    path("rooms/create/", room_create_view, name="room_create"),
    path("rooms/<int:pk>/edit/", room_edit_view, name="room_edit"),
    path("rooms/<int:pk>/delete/", room_delete_view, name="room_delete"),
]
