"""Public pages views."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def terms_of_service_view(request: HttpRequest) -> HttpResponse:
    return render(request, "pages/terms_of_service.html")


def privacy_policy_view(request: HttpRequest) -> HttpResponse:
    return render(request, "pages/privacy_policy.html")
