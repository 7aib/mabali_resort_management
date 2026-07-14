"""Public pages views."""
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse


def terms_of_service_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'pages/terms_of_service.html')


def privacy_policy_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'pages/privacy_policy.html')
