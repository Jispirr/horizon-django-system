from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from .models import Car, Customer, SaleOrder, Inquiry


# ─── PUBLIC VIEWS ───────────────────────────────────────────

def home(request):
    discounted_cars = Car.objects.filter(
        discount_percent__isnull=False,
        discount_percent__gt=0,
        status='available'
    ).order_by('-discount_percent')
    return render(request, 'horizon/index.html', {'discounted_cars': discounted_cars})


def catalog(request):
    cars = Car.objects.all()
    brand = request.GET.get('brand', 'all')
    category = request.GET.get('category', 'all')
    year = request.GET.get('year', 'all')

    if brand != 'all':
        cars = cars.filter(brand=brand)
    if category != 'all':
        cars = cars.filter(category=category)
    if year != 'all':
        try:
            year_int = int(year)
            if year_int == 2023:
                cars = cars.filter(year__gte=2023)
            elif year_int <= 2018:
                cars = cars.filter(year__lte=2018)
            else:
                cars = cars.filter(year=year_int)
        except ValueError:
            pass

    brands = Car.BRAND_CHOICES
    categories = Car.CATEGORY_CHOICES
    context = {
        'cars': cars,
        'brands': brands,
        'categories': categories,
        'selected_brand': brand,
        'selected_category': category,
        'selected_year': year,
    }
    return render(request, 'horizon/catalog.html', context)


def vehicle_detail(request, pk):
    car = get_object_or_404(Car, pk=pk)
    photos = car.get_all_photos()
    related = Car.objects.filter(brand=car.brand, status='available').exclude(pk=pk)[:4]
    return render(request, 'horizon/vehicle_details.html', {
        'car': car,
        'photos': photos,
        'related': related,
    })


