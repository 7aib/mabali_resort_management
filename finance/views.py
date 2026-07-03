from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import POS
from .constants import POSPaymentMethodChoices, CounterTypeChoices
from authentication.choices import UserRoles
from mabali_resort_management.decorators import roles_required
from error_logs.decorators import log_errors


@login_required
@roles_required(UserRoles.CEO, UserRoles.ACCOUNTANT, UserRoles.HR_MANAGER, UserRoles.MAIN_CASHIER)
@log_errors
def pos_entry_view(request):
    today = timezone.localdate()
    
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
