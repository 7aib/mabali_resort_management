"""Dashboard views for displaying resort management data."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone

from authentication.choices import UserRoles
from authentication.models import User
from cash_counters.models import EntryCounterForm, EntryTransaction
from finance.models import POS
from complementary.models import FreeBilling
from cash_counters.models import TicketRefund
from reservations.models import Room, Reservation
from reservations.choices import ReservationStatusChoices
from inventory.models import FuelTransactionLog, AmmoTransactionLog
from inventory.choices import StockStatusChoices
from error_logs.decorators import log_errors


@login_required
@log_errors
def dashboard_view(request: HttpResponse) -> HttpResponse:
    """Display the main dashboard with financial and operational metrics."""
    today = timezone.localdate()

    # ── POS totals today by counter type ──
    pos_qs = POS.objects.filter(date=today)
    pos_by_counter = (
        pos_qs.values('counter_type')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    total_pos_today = pos_qs.aggregate(s=Sum('amount'))['s'] or 0

    # ── Guest entry stats today ──
    today_entries = EntryCounterForm.objects.filter(created_at__date=today)
    total_adults = today_entries.aggregate(s=Sum('no_of_persons'))['s'] or 0
    total_kids = today_entries.aggregate(s=Sum('no_of_kids'))['s'] or 0
    total_guests = total_adults + total_kids
    new_guests = today_entries.filter(status='New').count()
    old_guests = today_entries.filter(status='Old').count()

    # ── Revenue breakdown today ──
    entry_revenue = EntryTransaction.objects.filter(
        created_at__date=today
    ).aggregate(s=Sum('amount'))['s'] or 0

    free_billing_total = FreeBilling.objects.filter(
        date=today
    ).aggregate(s=Sum('total_bill_amount'))['s'] or 0

    refund_total = TicketRefund.objects.filter(
        date=today
    ).aggregate(s=Sum('total_amount_refunded'))['s'] or 0

    # ── Complimentary / Free billing today ──
    free_bills = FreeBilling.objects.filter(date=today).order_by('-created_at')[:10]
    free_bill_count = FreeBilling.objects.filter(date=today).count()

    # ── Room bookings ──
    total_rooms = Room.objects.filter(is_deleted=False, is_active=True).count()
    active_reservations = Reservation.objects.filter(
        is_deleted=False,
        status__in=[ReservationStatusChoices.CONFIRMED, ReservationStatusChoices.CHECKED_IN],
    )
    occupied_count = 0
    reserved_count = 0
    for res in active_reservations:
        if res.check_in_date <= today < res.check_out_date:
            occupied_count += 1
        elif res.check_in_date > today:
            reserved_count += 1
    available_count = total_rooms - occupied_count - reserved_count

    # ── Inventory alerts (low stock) ──
    fuel_required = FuelTransactionLog.objects.filter(
        transaction_status=StockStatusChoices.REQUIRED
    ).count()
    ammo_required = AmmoTransactionLog.objects.filter(
        transaction_status=StockStatusChoices.REQUIRED
    ).count()
    pending_orders = fuel_required + ammo_required

    # ── Ticket refunds today ──
    refunds_today = TicketRefund.objects.filter(date=today).order_by('-created_at')[:10]
    refund_count = TicketRefund.objects.filter(date=today).count()

    # ── Recent entry transactions (last 10 today) ──
    recent_transactions = (
        EntryTransaction.objects
        .filter(created_at__date=today)
        .select_related('entry_form__customer')
        .order_by('-created_at')[:10]
    )

    # ── Visit type breakdown ──
    visit_breakdown = (
        today_entries.values('visit_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Role-based visibility for amounts
    user_role = getattr(request.user, 'role', None)
    can_view_amounts = user_role in (UserRoles.CEO, UserRoles.ACCOUNTANT, UserRoles.HR_MANAGER)

    # ── Overall stats (all time) ──
    total_guests_all = EntryCounterForm.objects.count()
    total_pos_all = POS.objects.aggregate(s=Sum('amount'))['s'] or 0
    total_reservations = Reservation.objects.filter(is_deleted=False).count()

    context = {
        'today': today,

        # POS
        'pos_by_counter': pos_by_counter,
        'total_pos_today': total_pos_today,

        # Guests
        'total_adults': total_adults,
        'total_kids': total_kids,
        'total_guests': total_guests,
        'new_guests': new_guests,
        'old_guests': old_guests,
        'visit_breakdown': visit_breakdown,

        # Revenue
        'entry_revenue': entry_revenue,
        'free_billing_total': free_billing_total,
        'refund_total': refund_total,

        # Free billing
        'free_bills': free_bills,
        'free_bill_count': free_bill_count,

        # Rooms
        'total_rooms': total_rooms,
        'occupied_count': occupied_count,
        'reserved_count': reserved_count,
        'available_count': available_count,

        # Inventory
        'pending_orders': pending_orders,

        # Refunds
        'refunds_today': refunds_today,
        'refund_count': refund_count,

        # Transactions
        'recent_transactions': recent_transactions,

        # All-time
        'total_guests_all': total_guests_all,
        'total_pos_all': total_pos_all,
        'total_reservations': total_reservations,

        # Permissions
        'can_view_amounts': can_view_amounts,
    }
    return render(request, 'dashboard/index.html', context)
