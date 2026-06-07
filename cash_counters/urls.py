from django.urls import path
from . import views

app_name = 'cash_counters'

urlpatterns = [
    path('cash-counters/new-guest-entry/', views.entry_form_view, name='entry_form'),
    path('cash-counters/daily-sales/', views.daily_sales_view, name='daily_sales'),
    path('cash-counters/check-customer/', views.check_customer_status, name='check_customer'),
]
