from django.utils import timezone

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from authentication.choices import UserRoles
from .models import EntryCounterForm, EntryTransaction, CashHandover, CashRegister, TicketRefund
from .constants import CitiesChoices, PaymentMethodChoices, VisitTypeChoices, GateChoices, StatusChoices, CounterTypeChoices, TicketRefundReasonChoices
from mabali_resort_management.constants import PAID_VISIT_PRICE
from mabali_resort_management.decorators import roles_required
from mabali_resort_management.pagination import paginate_queryset
from error_logs.decorators import log_errors

User = get_user_model()

@login_required
@log_errors
def daily_sales_view(request):
    today = timezone.localdate()

    daily_entries = EntryCounterForm.objects.filter(
        created_at__date=today
    ).select_related('customer').prefetch_related('transaction').order_by('-created_at')

    context = paginate_queryset(request, daily_entries, per_page=20)
    return render(request, 'cash_counters/daily_sales.html', context)


@login_required
@log_errors
def entry_form_view(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        name = request.POST.get('name')
        location = request.POST.get('location')
        no_of_persons = int(request.POST.get('no_of_persons', 1))
        no_of_kids = int(request.POST.get('no_of_kids', 0))
        visit_type = request.POST.get('visit_type')
        gate = request.POST.get('gate')
        payment_method = request.POST.get('payment_method', PaymentMethodChoices.CASH)

        if not phone_number or not name:
            messages.error(request, 'Phone number and name are required.')
            return redirect('cash_counters:entry_form')

        customer, created = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={'username': phone_number, 'first_name': name, 'role': UserRoles.CUSTOMER}
        )

        # If user existed but didn't have name set, update it
        if not created and not customer.first_name:
            customer.first_name = name
            customer.save()

        status = StatusChoices.NEW if created else StatusChoices.OLD

        entry = EntryCounterForm.objects.create(
            customer=customer,
            location=location,
            no_of_persons=no_of_persons,
            no_of_kids=no_of_kids,
            visit_type=visit_type,
            gate=gate,
            status=status
        )

        # Create transaction for Paid visits only
        if visit_type == VisitTypeChoices.PAID:
            amount = PAID_VISIT_PRICE * no_of_persons
            EntryTransaction.objects.create(
                entry_form=entry,
                amount=amount,
                payment_method=payment_method
            )

        messages.success(request, 'Entry recorded successfully.')
        return redirect('cash_counters:entry_form')

    context = {
        'cities': CitiesChoices.choices,
        'visit_types': VisitTypeChoices.choices,
        'gates': GateChoices.choices,
        'payment_methods': PaymentMethodChoices.choices,
        'paid_price': PAID_VISIT_PRICE,
        'paid_help_text': f'Entry fee: Rs. {PAID_VISIT_PRICE:,.0f} per person (Paid visits only)',
    }
    return render(request, 'cash_counters/entry_form.html', context)

@login_required
@log_errors
def check_customer_status(request):
    phone_number = request.GET.get('phone_number', '')
    if not phone_number:
        return JsonResponse({'status': 'invalid'})
    
    user = User.objects.filter(phone_number=phone_number).first()
    if user:
        return JsonResponse({
            'status': 'Old',
            'name': user.get_full_name() or user.first_name or user.username
        })
    return JsonResponse({'status': 'New', 'name': ''})


