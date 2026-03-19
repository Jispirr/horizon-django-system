from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from .models import Car, Customer, SaleOrder, Inquiry, InquiryMessage, DiscountEvent, ChatSession, ChatMessage


# ─── PUBLIC VIEWS ────────────────────────────────────────────

def home(request):
    discounted_cars = Car.objects.filter(
        discount_percent__isnull=False,
        discount_percent__gt=0,
        status='available'
    ).order_by('-discount_percent')
    active_event = DiscountEvent.objects.filter(is_active=True).first()
    return render(request, 'horizon/index.html', {
        'discounted_cars': discounted_cars,
        'active_event': active_event,
    })


def catalog(request):
    cars = Car.objects.all()
    brand    = request.GET.get('brand', 'all')
    category = request.GET.get('category', 'all')
    year     = request.GET.get('year', 'all')

    if brand != 'all':
        cars = cars.filter(brand=brand)
    if category != 'all':
        cars = cars.filter(category=category)
    if year != 'all':
        try:
            y = int(year)
            if y == 2023:    cars = cars.filter(year__gte=2023)
            elif y <= 2018:  cars = cars.filter(year__lte=2018)
            else:            cars = cars.filter(year=y)
        except ValueError:
            pass

    return render(request, 'horizon/catalog.html', {
        'cars': cars,
        'brands': Car.BRAND_CHOICES,
        'categories': Car.CATEGORY_CHOICES,
        'selected_brand': brand,
        'selected_category': category,
        'selected_year': year,
    })


def vehicle_detail(request, pk):
    car     = get_object_or_404(Car, pk=pk)
    photos  = car.get_all_photos()
    related = Car.objects.filter(brand=car.brand, status='available').exclude(pk=pk)[:4]
    return render(request, 'horizon/vehicle_details.html', {
        'car': car, 'photos': photos, 'related': related,
    })


@csrf_exempt
def contact_submit(request):
    if request.method == 'POST':
        first_name = request.POST.get('fname', '').strip()
        last_name  = request.POST.get('lname', '').strip()
        email      = request.POST.get('email', '').strip()
        message    = request.POST.get('message', '').strip()

        if not first_name or not email or not message:
            return JsonResponse({'success': False, 'error': 'Please fill in your name, email, and message.'})

        try:
            inq = Inquiry.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=request.POST.get('phone', '').strip(),
                vehicle_interest=request.POST.get('interest', '').strip(),
                message=message,
                status='new',
                is_read=False,
            )
            # Save the initial message into chat as well
            InquiryMessage.objects.create(
                inquiry=inq,
                sender='customer',
                body=message,
            )
            return JsonResponse({'success': True, 'chat_token': inq.chat_token, 'ticket_no': f'#{inq.pk:05d}', 'ticket_url': f'/inquiry-chat/{inq.chat_token}/'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'Could not save your message. Please try again.'})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})



def ticket_lookup(request):
    """Public ticket lookup — visitor enters email + ticket number to access."""
    error = None
    if request.method == 'POST':
        email     = request.POST.get('email', '').strip().lower()
        ticket_no = request.POST.get('ticket_no', '').strip().lstrip('#').lstrip('0')
        try:
            pk  = int(ticket_no)
            inq = Inquiry.objects.get(pk=pk, email__iexact=email)
            return redirect('customer_chat', token=inq.chat_token)
        except (ValueError, Inquiry.DoesNotExist):
            error = 'No ticket found with that number and email address. Please check and try again.'
    return render(request, 'horizon/ticket_lookup.html', {'error': error})


def releases(request):
    brand  = request.GET.get('brand', 'all')
    status = request.GET.get('status', 'all')
    cars   = Car.objects.all().order_by('-created_at')
    if brand  != 'all': cars = cars.filter(brand=brand)
    if status != 'all': cars = cars.filter(status=status)
    counts = {
        'available': Car.objects.filter(status='available').count(),
        'reserved':  Car.objects.filter(status='reserved').count(),
        'sold':      Car.objects.filter(status='sold').count(),
        'total':     Car.objects.count(),
    }
    return render(request, 'horizon/releases.html', {
        'cars': cars,
        'brands': Car.BRAND_CHOICES,
        'selected_brand': brand,
        'selected_status': status,
        'counts': counts,
    })


