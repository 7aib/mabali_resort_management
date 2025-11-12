
from .models import CashCounterLog, MainCashierReceipt


def CashCounterLogViewSet(request):
    queryset = CashCounterLog.objects.select_related("on_duty_cashier", "handover_to").all().order_by("-date")

    return queryset



def MainCashierReceiptViewSet(request):
    queryset = MainCashierReceipt.objects.select_related("received_from", "on_duty_cashier").all().order_by("-date")
    return queryset