@login_required
@roles_required(UserRoles.CASHIER, UserRoles.CEO )
@log_errors
def cash_handover_view(request):
    today = timezone.localdate()
    
    # Get cashiers and main cashiers for the dropdowns
    cashiers = User.objects.filter(
        role__in=[UserRoles.CASHIER, UserRoles.MAIN_CASHIER],
        is_active=True
    ).order_by('first_name', 'username')
    
    main_cashiers = User.objects.filter(
        role=UserRoles.MAIN_CASHIER,
        is_active=True
    ).order_by('first_name', 'username')
    
    if request.method == 'POST':
        date = request.POST.get('date')
        counter_type = request.POST.get('counter_type')
        cashier_id = request.POST.get('cashier')
        cash_amount = request.POST.get('cash_amount')
        handover_to_id = request.POST.get('handover_to')
        notes = request.POST.get('notes', '')
        
        if not date or not counter_type or not cashier_id or not cash_amount or not handover_to_id:
            messages.error(request, 'All required fields must be filled.')
            return redirect('cash_counters:cash_handover')
        
        try:
            cashier = User.objects.get(id=cashier_id)
            handover_to = User.objects.get(id=handover_to_id)
        except User.DoesNotExist:
            messages.error(request, 'Invalid user selected.')
            return redirect('cash_counters:cash_handover')
        
        CashHandover.objects.create(
            date=date,
            counter_type=counter_type,
            cashier=cashier,
            cash_amount=cash_amount,
            handover_to=handover_to,
            notes=notes
        )
        
        messages.success(request, 'Cash handover recorded successfully.')
        return redirect('cash_counters:cash_handover')
    
    # Get today's handovers
    today_handovers = CashHandover.objects.filter(
        date=today
    ).select_related('cashier', 'handover_to').order_by('-created_at')
    
    context = {
        'counter_types': CounterTypeChoices.choices,
        'cashiers': cashiers,
        'main_cashiers': main_cashiers,
        'today_handovers': today_handovers,
        'today': today,
    }
    return render(request, 'cash_counters/cash_handover.html', context)


@login_required
@roles_required(UserRoles.MAIN_CASHIER, UserRoles.CEO)
@log_errors
def cash_register_view(request):
    today = timezone.localdate()
    
    # Get cashiers for the dropdowns
    cashiers = User.objects.filter(
        role__in=[UserRoles.CASHIER, UserRoles.MAIN_CASHIER],
        is_active=True
    ).order_by('first_name', 'username')
    
    if request.method == 'POST':
        date = request.POST.get('date')
        counter_type = request.POST.get('counter_type')
        amount_received = request.POST.get('amount_received')
        received_from_id = request.POST.get('received_from')
        on_duty_cashier_id = request.POST.get('on_duty_cashier')
        notes = request.POST.get('notes', '')
        
        if not date or not counter_type or not amount_received or not received_from_id or not on_duty_cashier_id:
            messages.error(request, 'All required fields must be filled.')
            return redirect('cash_counters:cash_register')
        
        try:
            received_from = User.objects.get(id=received_from_id)
            on_duty_cashier = User.objects.get(id=on_duty_cashier_id)
        except User.DoesNotExist:
            messages.error(request, 'Invalid user selected.')
            return redirect('cash_counters:cash_register')
        
        CashRegister.objects.create(
            date=date,
            counter_type=counter_type,
            amount_received=amount_received,
            received_from=received_from,
            on_duty_cashier=on_duty_cashier,
            notes=notes
        )
        
        messages.success(request, 'Cash register entry recorded successfully.')
        return redirect('cash_counters:cash_register')
    
    # Get today's entries
    today_entries = CashRegister.objects.filter(
        date=today
    ).select_related('received_from', 'on_duty_cashier').order_by('-created_at')
    
    context = {
        'counter_types': CounterTypeChoices.choices,
        'cashiers': cashiers,
        'today_entries': today_entries,
        'today': today,
    }
    return render(request, 'cash_counters/cash_register.html', context)


@login_required
@log_errors
def ticket_refund_view(request):
    today = timezone.localdate()

    if request.method == 'POST':
        date = request.POST.get('date')
        no_of_tickets = request.POST.get('no_of_tickets', 1)
        rate_per_ticket = request.POST.get('rate_per_ticket', 0)
        total_amount_refunded = request.POST.get('total_amount_refunded', 0)
        reason = request.POST.get('reason')
        remarks = request.POST.get('remarks', '')

        if not date or not no_of_tickets or not rate_per_ticket or not total_amount_refunded or not reason:
            messages.error(request, 'All required fields must be filled.')
            return redirect('cash_counters:ticket_refund')

        TicketRefund.objects.create(
            date=date,
            no_of_tickets=int(no_of_tickets),
            rate_per_ticket=rate_per_ticket,
            total_amount_refunded=total_amount_refunded,
            reason=reason,
            remarks=remarks
        )

        messages.success(request, 'Ticket refund recorded successfully.')
        return redirect('cash_counters:ticket_refund')

    today_refunds = TicketRefund.objects.filter(
        date=today
    ).order_by('-created_at')

    context = {
        'reasons': TicketRefundReasonChoices.choices,
        'today_refunds': today_refunds,
        'today': today,
    }
    return render(request, 'cash_counters/ticket_refund.html', context)
