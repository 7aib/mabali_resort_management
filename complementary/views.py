from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import FreeBilling
from .choices import BillTypeChoices, HeadChoices, BillStatusChoices, DepartmentChoices
from error_logs.decorators import log_errors


@login_required
@log_errors
def free_billing_view(request):
    today = timezone.now().date()

    if request.method == 'POST':
        date = request.POST.get('date')
        guest_name = request.POST.get('guest_name', '')
        bill_type = request.POST.get('bill_type')
        head = request.POST.get('head')
        bill_status = request.POST.get('bill_status')
        invoice_no = request.POST.get('invoice_no', '')
        department = request.POST.get('department')
        total_bill_amount = request.POST.get('total_bill_amount', 0)
        discount_amount = request.POST.get('discount_amount', 0)
        reference = request.POST.get('reference', '')
        bill_upload = request.FILES.get('bill_upload')

        if not date or not bill_type or not head or not bill_status or not department:
            messages.error(request, 'Date, Bill Type, Head, Bill Status, and Department are required.')
            return redirect('complementary:free_billing')

        FreeBilling.objects.create(
            date=date,
            guest_name=guest_name,
            bill_type=bill_type,
            head=head,
            bill_status=bill_status,
            invoice_no=invoice_no,
            department=department,
            total_bill_amount=total_bill_amount,
            discount_amount=discount_amount,
            bill_upload=bill_upload,
            reference=reference
        )

        messages.success(request, 'Free billing entry recorded successfully.')
        return redirect('complementary:free_billing')

    today_entries = FreeBilling.objects.filter(
        date=today
    ).order_by('-created_at')

    context = {
        'bill_type_choices': BillTypeChoices.choices,
        'head_choices': HeadChoices.choices,
        'bill_status_choices': BillStatusChoices.choices,
        'department_choices': DepartmentChoices.choices,
        'today_entries': today_entries,
        'today': today,
    }
    return render(request, 'complementary/free_billing.html', context)
