from django.urls import path

from . import views

app_name = "complementary"

urlpatterns = [
    path("complementary/free-billing/", views.free_billing_view, name="free_billing"),
]
