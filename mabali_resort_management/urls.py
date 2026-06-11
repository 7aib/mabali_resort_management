from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("authentication.urls")),
    path("", include("dashboard.urls")),
    path("inventory/", include("inventory.urls")),
    path("", include("cash_counters.urls")),
    path("", include("finance.urls")),
]
