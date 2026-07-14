from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from .views import terms_of_service_view, privacy_policy_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("terms-of-service/", terms_of_service_view, name='terms_of_service'),
    path("privacy-policy/", privacy_policy_view, name='privacy_policy'),
    path("", include("authentication.urls")),
    path("", include("dashboard.urls")),
    path("inventory/", include("inventory.urls")),
    path("", include("cash_counters.urls")),
    path("", include("finance.urls")),
    path("reservations/", include("reservations.urls")),
    path("", include("complementary.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
