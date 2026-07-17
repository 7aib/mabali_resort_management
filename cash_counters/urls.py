from django.urls import path

from . import views

app_name = "cash_counters"

urlpatterns = [
    path("cash-counters/new-guest-entry/", views.entry_form_view, name="entry_form"),
    path("cash-counters/daily-sales/", views.daily_sales_view, name="daily_sales"),
    path(
        "cash-counters/check-customer/",
        views.check_customer_status,
        name="check_customer",
    ),
    path(
        "cash-counters/cash-handover/", views.cash_handover_view, name="cash_handover"
    ),
    path(
        "cash-counters/cash-register/", views.cash_register_view, name="cash_register"
    ),
    path(
        "cash-counters/ticket-refund/", views.ticket_refund_view, name="ticket_refund"
    ),
]