# ─── PUBLIC CHAT WIDGET ─────────────────────────────────────

@csrf_exempt
def widget_chat_start(request):
    """Visitor starts a new chat ticket."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    name    = request.POST.get('name', '').strip()
    email   = request.POST.get('email', '').strip()
    subject = request.POST.get('subject', '').strip()
    message = request.POST.get('message', '').strip()
    if not name or not email or not message:
        return JsonResponse({'success': False, 'error': 'Name, email and message are required.'})
    try:
        session = ChatSession.objects.create(
            name=name, email=email,
            subject=subject or message[:80],
        )
        ChatMessage.objects.create(session=session, sender='visitor', body=message)
        return JsonResponse({
            'success':       True,
            'token':         session.token,
            'ticket_number': session.ticket_number,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Could not start chat. Please try again.'})


@csrf_exempt
def widget_chat_send(request, token):
    """Visitor sends a message in an existing chat."""
    if request.method != 'POST':
        return JsonResponse({'success': False})
    session = get_object_or_404(ChatSession, token=token)
    body    = request.POST.get('body', '').strip()
    if not body:
        return JsonResponse({'success': False})
    ChatMessage.objects.create(session=session, sender='visitor', body=body)
    if session.status == 'closed':
        session.status = 'open'
        session.save(update_fields=['status'])
    return JsonResponse({'success': True})


def widget_chat_poll(request, token):
    """Visitor polls for new admin messages."""
    session  = get_object_or_404(ChatSession, token=token)
    after_id = int(request.GET.get('after', 0))
    msgs     = session.messages.filter(pk__gt=after_id, sender='admin').values('pk', 'body', 'sent_at')
    data     = [{'pk': m['pk'], 'sender': 'admin', 'body': m['body'],
                 'sent_at': m['sent_at'].strftime('%H:%M')} for m in msgs]
    # Mark admin messages seen by visitor
    session.messages.filter(sender='admin', is_seen=False).update(is_seen=True)
    return JsonResponse({'messages': data})


# ─── INQUIRY CHAT PAGE (customer accesses via token link) ────

@csrf_exempt
def customer_chat(request, token):
    """Public ticket/chat page for a customer linked to an inquiry."""
    inq = get_object_or_404(Inquiry, chat_token=token)

    # Ticket closed — show closed page, no interaction allowed
    if inq.status == 'resolved':
        return render(request, 'horizon/customer_chat.html', {
            'inq': inq, 'msgs': inq.messages.all(), 'closed': True
        })

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            InquiryMessage.objects.create(inquiry=inq, sender='customer', body=body)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('customer_chat', token=token)

    msgs = inq.messages.all()
    msgs.filter(sender='admin', is_seen=False).update(is_seen=True)
    return render(request, 'horizon/customer_chat.html', {
        'inq': inq, 'msgs': msgs, 'closed': False
    })


def customer_chat_poll(request, token):
    """Return new messages as JSON for the customer ticket page."""
    inq = get_object_or_404(Inquiry, chat_token=token)
    # Closed tickets — return closed status
    if inq.status == 'resolved':
        return JsonResponse({'messages': [], 'closed': True})
    after_id = int(request.GET.get('after', '0') or 0)
    msgs     = inq.messages.filter(pk__gt=after_id).values('pk', 'sender', 'body', 'sent_at')
    data     = [{'pk': m['pk'], 'sender': m['sender'], 'body': m['body'],
                 'sent_at': m['sent_at'].strftime('%b %d, %H:%M')} for m in msgs]
    return JsonResponse({'messages': data, 'closed': False})



# ─── ADMIN LIVE CHATS ─────────────────────────────────────

@login_required
def admin_chats(request):
    sessions     = ChatSession.objects.all()
    unread_count = sessions.filter(is_read=False).count()
    return render(request, 'horizon/admin_chats.html', {
        'sessions':     sessions,
        'unread_count': unread_count,
    })


@login_required
def admin_chat_open(request, pk):
    """Open a chat session — mark read, return messages as JSON."""
    session = get_object_or_404(ChatSession, pk=pk)
    if not session.is_read:
        session.is_read = True
        session.save(update_fields=['is_read'])
    session.messages.filter(sender='visitor', is_seen=False).update(is_seen=True)
    msgs = list(session.messages.values('pk', 'sender', 'body', 'sent_at'))
    data = [{'pk': m['pk'], 'sender': m['sender'], 'body': m['body'],
             'sent_at': m['sent_at'].strftime('%b %d, %H:%M')} for m in msgs]
    return JsonResponse({
        'pk':            session.pk,
        'name':          session.name,
        'email':         session.email,
        'status':        session.status,
        'priority':      session.priority,
        'ticket_number': session.ticket_number,
        'subject':       session.subject,
        'token':         session.token,
        'started':       session.started_at.strftime('%b %d, %Y · %H:%M'),
        'admin_notes':   session.admin_notes,
        'messages':      data,
        'last_id':       data[-1]['pk'] if data else 0,
    })


@login_required
def admin_chat_reply(request, pk):
    """Admin replies to a chat session."""
    session = get_object_or_404(ChatSession, pk=pk)
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            msg = ChatMessage.objects.create(session=session, sender='admin', body=body)
            return JsonResponse({'success': True, 'pk': msg.pk,
                                 'sent_at': msg.sent_at.strftime('%b %d, %H:%M')})
    return JsonResponse({'success': False})


@login_required
def admin_chat_poll(request, pk):
    """Poll for new visitor messages in this session."""
    session  = get_object_or_404(ChatSession, pk=pk)
    after_id = int(request.GET.get('after', 0))
    msgs     = session.messages.filter(pk__gt=after_id, sender='visitor').values('pk', 'body', 'sent_at')
    data     = [{'pk': m['pk'], 'sender': 'visitor', 'body': m['body'],
                 'sent_at': m['sent_at'].strftime('%b %d, %H:%M')} for m in msgs]
    session.messages.filter(sender='visitor', is_seen=False).update(is_seen=True)
    unread = ChatSession.objects.filter(is_read=False).count()
    return JsonResponse({'messages': data, 'unread': unread})


@login_required
def admin_chats_unread(request):
    """Return count of unread chat sessions for sidebar badge."""
    count = ChatSession.objects.filter(is_read=False).count()
    return JsonResponse({'unread': count})


@login_required
def admin_chat_update(request, pk):
    """Update ticket status, priority, admin notes."""
    session = get_object_or_404(ChatSession, pk=pk)
    if request.method == 'POST':
        new_status   = request.POST.get('status', '').strip()
        new_priority = request.POST.get('priority', '').strip()
        new_notes    = request.POST.get('admin_notes', None)
        valid_statuses  = ['open', 'in_progress', 'resolved', 'closed']
        valid_priorities = ['low', 'normal', 'high']
        changed = []
        if new_status and new_status in valid_statuses:
            session.status = new_status
            changed.append('status')
        if new_priority and new_priority in valid_priorities:
            session.priority = new_priority
            changed.append('priority')
        if new_notes is not None:
            session.admin_notes = new_notes
            changed.append('admin_notes')
        if changed:
            session.save(update_fields=changed + ['updated_at'])
        return JsonResponse({
            'success':  True,
            'status':   session.status,
            'priority': session.priority,
        })
    return JsonResponse({'success': False})


@login_required
def admin_chat_close(request, pk):
    """Toggle close/reopen a chat session."""
    session = get_object_or_404(ChatSession, pk=pk)
    if request.method == 'POST':
        session.status = 'closed' if session.status != 'closed' else 'open'
        session.save(update_fields=['status', 'updated_at'])
        return JsonResponse({'success': True, 'status': session.status})
    return JsonResponse({'success': False})




# ─── AUTH ─────────────────────────────────────────────────────

def admin_login(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'horizon/admin_login.html')


def admin_logout(request):
    logout(request)
    return redirect('home')


# ─── ADMIN VIEWS ──────────────────────────────────────────────

@login_required
def admin_dashboard(request):
    return render(request, 'horizon/admin_dashboard.html', {
        'total_inventory':      Car.objects.count(),
        'available_cars':       Car.objects.filter(status='available').count(),
        'new_inquiries':        Inquiry.objects.filter(is_read=False).count(),
        'processing_inquiries': Inquiry.objects.filter(status='processing').count(),
        'recent_orders':        SaleOrder.objects.select_related('customer', 'car').order_by('-date')[:5],
        'recent_inquiries':     Inquiry.objects.select_related('car').order_by('-created_at')[:5],
    })


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
        for slot in ['photo', 'photo_2', 'photo_3', 'photo_4']:
            if request.FILES.get(slot):
                setattr(car, slot, request.FILES[slot])
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
        for slot in ['photo', 'photo_2', 'photo_3', 'photo_4']:
            if request.FILES.get(slot):
                setattr(car, slot, request.FILES[slot])
            if request.POST.get(f'clear_{slot}'):
                setattr(car, slot, None)
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
        car      = get_object_or_404(Car, pk=request.POST.get('car'))
        SaleOrder.objects.create(
            customer=customer, car=car,
            amount=request.POST.get('amount'),
            payment_method=request.POST.get('payment_method', 'cash'),
            status='pending',
        )
        messages.success(request, 'Sale order created!')
        return redirect('admin_orders')
    return render(request, 'horizon/admin_order_form.html', {
        'customers': Customer.objects.all(),
        'cars': Car.objects.filter(listing_type='sale', status='available'),
    })


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
    status_filter = request.GET.get('status', 'all')
    read_filter   = request.GET.get('read', 'all')
    inquiries     = Inquiry.objects.select_related('car').all().order_by('-is_read', '-created_at')
    if status_filter != 'all':
        inquiries = inquiries.filter(status=status_filter)
    if read_filter == 'unread':
        inquiries = inquiries.filter(is_read=False)
    elif read_filter == 'read':
        inquiries = inquiries.filter(is_read=True)
    counts = {
        'new':        Inquiry.objects.filter(status='new').count(),
        'processing': Inquiry.objects.filter(status='processing').count(),
        'resolved':   Inquiry.objects.filter(status='resolved').count(),
        'unread':     Inquiry.objects.filter(is_read=False).count(),
        'total':      Inquiry.objects.count(),
    }
    return render(request, 'horizon/admin_inquiries.html', {
        'inquiries': inquiries,
        'status_filter': status_filter,
        'read_filter': read_filter,
        'counts': counts,
        'cars': Car.objects.all().order_by('brand', 'model'),
    })


@login_required
def admin_inquiry_delete(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    if request.method == 'POST':
        inquiry.delete()
        messages.success(request, 'Inquiry deleted.')
    return redirect('admin_inquiries')


@login_required
def admin_inquiry_detail(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)

    # Auto mark read + auto set processing when admin opens it
    changed_fields = []
    if not inquiry.is_read:
        inquiry.is_read = True
        changed_fields.append('is_read')
    if inquiry.status == 'new':
        inquiry.status = 'processing'
        changed_fields.append('status')
    if changed_fields:
        inquiry.save(update_fields=changed_fields)

    # Mark customer messages as seen by admin
    inquiry.messages.filter(sender='customer', is_seen=False).update(is_seen=True)

    cars = Car.objects.all().order_by('brand', 'model')
    msgs = inquiry.messages.all()
    last_msg_id = msgs.last().pk if msgs.exists() else 0
    return render(request, 'horizon/admin_inquiry_detail.html', {
        'inq': inquiry,
        'cars': cars,
        'msgs': msgs,
        'last_msg_id': last_msg_id,
        'back_url': request.META.get('HTTP_REFERER', '/admin-panel/inquiries/'),
    })


@login_required
def admin_inquiry_update(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status', inquiry.status)
        inquiry.status = new_status if new_status in ['processing', 'resolved'] else inquiry.status
        inquiry.admin_notes = request.POST.get('admin_notes', inquiry.admin_notes)
        inquiry.is_read     = True
        car_id = request.POST.get('car_id', '').strip()
        if car_id and car_id.isdigit():
            inquiry.car = Car.objects.filter(pk=int(car_id)).first()
        else:
            inquiry.car = None
        inquiry.save()
        messages.success(request, f'Inquiry from {inquiry.full_name} updated.')
    return redirect('admin_inquiry_detail', pk=pk)


@login_required
def admin_inquiry_send_message(request, pk):
    """Admin sends a chat message to the customer."""
    inquiry = get_object_or_404(Inquiry, pk=pk)
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            msg = InquiryMessage.objects.create(inquiry=inquiry, sender='admin', body=body)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'pk': msg.pk,
                                     'sent_at': msg.sent_at.strftime('%b %d, %H:%M')})
    return redirect('admin_inquiry_detail', pk=pk)


@login_required
def admin_inquiry_poll(request, pk):
    """Return new messages as JSON for live polling (admin side)."""
    inquiry  = get_object_or_404(Inquiry, pk=pk)
    after_id = int(request.GET.get('after', 0))
    msgs     = inquiry.messages.filter(pk__gt=after_id).values('pk', 'sender', 'body', 'sent_at')
    data     = [{'pk': m['pk'], 'sender': m['sender'], 'body': m['body'],
                 'sent_at': m['sent_at'].strftime('%b %d, %H:%M')} for m in msgs]
    # Mark customer messages seen
    inquiry.messages.filter(sender='customer', is_seen=False).update(is_seen=True)
    return JsonResponse({'messages': data})


@login_required
def admin_inquiry_toggle_read(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    if request.method == 'POST':
        inquiry.is_read = not inquiry.is_read
        inquiry.save()
    next_url = request.POST.get('next', '')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect('admin_inquiries')




@login_required
def admin_discounts(request):
    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action in ('apply', 'remove', 'edit', '') and request.POST.get('car_id'):
            car = get_object_or_404(Car, pk=request.POST.get('car_id'))
            if action == 'remove':
                car.discount_percent = None
                car.discount_label   = ''
            else:
                car.discount_percent = request.POST.get('discount_percent') or None
                car.discount_label   = request.POST.get('discount_label', '')
            car.save()
            messages.success(request, f'Discount updated for {car}.')
        elif action == 'event_create':
            DiscountEvent.objects.create(
                name=request.POST.get('event_name', 'New Event'),
                banner_title=request.POST.get('banner_title', ''),
                banner_subtitle=request.POST.get('banner_subtitle', ''),
                is_active=False,
            )
            messages.success(request, 'Event created.')
        elif action == 'event_toggle':
            event = get_object_or_404(DiscountEvent, pk=request.POST.get('event_id'))
            event.is_active = not event.is_active
            event.save()
            messages.success(request, f'"{event.name}" {"activated" if event.is_active else "deactivated"}.')
        elif action == 'event_delete':
            event = get_object_or_404(DiscountEvent, pk=request.POST.get('event_id'))
            name  = event.name; event.delete()
            messages.success(request, f'Event "{name}" deleted.')
        elif action == 'event_edit':
            event = get_object_or_404(DiscountEvent, pk=request.POST.get('event_id'))
            event.name            = request.POST.get('event_name', event.name)
            event.banner_title    = request.POST.get('banner_title', event.banner_title)
            event.banner_subtitle = request.POST.get('banner_subtitle', event.banner_subtitle)
            event.save()
            messages.success(request, f'Event "{event.name}" updated.')
        return redirect('admin_discounts')

    cars      = Car.objects.all().order_by('brand', 'model')
    discounted = Car.objects.filter(discount_percent__isnull=False, discount_percent__gt=0).order_by('brand', 'model')
    events    = DiscountEvent.objects.all()
    return render(request, 'horizon/admin_discounts.html', {
        'cars': cars, 'discounted': discounted, 'events': events,
    })


@login_required
def admin_settings(request):
    if request.method == 'POST':
        messages.success(request, 'Settings saved!')
    return render(request, 'horizon/admin_settings.html')
