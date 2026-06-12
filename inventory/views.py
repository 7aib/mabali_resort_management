"""Inventory management views."""
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import GeneratorLog, InventoryItem, AmbulanceLog, FuelEntry, AmmoEntry
from .choices import GeneratorCapacityChoices, AssetCategoryChoices, StockStatusChoices, HospitalChoices, PatientTypeChoices, FuelTypeChoices, FuelStatusChoices, VehicleChoices, AmmoCaliberChoices, AmmoStatusChoices, AmmoPaymentChoices

User = get_user_model()


@login_required
def inventory_dashboard(request: HttpResponse) -> HttpResponse:
    """Display the inventory dashboard."""
    return render(request, 'inventory/dashboard.html')


@login_required
def inventory_item_create_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category')
        status = request.POST.get('status', StockStatusChoices.REQUIRED)
        quantity = request.POST.get('quantity', 0)
        unit = request.POST.get('unit', 'unit')
        supplier = request.POST.get('supplier', '')
        notes = request.POST.get('notes', '')
        
        if not name or not category:
            messages.error(request, 'Name and category are required.')
            return redirect('inventory:item_create')
        
        InventoryItem.objects.create(
            name=name,
            category=category,
            status=status,
            quantity=quantity,
            unit=unit,
            supplier=supplier,
            notes=notes
        )
        
        messages.success(request, 'Inventory item created successfully.')
        return redirect('inventory:item_list')
    
    context = {
        'categories': AssetCategoryChoices.choices,
        'statuses': StockStatusChoices.choices,
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
def generator_log_view(request):
    today = timezone.now().date()
    
    # Get generators from inventory items
    generators = InventoryItem.objects.filter(
        category='generator',
        is_deleted=False
    )
    
    if request.method == 'POST':
        generator_id = request.POST.get('generator')
        capacity = request.POST.get('capacity')
        run_hours = request.POST.get('run_hours')
        fuel_used_liters = request.POST.get('fuel_used_liters', 0)
        notes = request.POST.get('notes', '')
        
        if not generator_id or not capacity or not run_hours:
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
            capacity=capacity,
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
        'generator_types': GeneratorCapacityChoices.choices,
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
    
    if request.method == 'POST':
        date = request.POST.get('date')
        fuel_type = request.POST.get('fuel_type')
        status = request.POST.get('status')
        quantity = request.POST.get('quantity')
        amount = request.POST.get('amount', 0)
        issued_to = request.POST.get('issued_to', '')
        notes = request.POST.get('notes', '')
        
        if not date or not fuel_type or not status or not quantity:
            messages.error(request, 'All required fields must be filled.')
            return redirect('inventory:fuel_entry')
        
        FuelEntry.objects.create(
            date=date,
            fuel_type=fuel_type,
            status=status,
            quantity=quantity,
            amount=amount,
            issued_to=issued_to if issued_to else None,
            notes=notes
        )
        
        messages.success(request, 'Fuel entry recorded successfully.')
        return redirect('inventory:fuel_entry')
    
    # Get today's entries
    today_entries = FuelEntry.objects.filter(
        date=today
    ).order_by('-created_at')
    
    context = {
        'fuel_types': FuelTypeChoices.choices,
        'fuel_statuses': FuelStatusChoices.choices,
        'vehicles': VehicleChoices.choices,
        'today_entries': today_entries,
        'today': today,
    }
    return render(request, 'inventory/fuel_entry.html', context)


@login_required
def ammo_entry_view(request):
    today = timezone.now().date()
    
    if request.method == 'POST':
        date = request.POST.get('date')
        bullet_type = request.POST.get('bullet_type')
        bullet_status = request.POST.get('bullet_status')
        bullet_quantity = request.POST.get('bullet_quantity')
        payment = request.POST.get('payment')
        free_bullet_reason = request.POST.get('free_bullet_reason', '')
        
        if not date or not bullet_type or not bullet_status or not bullet_quantity or not payment:
            messages.error(request, 'All required fields must be filled.')
            return redirect('inventory:ammo_entry')
        
        AmmoEntry.objects.create(
            date=date,
            bullet_type=bullet_type,
            bullet_status=bullet_status,
            bullet_quantity=bullet_quantity,
            payment=payment,
            free_bullet_reason=free_bullet_reason if free_bullet_reason else None
        )
        
        messages.success(request, 'Ammo entry recorded successfully.')
        return redirect('inventory:ammo_entry')
    
    # Get today's entries
    today_entries = AmmoEntry.objects.filter(
        date=today
    ).order_by('-created_at')
    
    context = {
        'bullet_types': AmmoCaliberChoices.choices,
        'bullet_statuses': AmmoStatusChoices.choices,
        'payment_methods': AmmoPaymentChoices.choices,
        'today_entries': today_entries,
        'today': today,
    }
    return render(request, 'inventory/ammo_entry.html', context)