"""Dashboard views for displaying resort management data."""
from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum, Count

from authentication.choices import UserRoles
from cash_counters.models import EntryCounterForm, EntryTransaction


@login_required
def dashboard_view(request: HttpResponse) -> HttpResponse:
    """Display the main dashboard with financial and operational metrics."""
    today = date.today()

    counters = [
        {"name": "Restaurant", "pos": 150000},
        {"name": "Boating", "pos": 80000},
        {"name": "Parasailing", "pos": 60000},  # excluded from POS in totals per rule
        {"name": "Cafe", "pos": 40000},
    ]
    total_pos_ex_parasailing = sum(
        c["pos"] for c in counters if c["name"].lower() != "parasailing"
    )

    # ── Live guest entry stats for today ──
    today_entries = EntryCounterForm.objects.filter(created_at__date=today)
    total_adults = today_entries.aggregate(s=Sum('no_of_persons'))['s'] or 0
    total_kids   = today_entries.aggregate(s=Sum('no_of_kids'))['s'] or 0
    guest_entry = {
        "date":   today,
        "adults": total_adults,
        "kids":   total_kids,
        "total":  total_adults + total_kids,
    }

    avg_spend_per_person = round(
        (total_pos_ex_parasailing or 0) / (guest_entry["total"] or 1), 2
    )

    expenses = [
        {"title": "Fuel & Maintenance", "amount": 18000},
        {"title": "Supplies", "amount": 12500},
        {"title": "Utilities", "amount": 9200},
    ]

    trusts_today = [
        {
            "payer": "ABC Travels",
            "amount": 35000,
            "reference": "TR-2025-1001",
            "paid": True,
        },
        {
            "payer": "Walk-in Group",
            "amount": 15000,
            "reference": "TR-2025-1002",
            "paid": True,
        },
    ]

    complimentary = [
        {"item": "Welcome Drinks", "qty": 12, "reason": "VIP Guests"},
        {"item": "Boat Ride", "qty": 2, "reason": "Service Recovery"},
    ]

    room_bookings = {
        "night_stay_count": 22,
        "rooms_occupied": 18,
        "rooms_available": 12,
    }

    events_today = [
        {
            "guest_name": "Khan Family",
            "location": "Lakeside Lawn",
            "event_type": "Birthday",
            "amount": 65000,
        },
        {
            "guest_name": "BluePeak Corp",
            "location": "Hall A",
            "event_type": "Team Meetup",
            "amount": 120000,
        },
    ]

    expense_refunds = [
        {"type": "Expense", "title": "Decor Vendor", "amount": 7000},
        {"type": "Refund", "title": "Meal Refund", "amount": 2500},
    ]

    # ── Live transaction history (last 10 today) ──
    recent_transactions = (
        EntryTransaction.objects
        .filter(created_at__date=today)
        .select_related('entry_form__customer')
        .order_by('-created_at')[:10]
    )

    # Role-based visibility for amounts (CEO, ACCOUNTANT)
    user_role = getattr(request.user, "role", None)
    can_view_amounts = user_role in (UserRoles.CEO, UserRoles.ACCOUNTANT)

    context = {
        "today": today,
        "counters": counters,
        "total_pos_ex_parasailing": total_pos_ex_parasailing,
        "guest_entry": guest_entry,
        "avg_spend_per_person": avg_spend_per_person,
        "expenses": expenses,
        "trusts_today": trusts_today,
        "complimentary": complimentary,
        "room_bookings": room_bookings,
        "events_today": events_today,
        "expense_refunds": expense_refunds,
        "recent_transactions": recent_transactions,
        "can_view_amounts": can_view_amounts,
    }
    return render(request, "dashboard/index.html", context)
