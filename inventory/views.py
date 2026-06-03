"""Inventory management views."""
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required


@login_required
def inventory_dashboard(request: HttpResponse) -> HttpResponse:
    """Display the inventory dashboard."""
    return render(request, 'inventory/dashboard.html')