def contact_submit(request):
    if request.method == 'POST':
        Inquiry.objects.create(
            first_name=request.POST.get('fname', ''),
            last_name=request.POST.get('lname', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            vehicle_interest=request.POST.get('interest', ''),
            message=request.POST.get('message', ''),
        )
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


# ─── AUTH ────────────────────────────────────────────────────

def admin_login(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'horizon/admin_login.html')


def admin_logout(request):
    logout(request)
    return redirect('home')


# ─── ADMIN VIEWS ─────────────────────────────────────────────

@login_required
def admin_dashboard(request):
    context = {
        'total_inventory': Car.objects.count(),
        'new_inquiries': Inquiry.objects.filter(is_read=False).count(),
        'recent_orders': SaleOrder.objects.select_related('customer', 'car').order_by('-date')[:5],
    }
    return render(request, 'horizon/admin_dashboard.html', context)


@login_required
def admin_cars(request):
    listing = request.GET.get('listing', 'all')
    cars = Car.objects.all().order_by('-created_at')
    if listing == 'sale':
        cars = cars.filter(listing_type='sale')
    return render(request, 'horizon/admin_cars.html', {'cars': cars, 'listing': listing})


@login_required
def admin_car_add(request):
    if request.method == 'POST':
        car = Car.objects.create(
            brand=request.POST.get('brand'),
            model=request.POST.get('model'),
            year=request.POST.get('year'),
            category=request.POST.get('category'),
            listing_type=request.POST.get('listing_type', 'sale'),
            sale_price=request.POST.get('sale_price') or None,
            mileage=request.POST.get('mileage') or None,
            transmission=request.POST.get('transmission', 'automatic'),
            fuel_type=request.POST.get('fuel_type', 'gasoline'),
            color=request.POST.get('color', ''),
            plate_number=request.POST.get('plate_number', ''),
            description=request.POST.get('description', ''),
            discount_percent=request.POST.get('discount_percent') or None,
            discount_label=request.POST.get('discount_label', ''),
        )
        if request.FILES.get('photo'):
            car.photo = request.FILES['photo']
        if request.FILES.get('photo_2'):
            car.photo_2 = request.FILES['photo_2']
        if request.FILES.get('photo_3'):
            car.photo_3 = request.FILES['photo_3']
        if request.FILES.get('photo_4'):
            car.photo_4 = request.FILES['photo_4']
        car.save()
        messages.success(request, 'Car added to inventory!')
        return redirect('admin_cars')
    photo_slots = [
        ('photo',   None, 'Main Photo'),
        ('photo_2', None, '2nd Photo (optional)'),
        ('photo_3', None, '3rd Photo (optional)'),
        ('photo_4', None, '4th Photo (optional)'),
    ]
    return render(request, 'horizon/admin_car_form.html', {'action': 'Add', 'car': None, 'photo_slots': photo_slots})


@login_required
def admin_car_edit(request, pk):
    car = get_object_or_404(Car, pk=pk)
    if request.method == 'POST':
        car.brand        = request.POST.get('brand')
        car.model        = request.POST.get('model')
        car.year         = request.POST.get('year')
        car.category     = request.POST.get('category')
        car.listing_type = request.POST.get('listing_type', 'sale')
        car.sale_price   = request.POST.get('sale_price') or None
        car.status       = request.POST.get('status', 'available')
        car.mileage      = request.POST.get('mileage') or None
        car.transmission = request.POST.get('transmission', 'automatic')
        car.fuel_type    = request.POST.get('fuel_type', 'gasoline')
        car.color        = request.POST.get('color', '')
        car.plate_number = request.POST.get('plate_number', '')
        car.description  = request.POST.get('description', '')
        car.discount_percent = request.POST.get('discount_percent') or None
        car.discount_label   = request.POST.get('discount_label', '')
        # Only replace photo if a new file was uploaded
        if request.FILES.get('photo'):
            car.photo = request.FILES['photo']
        if request.FILES.get('photo_2'):
            car.photo_2 = request.FILES['photo_2']
        if request.FILES.get('photo_3'):
            car.photo_3 = request.FILES['photo_3']
        if request.FILES.get('photo_4'):
            car.photo_4 = request.FILES['photo_4']
        # Allow clearing individual photos
        if request.POST.get('clear_photo'):
            car.photo = None
        if request.POST.get('clear_photo_2'):
            car.photo_2 = None
        if request.POST.get('clear_photo_3'):
            car.photo_3 = None
        if request.POST.get('clear_photo_4'):
            car.photo_4 = None
        car.save()
        messages.success(request, 'Car updated successfully!')
        return redirect('admin_cars')
    photo_slots = [
        ('photo',   car.photo,   'Main Photo'),
        ('photo_2', car.photo_2, '2nd Photo (optional)'),
        ('photo_3', car.photo_3, '3rd Photo (optional)'),
        ('photo_4', car.photo_4, '4th Photo (optional)'),
    ]
    return render(request, 'horizon/admin_car_form.html', {'action': 'Edit', 'car': car, 'photo_slots': photo_slots})


@login_required
def admin_car_delete(request, pk):
    car = get_object_or_404(Car, pk=pk)
    if request.method == 'POST':
        car.delete()
        messages.success(request, 'Car removed from inventory.')
    return redirect('admin_cars')


@login_required
def admin_orders(request):
    orders = SaleOrder.objects.select_related('customer', 'car').order_by('-date')
    return render(request, 'horizon/admin_orders.html', {'orders': orders})


@login_required
def admin_order_add(request):
    if request.method == 'POST':
        customer = get_object_or_404(Customer, pk=request.POST.get('customer'))
        car = get_object_or_404(Car, pk=request.POST.get('car'))
        SaleOrder.objects.create(
            customer=customer,
            car=car,
            amount=request.POST.get('amount'),
            payment_method=request.POST.get('payment_method', 'cash'),
            status='pending',
        )
        messages.success(request, 'Sale order created!')
        return redirect('admin_orders')
    customers = Customer.objects.all()
    cars = Car.objects.filter(listing_type='sale', status='available')
    return render(request, 'horizon/admin_order_form.html', {'customers': customers, 'cars': cars})


@login_required
def admin_order_edit(request, pk):
    order = get_object_or_404(SaleOrder, pk=pk)
    if request.method == 'POST':
        order.status         = request.POST.get('status', order.status)
        order.payment_method = request.POST.get('payment_method', order.payment_method)
        order.amount         = request.POST.get('amount', order.amount)
        order.save()
        messages.success(request, 'Order updated!')
        return redirect('admin_orders')
    return render(request, 'horizon/admin_order_edit.html', {'order': order})


@login_required
def admin_customers(request):
    customers = Customer.objects.all().order_by('-created_at')
    return render(request, 'horizon/admin_customers.html', {'customers': customers})


@login_required
def admin_customer_add(request):
    if request.method == 'POST':
        Customer.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone', ''),
            customer_type=request.POST.get('customer_type', 'buyer'),
        )
        messages.success(request, 'Customer added!')
        return redirect('admin_customers')
    return render(request, 'horizon/admin_customer_form.html')


@login_required
def admin_inquiries(request):
    inquiries = Inquiry.objects.all().order_by('-created_at')
    Inquiry.objects.filter(is_read=False).update(is_read=True)
    return render(request, 'horizon/admin_inquiries.html', {'inquiries': inquiries})


@login_required
def admin_inquiry_delete(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    if request.method == 'POST':
        inquiry.delete()
        messages.success(request, 'Inquiry deleted.')
    return redirect('admin_inquiries')


@login_required
def admin_discounts(request):
    if request.method == 'POST':
        car_id = request.POST.get('car_id')
        car = get_object_or_404(Car, pk=car_id)
        action = request.POST.get('action')
        if action == 'remove':
            car.discount_percent = None
            car.discount_label   = ''
            car.save()
            messages.success(request, f'Discount removed from {car}.')
        else:
            car.discount_percent = request.POST.get('discount_percent') or None
            car.discount_label   = request.POST.get('discount_label', '')
            car.save()
            messages.success(request, f'Discount updated for {car}.')
        return redirect('admin_discounts')

    cars      = Car.objects.filter(status='available').order_by('brand', 'model')
    discounted = cars.filter(discount_percent__isnull=False, discount_percent__gt=0)
    return render(request, 'horizon/admin_discounts.html', {
        'cars': cars,
        'discounted': discounted,
    })


@login_required
def admin_settings(request):
    if request.method == 'POST':
        messages.success(request, 'Settings saved!')
    return render(request, 'horizon/admin_settings.html')
