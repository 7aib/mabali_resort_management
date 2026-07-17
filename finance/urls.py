from django.urls import path

from . import views

app_name = "finance"

urlpatterns = [
    path("finance/pos-entry/", views.pos_entry_view, name="pos_entry"),
]
