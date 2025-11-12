from django.urls import path
from .views import CashCounterLogViewSet, MainCashierReceiptViewSet

urlpatterns = [
    path("/cash-counters/",CashCounterLogViewSet, name="cash-counters"),
    path("/main-cashier-receipts/",MainCashierReceiptViewSet, name="main-cashier-receipts"),
]
