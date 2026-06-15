"""Inventory management views."""
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model

from authentication.choices import UserRoles
from mabali_resort_management.decorators import roles_required
from .models import GeneratorLog, InventoryItem, AmbulanceLog, FuelTransactionLog, AmmoTransactionLog
from .choices import AssetCategoryChoices, StockStatusChoices, HospitalChoices, PatientTypeChoices, AmmoCaliberChoices, AmmoPaymentChoices

User = get_user_model()


@login_required
def inventory_dashboard(request: HttpResponse) -> HttpResponse:
    """Display the inventory dashboard."""
    return render(request, 'inventory/dashboard.html')


@login_required
@roles_required(UserRoles.CEO, UserRoles.ACCOUNTANT, UserRoles.HR_MANAGER)
def inventory_item_create_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category')
        stock_quantity = request.POST.get('stock_quantity', 0)
        unit = request.POST.get('unit', '')
        supplier = request.POST.get('supplier', '')
        notes = request.POST.get('notes', '')
        
        if not name or not category:
            messages.error(request, 'Name and category are required.')
            return redirect('inventory:item_create')
        
        InventoryItem.objects.create(
            name=name,
            category=category,
            stock_quantity=stock_quantity,
            unit=unit,
            supplier=supplier,
            notes=notes
        )
        
        messages.success(request, 'Inventory item created successfully.')
        return redirect('inventory:item_list')
    
    context = {
        'categories': AssetCategoryChoices.choices,
    }
    return render(request, 'inventory/item_create.html', context)


@login_required
def inventory_item_list_view(request):
    items = InventoryItem.objects.filter(is_deleted=False).order_by('-created_at')
    
    context = {
        'items': items,
    }
    return render(request, 'inventory/item_list.html', context)


@login_required
@roles_required(UserRoles.CEO, UserRoles.ACCOUNTANT, UserRoles.HR_MANAGER)
def inventory_item_delete_view(request, pk):
    try:
        item = InventoryItem.objects.get(pk=pk, is_deleted=False)
    except InventoryItem.DoesNotExist:
        messages.error(request, 'Item not found.')
        return redirect('inventory:item_list')
    
    if request.method == 'POST':
        item.is_deleted = True
        item.deleted_at = timezone.now()
        item.save(update_fields=['is_deleted', 'deleted_at'])
        messages.success(request, f'"{item.name}" deleted successfully.')
        return redirect('inventory:item_list')
    
    return redirect('inventory:item_list')


@login_required
def generator_log_view(request):
    today = timezone.now().date()
    
    # Get generators from inventory items
    generators = InventoryItem.objects.filter(
        category='generator',
        is_deleted=False
    )
    
    if request.method == 'POST':
        generator_id = request.POST.get('generator')
        run_hours = request.POST.get('run_hours')
        fuel_used_liters = request.POST.get('fuel_used_liters', 0)
        notes = request.POST.get('notes', '')
        
        if not generator_id or not run_hours:
            messages.error(request, 'All required fields must be filled.')
            return redirect('inventory:generator_log')
        
        try:
            generator = InventoryItem.objects.get(id=generator_id)
        except InventoryItem.DoesNotExist:
            messages.error(request, 'Invalid generator selected.')
            return redirect('inventory:generator_log')
        
        GeneratorLog.objects.create(
            created_by=request.user,
            generator=generator,
            run_hours=run_hours,
            fuel_used_liters=fuel_used_liters,
            notes=notes
        )
        
        messages.success(request, 'Generator log recorded successfully.')
        return redirect('inventory:generator_log')
    
    # Get today's logs
    today_logs = GeneratorLog.objects.filter(
        created_at__date=today
    ).select_related('generator', 'created_by').order_by('-created_at')
    
    context = {
        'generators': generators,
        'today_logs': today_logs,
    }
    return render(request, 'inventory/generator_log.html', context)


@login_required
def ambulance_log_view(request):
    today = timezone.now().date()
    
    # Get ambulances from inventory items
    ambulances = InventoryItem.objects.filter(
        category='ambulance',
        is_deleted=False
    )
    
    # Get drivers (users with relevant roles)
    drivers = User.objects.filter(
        is_active=True
    ).order_by('first_name', 'username')
    
    if request.method == 'POST':
        date = request.POST.get('date')
        patient_name = request.POST.get('patient_name')
        patient_type = request.POST.get('patient_type')
        ambulance_id = request.POST.get('ambulance')
        start_reading_km = request.POST.get('start_reading_km')
        end_reading_km = request.POST.get('end_reading_km')
        medical_expense = request.POST.get('medical_expense', 0)
        hospital = request.POST.get('hospital')
        driver_id = request.POST.get('driver')
        notes = request.POST.get('notes', '')
        
        if not date or not patient_name or not patient_type or not ambulance_id or not start_reading_km or not end_reading_km or not hospital or not driver_id:
            messages.error(request, 'All required fields must be filled.')
            return redirect('inventory:ambulance_log')
        
        try:
            ambulance = InventoryItem.objects.get(id=ambulance_id)
            driver = User.objects.get(id=driver_id)
        except (InventoryItem.DoesNotExist, User.DoesNotExist):
            messages.error(request, 'Invalid selection.')
            return redirect('inventory:ambulance_log')
        
        AmbulanceLog.objects.create(
            date=date,
            patient_name=patient_name,
            patient_type=patient_type,
            ambulance=ambulance,
            start_reading_km=start_reading_km,
            end_reading_km=end_reading_km,
            medical_expense=medical_expense,
            hospital=hospital,
            driver=driver,
            notes=notes
        )
        
        messages.success(request, 'Ambulance log recorded successfully.')
        return redirect('inventory:ambulance_log')
    
    # Get today's logs
    today_logs = AmbulanceLog.objects.filter(
        date=today
    ).select_related('ambulance', 'driver').order_by('-created_at')
    
    context = {
        'ambulances': ambulances,
        'drivers': drivers,
        'hospitals': HospitalChoices.choices,
        'patient_types': PatientTypeChoices.choices,
        'today_logs': today_logs,
        'today': today,
    }
    return render(request, 'inventory/ambulance_log.html', context)


