from django.shortcuts import render

# Create your views here.

def inventory_dashboard(request):
    return render(request, 'inventory/dashboard.html')