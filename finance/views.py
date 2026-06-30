from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import POS, TicketRefund
from .constants import POSPaymentMethodChoices, CounterTypeChoices, TicketRefundReasonChoices
from error_logs.decorators import log_errors


@login_required
@log_errors
def pos_entry_view(request):
    today = timezone.now().date()
    
    if request.method == 'POST':
        date = request.POST.get('date')
        counter_type = request.POST.get('counter_type')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        remarks = request.POST.get('remarks', '')
        
        if not date or not counter_type or not amount or not payment_method:
            messages.error(request, 'All required fields must be filled.')
            return redirect('finance:pos_entry')
        
        POS.objects.create(
            date=date,
            counter_type=counter_type,
            amount=amount,
            payment_method=payment_method,
            remarks=remarks
        )
        
        messages.success(request, 'POS entry recorded successfully.')
        return redirect('finance:pos_entry')
    
    # Get today's entries
    today_entries = POS.objects.filter(
        date=today
    ).order_by('-created_at')
    
    context = {
        'counter_types': CounterTypeChoices.choices,
        'payment_methods': POSPaymentMethodChoices.choices,
        'today_entries': today_entries,
        'today': today,
    }
    return render(request, 'finance/pos_entry.html', context)


@login_required
@log_errors
def ticket_refund_view(request):
    today = timezone.now().date()

    if request.method == 'POST':
        date = request.POST.get('date')
        no_of_tickets = request.POST.get('no_of_tickets', 1)
        rate_per_ticket = request.POST.get('rate_per_ticket', 0)
        total_amount_refunded = request.POST.get('total_amount_refunded', 0)
        reason = request.POST.get('reason')
        remarks = request.POST.get('remarks', '')

        if not date or not no_of_tickets or not rate_per_ticket or not total_amount_refunded or not reason:
            messages.error(request, 'All required fields must be filled.')
            return redirect('finance:ticket_refund')

        TicketRefund.objects.create(
            date=date,
            no_of_tickets=int(no_of_tickets),
            rate_per_ticket=rate_per_ticket,
            total_amount_refunded=total_amount_refunded,
            reason=reason,
            remarks=remarks
        )

        messages.success(request, 'Ticket refund recorded successfully.')
        return redirect('finance:ticket_refund')

    today_refunds = TicketRefund.objects.filter(
        date=today
    ).order_by('-created_at')

    context = {
        'reasons': TicketRefundReasonChoices.choices,
        'today_refunds': today_refunds,
        'today': today,
    }
    return render(request, 'finance/ticket_refund.html', context)