@login_required
def fuel_entry_view(request):
    today = timezone.now().date()
    
    fuel_items = InventoryItem.objects.filter(
        category='fuel',
        is_deleted=False
    )
    
    vehicle_items = InventoryItem.objects.filter(
        category__in=['jetski', 'boat', 'speedboat', 'parasail', 'vehicle', 'generator', 'ambulance'],
        is_deleted=False
    )
    
    if request.method == 'POST':
        date = request.POST.get('date')
        transaction_status = request.POST.get('transaction_status')
        quantity = request.POST.get('quantity')
        amount = request.POST.get('amount', 0)
        issued_to_id = request.POST.get('issued_to', '')
        inventory_item_id = request.POST.get('inventory_item', '')
        notes = request.POST.get('notes', '')
        
        if not date or not transaction_status or not quantity:
            messages.error(request, 'All required fields must be filled.')
            return redirect('inventory:fuel_entry')
        
        inventory_item = None
        if inventory_item_id:
            try:
                inventory_item = InventoryItem.objects.get(id=inventory_item_id)
            except InventoryItem.DoesNotExist:
                pass
        
        issued_to = None
        if issued_to_id:
            try:
                issued_to = InventoryItem.objects.get(id=issued_to_id)
            except InventoryItem.DoesNotExist:
                pass
        
        FuelTransactionLog.objects.create(
            date=date,
            created_by=request.user,
            inventory_item=inventory_item,
            transaction_status=transaction_status,
            quantity=quantity,
            amount=amount,
            issued_to=issued_to,
            notes=notes
        )
        
        messages.success(request, 'Fuel entry recorded successfully.')
        return redirect('inventory:fuel_entry')
    
    today_entries = FuelTransactionLog.objects.filter(
        date=today
    ).select_related('inventory_item', 'created_by', 'issued_to').order_by('-created_at')
    
    context = {
        'fuel_items': fuel_items,
        'vehicle_items': vehicle_items,
        'stock_statuses': StockStatusChoices.choices,
        'today_entries': today_entries,
        'today': today,
    }
    return render(request, 'inventory/fuel_entry.html', context)


@login_required
def ammo_entry_view(request):
    today = timezone.now().date()
    
    # Get ammo items from inventory
    ammo_items = InventoryItem.objects.filter(
        category='ammo',
        is_deleted=False
    )
    
    if request.method == 'POST':
        date = request.POST.get('date')
        bullet_type = request.POST.get('bullet_type')
        transaction_status = request.POST.get('transaction_status')
        bullet_quantity = request.POST.get('bullet_quantity')
        payment = request.POST.get('payment')
        free_bullet_reason = request.POST.get('free_bullet_reason', '')
        inventory_item_id = request.POST.get('inventory_item', '')
        
        if not date or not bullet_type or not transaction_status or not bullet_quantity or not payment:
            messages.error(request, 'All required fields must be filled.')
            return redirect('inventory:ammo_entry')
        
        inventory_item = None
        if inventory_item_id:
            try:
                inventory_item = InventoryItem.objects.get(id=inventory_item_id)
            except InventoryItem.DoesNotExist:
                pass
        
        AmmoTransactionLog.objects.create(
            date=date,
            created_by=request.user,
            inventory_item=inventory_item,
            bullet_type=bullet_type,
            transaction_status=transaction_status,
            bullet_quantity=bullet_quantity,
            payment=payment,
            free_bullet_reason=free_bullet_reason if free_bullet_reason else None
        )
        
        messages.success(request, 'Ammo entry recorded successfully.')
        return redirect('inventory:ammo_entry')
    
    # Get today's entries
    today_entries = AmmoTransactionLog.objects.filter(
        date=today
    ).select_related('inventory_item', 'created_by').order_by('-created_at')
    
    context = {
        'ammo_items': ammo_items,
        'bullet_types': AmmoCaliberChoices.choices,
        'stock_statuses': StockStatusChoices.choices,
        'payment_methods': AmmoPaymentChoices.choices,
        'today_entries': today_entries,
        'today': today,
    }
    return render(request, 'inventory/ammo_entry.html', context)