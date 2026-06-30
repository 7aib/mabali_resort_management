"""Dashboard views for displaying resort management data."""
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum, Count, Q, F
from django.utils import timezone

from authentication.choices import UserRoles
from authentication.models import User
from cash_counters.models import EntryCounterForm, EntryTransaction, CashRegister, CashHandover
from finance.models import POS
from complementary.models import FreeBilling
from cash_counters.models import TicketRefund
from reservations.models import Room, Reservation
from reservations.choices import ReservationStatusChoices
from inventory.models import FuelTransactionLog, AmmoTransactionLog
from inventory.choices import StockStatusChoices
from error_logs.decorators import log_errors

# Counter types to exclude from POS (parasailing is part of Water Sports)
EXEMPT_FROM_POS = ['Water Sports']


@login_required
@log_errors
def dashboard_view(request: HttpResponse) -> HttpResponse:
    """Display the main dashboard with financial and operational metrics."""
    today = timezone.localdate()

    # ── POS totals today by counter type (exempt parasailing/water sports) ──
    pos_qs = POS.objects.filter(date=today).exclude(counter_type__in=EXEMPT_FROM_POS)
    pos_by_counter = (
        pos_qs.values('counter_type')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    total_pos_today = pos_qs.aggregate(s=Sum('amount'))['s'] or 0

    # ── POS by counter with cashier info (main cashier + general cashier) ──
    pos_with_cashier = (
        POS.objects.filter(date=today)
        .exclude(counter_type__in=EXEMPT_FROM_POS)
        .values('counter_type', 'payment_method')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('counter_type')
    )

    # ── Guest entry stats today ──
    today_entries = EntryCounterForm.objects.filter(created_at__date=today)
    total_adults = today_entries.aggregate(s=Sum('no_of_persons'))['s'] or 0
    total_kids = today_entries.aggregate(s=Sum('no_of_kids'))['s'] or 0
    total_guests = total_adults + total_kids
    new_guests = today_entries.filter(status='New').count()
    old_guests = today_entries.filter(status='Old').count()

    # ── Guest Entry Detail (all entries today with details) ──
    guest_entries_detail = (
        today_entries
        .select_related('customer')
        .order_by('-created_at')
    )

    # ── Revenue breakdown today ──
    entry_revenue = EntryTransaction.objects.filter(
        created_at__date=today
    ).aggregate(s=Sum('amount'))['s'] or 0

    # ── Cash Counter Revenue (total from all cash counter entries) ──
    cash_counter_revenue = entry_revenue  # EntryTransaction amounts = cash counter revenue

    # ── Cash Register (received from cashiers today) ──
    cash_register_today = CashRegister.objects.filter(date=today)
    total_cash_register = cash_register_today.aggregate(s=Sum('amount_received'))['s'] or 0
    cash_register_count = cash_register_today.count()

    # ── Cash Handover (handed over to main cashier today) ──
    cash_handover_today = CashHandover.objects.filter(date=today)
    total_cash_handover = cash_handover_today.aggregate(s=Sum('cash_amount'))['s'] or 0
    cash_handover_count = cash_handover_today.count()

    # ── Average spending per person (based on cash counter amounts) ──
    avg_spending_per_person = Decimal('0')
    if total_guests > 0:
        avg_spending_per_person = cash_counter_revenue / Decimal(total_guests)

    free_billing_total = FreeBilling.objects.filter(
        date=today
    ).aggregate(s=Sum('total_bill_amount'))['s'] or 0

    refund_total = TicketRefund.objects.filter(
        date=today
    ).aggregate(s=Sum('total_amount_refunded'))['s'] or 0

    # ── Complimentary / Free billing today ──
    free_bills = FreeBilling.objects.filter(date=today).order_by('-created_at')[:10]
    free_bill_count = FreeBilling.objects.filter(date=today).count()
    free_bills_total = FreeBilling.objects.filter(date=today).aggregate(s=Sum('total_bill_amount'))['s'] or 0
    free_bills_discount = FreeBilling.objects.filter(date=today).aggregate(s=Sum('discount_amount'))['s'] or 0

    # ── Trust Amount (Advance payments received today) ──
    trust_amounts = (
        Reservation.objects.filter(
            advance_date=today,
            advance_amount__gt=0,
            is_deleted=False
        )
        .select_related('customer', 'room')
        .order_by('-created_at')
    )
    total_trust_amount = trust_amounts.aggregate(s=Sum('advance_amount'))['s'] or 0

    # ── Room bookings ──
    total_rooms = Room.objects.filter(is_deleted=False, is_active=True).count()
    active_reservations = Reservation.objects.filter(
        is_deleted=False,
        status__in=[ReservationStatusChoices.CONFIRMED, ReservationStatusChoices.CHECKED_IN],
    ).select_related('customer', 'room').order_by('-check_in_date')
    occupied_count = 0
    reserved_count = 0
    occupied_rooms = []
    reserved_rooms = []
    for res in active_reservations:
        if res.check_in_date <= today < res.check_out_date:
            occupied_count += 1
            occupied_rooms.append(res)
        elif res.check_in_date > today:
            reserved_count += 1
            reserved_rooms.append(res)
    available_count = total_rooms - occupied_count - reserved_count

    # ── Today's Room Bookings (check-ins and check-outs today) ──
    today_checkins = Reservation.objects.filter(
        check_in_date=today, is_deleted=False
    ).select_related('customer', 'room').order_by('-created_at')
    today_checkouts = Reservation.objects.filter(
        check_out_date=today, is_deleted=False
    ).select_related('customer', 'room').order_by('-created_at')

    # ── Tonight stay revenue ──
    night_stay_revenue = (
        Reservation.objects.filter(
            check_in_date__lte=today,
            check_out_date__gt=today,
            is_deleted=False
        ).aggregate(s=Sum('rate_per_night'))['s'] or 0
    )

    # ── Today's Events (Group/Event and Decor team entries) ──
    event_entries = today_entries.filter(
        visit_type__in=['Group', 'Decor team events']
    ).select_related('customer').order_by('-created_at')

    events_today = []
    for entry in event_entries:
        tx = EntryTransaction.objects.filter(entry_form=entry).first()
        events_today.append({
            'guest_name': entry.customer.get_full_name() or entry.customer.username,
            'location': entry.get_location_display(),
            'event_type': entry.get_visit_type_display(),
            'amount': tx.amount if tx else 0,
            'time': entry.created_at,
        })

    # ── Today's expenses / refunds ──
    expense_items = []

    # Ticket refunds
    refunds_today = TicketRefund.objects.filter(date=today).order_by('-created_at')[:10]
    refund_count = TicketRefund.objects.filter(date=today).count()
    for ref in refunds_today:
        expense_items.append({
            'type': 'Ticket Refund',
            'description': ref.get_reason_display(),
            'amount': ref.total_amount_refunded,
            'time': ref.created_at,
        })

    # Free billing as expense
    free_bills_expense = FreeBilling.objects.filter(date=today).order_by('-created_at')
    for fb in free_bills_expense:
        expense_items.append({
            'type': 'Free/Complimentary',
            'description': fb.get_head_display(),
            'amount': fb.total_bill_amount,
            'time': fb.created_at,
        })

    # Sort expenses by time
    expense_items.sort(key=lambda x: x['time'], reverse=True)
    total_expenses = refund_total + free_billing_total

    # ── Inventory alerts (low stock) ──
    fuel_required = FuelTransactionLog.objects.filter(
        transaction_status=StockStatusChoices.REQUIRED
    ).count()
    ammo_required = AmmoTransactionLog.objects.filter(
        transaction_status=StockStatusChoices.REQUIRED
    ).count()
    pending_orders = fuel_required + ammo_required

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
    can_view_amounts = user_role in (UserRoles.CEO, UserRoles.ACCOUNTANT, UserRoles.HR_MANAGER, UserRoles.MAIN_CASHIER)

    # ── Overall stats (all time) ──
    total_guests_all = EntryCounterForm.objects.count()
    total_pos_all = POS.objects.aggregate(s=Sum('amount'))['s'] or 0
    total_reservations = Reservation.objects.filter(is_deleted=False).count()

    context = {
        'today': today,

        # POS
        'pos_by_counter': pos_by_counter,
        'pos_with_cashier': pos_with_cashier,
        'total_pos_today': total_pos_today,

        # Guests
        'total_adults': total_adults,
        'total_kids': total_kids,
        'total_guests': total_guests,
        'new_guests': new_guests,
        'old_guests': old_guests,
        'guest_entries_detail': guest_entries_detail,
        'visit_breakdown': visit_breakdown,

        # Spending
        'avg_spending_per_person': avg_spending_per_person,

        # Revenue
        'entry_revenue': entry_revenue,
        'cash_counter_revenue': cash_counter_revenue,
        'total_cash_register': total_cash_register,
        'cash_register_count': cash_register_count,
        'total_cash_handover': total_cash_handover,
        'cash_handover_count': cash_handover_count,
        'free_billing_total': free_billing_total,
        'refund_total': refund_total,

        # Trust Amount
        'trust_amounts': trust_amounts,
        'total_trust_amount': total_trust_amount,

        # Free billing
        'free_bills': free_bills,
        'free_bill_count': free_bill_count,
        'free_bills_total': free_bills_total,
        'free_bills_discount': free_bills_discount,

        # Rooms
        'total_rooms': total_rooms,
        'occupied_count': occupied_count,
        'reserved_count': reserved_count,
        'available_count': available_count,
        'occupied_rooms': occupied_rooms,
        'reserved_rooms': reserved_rooms,
        'active_reservations': active_reservations,
        'today_checkins': today_checkins,
        'today_checkouts': today_checkouts,
        'night_stay_revenue': night_stay_revenue,

        # Events
        'events_today': events_today,
        'event_count': len(events_today),

        # Expenses
        'expense_items': expense_items[:15],
        'total_expenses': total_expenses,

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
