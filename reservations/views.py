"""Reservations views."""
from decimal import Decimal

from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils import timezone

from authentication.choices import UserRoles
from mabali_resort_management.decorators import roles_required
from error_logs.decorators import log_errors
from .models import Room, Reservation
from .choices import (
    PaymentMethodChoices, PaymentTypeChoices, ReservationStatusChoices, BankChoices,
)

User = get_user_model()


def _get_customer_by_phone(phone: str):
    """Return existing User matching phone, or None."""
    if not phone:
        return None
    return User.objects.filter(phone_number=phone, is_deleted=False).first()


def _get_or_create_customer(phone: str, name: str):
    """Return existing user by phone, or create a new User with CUSTOMER role."""
    user = _get_customer_by_phone(phone)
    if user:
        return user
    username = phone
    counter = 1
    while User.objects.filter(username=username).exists():
        username = '%s_%d' % (phone, counter)
        counter += 1
    return User.objects.create(
        username=username,
        first_name=name,
        phone_number=phone,
        role=UserRoles.CUSTOMER,
    )


@login_required
@roles_required(UserRoles.CEO, UserRoles.ACCOUNTANT, UserRoles.MAIN_CASHIER, UserRoles.CASHIER, UserRoles.HR_MANAGER)
@log_errors
def reservation_create_view(request: HttpRequest) -> HttpResponse:
    rooms = Room.objects.filter(is_deleted=False, is_active=True).order_by('name')

    if request.method == 'POST':
        guest_name = request.POST.get('guest_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        no_of_adults = request.POST.get('no_of_adults', 1)
        no_of_kids = request.POST.get('no_of_kids', 0)
        room_id = request.POST.get('room')
        check_in_date = request.POST.get('check_in_date')
        check_out_date = request.POST.get('check_out_date')
        nights = request.POST.get('nights', 1)
        rate_per_night = request.POST.get('rate_per_night', 0)
        advance_amount = request.POST.get('advance_amount', 0)
        advance_date = request.POST.get('advance_date') or None
        advance_bank = request.POST.get('advance_bank', '')
        discount = request.POST.get('discount', 0)
        amount_received = request.POST.get('amount_received', 0)
        payment_type = request.POST.get('payment_type', PaymentTypeChoices.ADVANCE)
        payment_method = request.POST.get('payment_method', '')
        remarks = request.POST.get('remarks', '')

        if not guest_name or not phone_number or not room_id or not check_in_date or not check_out_date:
            messages.error(request, 'Guest name, phone, room, and dates are required.')
            return redirect('reservations:reservation_create')

        try:
            room = Room.objects.get(pk=room_id, is_deleted=False)
        except Room.DoesNotExist:
            messages.error(request, 'Invalid room selected.')
            return redirect('reservations:reservation_create')

        customer = _get_or_create_customer(phone_number, guest_name)

        try:
            reservation = Reservation.objects.create(
                customer=customer,
                guest_name=guest_name,
                phone_number=phone_number,
                no_of_adults=int(no_of_adults),
                no_of_kids=int(no_of_kids),
                room=room,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                nights=int(nights),
                rate_per_night=Decimal(str(rate_per_night)),
                advance_amount=Decimal(str(advance_amount)),
                advance_date=advance_date,
                advance_bank=advance_bank,
                discount=Decimal(str(discount)),
                amount_received=Decimal(str(amount_received)),
                payment_type=payment_type,
                payment_method=payment_method,
                remarks=remarks,
                created_by=request.user,
            )
            messages.success(request, 'Reservation created for %s.' % guest_name)
            return redirect('reservations:reservation_list')
        except Exception as e:
            messages.error(request, 'Error creating reservation: %s' % str(e))
            return redirect('reservations:reservation_create')

    context = {
        'rooms': rooms,
        'payment_methods': PaymentMethodChoices.choices,
        'payment_types': PaymentTypeChoices.choices,
        'banks': BankChoices.choices,
        'statuses': ReservationStatusChoices.choices,
        'today': timezone.now().date(),
    }
    return render(request, 'reservations/reservation_create.html', context)


@login_required
@roles_required(UserRoles.CEO, UserRoles.ACCOUNTANT, UserRoles.MAIN_CASHIER, UserRoles.CASHIER, UserRoles.HR_MANAGER)
@log_errors
def reservation_list_view(request: HttpRequest) -> HttpResponse:
    reservations = Reservation.objects.select_related(
        'customer', 'room', 'created_by'
    ).filter(is_deleted=False).order_by('-check_in_date')

    context = {
        'reservations': reservations,
        'total_count': reservations.count(),
    }
    return render(request, 'reservations/reservation_list.html', context)


@login_required
@log_errors
def customer_lookup_api(request: HttpRequest) -> HttpResponse:
    """AJAX endpoint — return customer data by phone number."""
    from django.http import JsonResponse
    phone = request.GET.get('phone', '').strip()
    if not phone:
        return JsonResponse({'found': False})
    customer = _get_customer_by_phone(phone)
    if not customer:
        return JsonResponse({'found': False})
    display_name = customer.get_full_name() or customer.first_name or customer.username
    return JsonResponse({
        'found': True,
        'name': display_name,
        'phone': customer.phone_number,
        'email': customer.email,
    })


@login_required
@log_errors
def room_status_view(request: HttpRequest) -> HttpResponse:
    """Show live status of every room."""
    today = timezone.now().date()
    rooms = Room.objects.filter(is_deleted=False, is_active=True).order_by('name')

    # Collect all active (non-cancelled, non-checked_out) reservations in one query
    active_reservations = Reservation.objects.filter(
        is_deleted=False,
        status__in=[ReservationStatusChoices.CONFIRMED, ReservationStatusChoices.CHECKED_IN],
    ).select_related('customer', 'room')

    # Build a lookup: room_id -> list of active reservations
    res_map = {}
    for res in active_reservations:
        res_map.setdefault(res.room_id, []).append(res)

    room_data = []
    for room in rooms:
        reservations = res_map.get(room.id, [])
        matched = None

        for res in reservations:
            # Occupied: today falls within stay period
            if res.check_in_date <= today < res.check_out_date:
                matched = res
                break
            # Reserved: check-in is in the future
            if res.check_in_date > today:
                if matched is None or res.check_in_date < matched.check_in_date:
                    matched = res

        if matched and matched.check_in_date <= today < matched.check_out_date:
            status = 'occupied'
            detail = 'Checking out %s' % matched.check_out_date.strftime('%b %d')
        elif matched:
            status = 'reserved'
            detail = 'Check-in %s' % matched.check_in_date.strftime('%b %d')
        else:
            status = 'available'
            detail = 'Available'

        guest = None
        if matched:
            guest = matched.guest_name or (matched.customer.get_full_name() if matched.customer else '—')

        room_data.append({
            'room': room,
            'status': status,
            'guest': guest,
            'detail': detail,
        })

    occupied_count = sum(1 for r in room_data if r['status'] == 'occupied')
    reserved_count = sum(1 for r in room_data if r['status'] == 'reserved')
    available_count = sum(1 for r in room_data if r['status'] == 'available')

    context = {
        'room_data': room_data,
        'total_rooms': len(room_data),
        'occupied_count': occupied_count,
        'reserved_count': reserved_count,
        'available_count': available_count,
        'today': today,
    }
    return render(request, 'reservations/room_status.html', context)
