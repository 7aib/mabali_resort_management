from django.utils import timezone

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from authentication.choices import UserRoles
from .models import EntryCounterForm, EntryTransaction
from .constants import CitiesChoices, PaymentMethodChoices, VisitTypeChoices, GateChoices, StatusChoices
from mabali_resort_management.constants import PAID_VISIT_PRICE

User = get_user_model()

@login_required
def daily_sales_view(request):
    today = timezone.now().date()

    # Fetch last 20 entries for transaction history shown below the form 
    daily_entries = EntryCounterForm.objects.filter(created_at__date=today).select_related('customer').prefetch_related('transaction').order_by('-created_at')[:20]
    
    # Calculate total sales for the day
    # total_sales = sum(entry.transaction.amount for entry in daily_entries if hasattr(entry, 'transaction'))
    
    context = {
        'daily_entries': daily_entries,
        # 'total_sales': total_sales,
    }
    return render(request, 'cash_counters/daily_sales.html', context)


@login_required
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
