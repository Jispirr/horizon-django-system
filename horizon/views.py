from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Car, Brand, Category, Customer, SaleOrder, Inquiry, InquiryReply, DiscountEvent, DiscountEventCar, ChatSession, ChatMessage, CustomerReview, DealershipSettings, TestDriveRequest, ActivityLog

import io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, Image as RLImage,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ─── PUBLIC VIEWS ────────────────────────────────────────────

def home(request):
    discounted_cars = Car.objects.filter(
        discount_percent__isnull=False,
        discount_percent__gt=0,
        status='available'
    ).order_by('-discount_percent')
    active_event = DiscountEvent.objects.filter(is_active=True).first()

    # Trending: most-viewed available cars
    trending_cars = Car.objects.filter(status='available').order_by('-view_count')[:6]

    # Recently Viewed: fetch from session, preserve order
    recently_viewed_ids = request.session.get('recently_viewed', [])
    if recently_viewed_ids:
        from django.db.models import Case, When, IntegerField
        preserved_order = Case(
            *[When(pk=pk, then=pos) for pos, pk in enumerate(recently_viewed_ids)],
            output_field=IntegerField()
        )
        recently_viewed_cars = (
            Car.objects.filter(pk__in=recently_viewed_ids)
            .order_by(preserved_order)[:6]
        )
    else:
        recently_viewed_cars = []

    # Personalized recommendations: based on categories/brands from search history
    search_history = request.session.get('search_history', [])
    recommended_cars = []
    if search_history:
        from django.db.models import Q
        rec_q = Q()
        for term in search_history[-5:]:  # last 5 unique search terms
            rec_q |= Q(brand__name__icontains=term)
            rec_q |= Q(category__name__icontains=term)
            rec_q |= Q(model__icontains=term)
        recommended_cars = (
            Car.objects.filter(status='available')
            .filter(rec_q)
            .exclude(pk__in=recently_viewed_ids)
            .order_by('-view_count')
            .distinct()[:6]
        )

    return render(request, 'horizon/index.html', {
        'discounted_cars': discounted_cars,
        'active_event': active_event,
        'trending_cars': trending_cars,
        'recently_viewed_cars': recently_viewed_cars,
        'recommended_cars': recommended_cars,
        'has_history': bool(recently_viewed_ids or search_history),
    })


def catalog(request):
    from django.core.paginator import Paginator
    cars = Car.objects.all()
    brand_slug    = request.GET.get('brand', 'all')
    category_slug = request.GET.get('category', 'all')
    year          = request.GET.get('year', 'all')
    min_price     = request.GET.get('min_price', '').strip()
    max_price     = request.GET.get('max_price', '').strip()
    transmission  = request.GET.get('transmission', 'all')
    fuel_type     = request.GET.get('fuel_type', 'all')
    status        = request.GET.get('status', 'all')

    if brand_slug != 'all':
        cars = cars.filter(brand__slug=brand_slug)
    if category_slug != 'all':
        cars = cars.filter(category__slug=category_slug)
    if year != 'all':
        try:
            y = int(year)
            if y == 2023:    cars = cars.filter(year__gte=2023)
            elif y <= 2018:  cars = cars.filter(year__lte=2018)
            else:            cars = cars.filter(year=y)
        except ValueError:
            pass
    if min_price:
        try:
            cars = cars.filter(sale_price__gte=float(min_price))
        except ValueError:
            min_price = ''
    if max_price:
        try:
            cars = cars.filter(sale_price__lte=float(max_price))
        except ValueError:
            max_price = ''
    if transmission != 'all':
        cars = cars.filter(transmission=transmission)
    if fuel_type != 'all':
        cars = cars.filter(fuel_type=fuel_type)
    if status != 'all':
        cars = cars.filter(status=status)

    total = cars.count()
    paginator = Paginator(cars, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'horizon/catalog.html', {
        'cars': page_obj,
        'page_obj': page_obj,
        'total': total,
        'brands': Brand.objects.all(),
        'categories': Category.objects.all(),
        'selected_brand': brand_slug,
        'selected_category': category_slug,
        'selected_year': year,
        'min_price': min_price,
        'max_price': max_price,
        'selected_transmission': transmission,
        'selected_fuel_type': fuel_type,
        'selected_status': status,
    })


def search_autocomplete(request):
    q = request.GET.get('q', '').strip()
    results = []
    if len(q) >= 2:
        cars = Car.objects.filter(
            Q(brand__name__icontains=q)   |
            Q(model__icontains=q)          |
            Q(color__icontains=q)          |
            Q(category__name__icontains=q) |
            Q(fuel_type__icontains=q)      |
            Q(transmission__icontains=q)
        ).select_related('brand', 'category').distinct().order_by('status', 'brand__name', 'model')[:8]

        for car in cars:
            results.append({
                'pk':       car.pk,
                'brand':    car.brand.name if car.brand else '',
                'model':    car.model,
                'year':     car.year,
                'category': car.category.name if car.category else '',
                'status':   car.status,
                'price':    str(car.discounted_price or car.sale_price or ''),
                'img':      car.get_display_image() or '',
                'url':      f'/catalog/{car.pk}/',
            })
    return JsonResponse({'results': results})


def search(request):
    query = request.GET.get('q', '').strip()
    cars = Car.objects.none()
    total = 0

    if query:
        cars = Car.objects.filter(
            Q(brand__name__icontains=query)   |
            Q(model__icontains=query)          |
            Q(color__icontains=query)          |
            Q(description__icontains=query)    |
            Q(category__name__icontains=query) |
            Q(fuel_type__icontains=query)      |
            Q(transmission__icontains=query)   |
            Q(plate_number__icontains=query)
        ).distinct().order_by('-created_at')

        # Allow bare year queries like "2022"
        try:
            year_int = int(query)
            cars = (cars | Car.objects.filter(year=year_int)).distinct()
        except ValueError:
            pass

        total = cars.count()

        # Track search history for personalized recommendations (max 20 unique terms)
        search_history = request.session.get('search_history', [])
        if query not in search_history:
            search_history.insert(0, query)
            request.session['search_history'] = search_history[:20]
            request.session.modified = True

    return render(request, 'horizon/search.html', {
        'query': query,
        'cars':  cars,
        'total': total,
        'suggest_terms': ['BMW', 'Toyota', 'Lexus', 'Sedan', 'SUV', 'Electric', 'Diesel', '2022', 'White', 'Porsche'],
    })


def vehicle_detail(request, pk):
    from django.db.models import Q, F
    car     = get_object_or_404(Car, pk=pk)

    # Increment view count (atomic, no race conditions)
    Car.objects.filter(pk=pk).update(view_count=F('view_count') + 1)
    car.refresh_from_db(fields=['view_count'])

    # Track recently viewed in session (most recent first, max 12)
    recently_viewed = request.session.get('recently_viewed', [])
    if pk in recently_viewed:
        recently_viewed.remove(pk)
    recently_viewed.insert(0, pk)
    request.session['recently_viewed'] = recently_viewed[:12]
    request.session.modified = True
    photos  = car.get_all_photos()
    related = Car.objects.filter(brand=car.brand, status='available').exclude(pk=pk)[:4]

    # Similar Cars: same category OR similar fuel type + transmission, different brand
    similar_qs = Car.objects.filter(status='available').exclude(pk=pk).exclude(brand=car.brand)

    # Build similarity filter: same category is strongest signal
    sim_filter = Q()
    if car.category:
        sim_filter |= Q(category=car.category)
    sim_filter |= Q(fuel_type=car.fuel_type, transmission=car.transmission)

    similar = similar_qs.filter(sim_filter).order_by('?')[:4]

    # Fallback: if fewer than 2, just grab any available cars of same category
    if similar.count() < 2 and car.category:
        similar = Car.objects.filter(status='available', category=car.category).exclude(pk=pk)[:4]

    return render(request, 'horizon/vehicle_details.html', {
        'car': car, 'photos': photos, 'related': related, 'similar': similar,
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
            # Save initial message as a reply so thread works
            first_reply = InquiryReply.objects.create(inquiry=inq, sender='visitor', body=message)
            return JsonResponse({
                'success':    True,
                'token':      inq.reply_token,
                'inquiry_no': inq.inquiry_number,
                'name':       inq.first_name,
                'last_id':    first_reply.pk,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'Could not save your message. Please try again.'})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})



@csrf_exempt
def test_drive_request(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

    from django.core.exceptions import ValidationError
    import datetime

    first_name = request.POST.get('first_name', '').strip()
    last_name  = request.POST.get('last_name', '').strip()
    phone      = request.POST.get('phone', '').strip()
    date_str   = request.POST.get('preferred_date', '').strip()
    pref_time  = request.POST.get('preferred_time', '').strip()
    notes      = request.POST.get('notes', '').strip()
    car_pk     = request.POST.get('car_pk', '').strip()

    if not first_name:
        return JsonResponse({'success': False, 'error': 'Please enter your first name.'})
    if not phone:
        return JsonResponse({'success': False, 'error': 'Please enter your phone number.'})
    if not date_str:
        return JsonResponse({'success': False, 'error': 'Please select a preferred date.'})

    try:
        preferred_date = datetime.date.fromisoformat(date_str)
        if preferred_date <= datetime.date.today():
            return JsonResponse({'success': False, 'error': 'Please choose a future date.'})
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid date format.'})

    car = None
    if car_pk and car_pk.isdigit():
        car = Car.objects.filter(pk=int(car_pk)).first()

    try:
        td = TestDriveRequest.objects.create(
            car=car,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            preferred_date=preferred_date,
            preferred_time=pref_time,
            notes=notes,
        )
        return JsonResponse({
            'success': True,
            'ref_no':  td.ref_number,
        })
    except Exception:
        return JsonResponse({'success': False, 'error': 'Could not save your request. Please try again.'})


@csrf_exempt
def ticket_lookup(request):
    """Ticket lookup — handles both CHT- chat sessions and INQ- inquiry threads."""
    error = None
    if request.method == 'POST':
        email     = request.POST.get('email', '').strip().lower()
        ticket_no = request.POST.get('ticket_no', '').strip().lstrip('#').strip()

        if not email or not ticket_no:
            error = 'Please enter both your ticket number and email.'
        else:
            upper = ticket_no.upper()

            # ── INQ- inquiry thread lookup ──
            if upper.startswith('INQ'):
                digits_str = upper[3:].lstrip('-').lstrip('0') or '0'
                try:
                    inq_pk = int(digits_str)
                    inq = Inquiry.objects.filter(pk=inq_pk, email__iexact=email).first()
                    if inq:
                        return redirect('inquiry_thread', token=inq.reply_token)
                    else:
                        error = 'No inquiry found with that number and email. Please check and try again.'
                except ValueError:
                    error = 'Invalid ticket number format.'

            # ── CHT- chat session lookup ──
            else:
                cht_num = upper
                if not cht_num.startswith('CHT-'):
                    if cht_num.startswith('CHT'):
                        digits = cht_num[3:].lstrip('0') or '0'
                        cht_num = f'CHT-{int(digits):05d}'
                    else:
                        try:
                            cht_num = f'CHT-{int(ticket_no):05d}'
                        except ValueError:
                            cht_num = upper

                try:
                    session = ChatSession.objects.get(
                        ticket_number__iexact=cht_num,
                        email__iexact=email
                    )
                    if session.status == 'closed':
                        error = 'This ticket has been closed. Start a new chat if you need further help.'
                    else:
                        return render(request, 'horizon/ticket_found.html', {'session': session})
                except ChatSession.DoesNotExist:
                    error = 'No ticket found with that number and email. Please check and try again.'

    return render(request, 'horizon/ticket_lookup.html', {'error': error})

def inquiry_thread(request, token):
    """Visitor views their inquiry thread via the unique token link."""
    inq  = get_object_or_404(Inquiry, reply_token=token)
    msgs = inq.replies.all()
    last = msgs.last()
    return render(request, 'horizon/customer_chat.html', {
        'inq':     inq,
        'msgs':    msgs,
        'closed':  inq.status == 'resolved',
        'last_id': last.pk if last else 0,
    })


@csrf_exempt
def inquiry_reply(request, token):
    """Visitor sends a follow-up reply on their inquiry thread."""
    inq = get_object_or_404(Inquiry, reply_token=token)
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            reply = InquiryReply.objects.create(inquiry=inq, sender='visitor', body=body)
            # Re-open if resolved + mark unread so admin badge reappears
            changed = ['is_read']
            inq.is_read = False
            if inq.status == 'resolved':
                inq.status = 'processing'
                changed.append('status')
            inq.save(update_fields=changed)
            return JsonResponse({'success': True, 'pk': reply.pk, 'sent_at': reply.sent_at.strftime('%H:%M')})
    return JsonResponse({'success': False})


def inquiry_poll(request, token):
    """Visitor polls for new admin replies on their inquiry."""
    inq = get_object_or_404(Inquiry, reply_token=token)
    closed = inq.status == 'resolved'
    after_id = int(request.GET.get('after', 0))
    replies = inq.replies.filter(pk__gt=after_id).values('pk', 'sender', 'body', 'sent_at')
    data = [{'pk': r['pk'], 'sender': r['sender'], 'body': r['body'],
             'sent_at': r['sent_at'].strftime('%H:%M')} for r in replies]
    return JsonResponse({'replies': data, 'closed': closed})



def releases(request):
    brand    = request.GET.get('brand', 'all')
    status   = request.GET.get('status', 'all')
    category = request.GET.get('category', 'all')
    cars     = Car.objects.all().order_by('-created_at')
    if brand    != 'all': cars = cars.filter(brand__slug=brand)
    if status   != 'all': cars = cars.filter(status=status)
    if category != 'all': cars = cars.filter(category__slug=category)
    counts = {
        'available': Car.objects.filter(status='available').count(),
        'reserved':  Car.objects.filter(status='reserved').count(),
        'sold':      Car.objects.filter(status='sold').count(),
        'total':     Car.objects.count(),
    }
    return render(request, 'horizon/releases.html', {
        'cars': cars,
        'brands': Brand.objects.all(),
        'categories': Category.objects.all(),
        'selected_brand': brand,
        'selected_status': status,
        'selected_category': category,
        'counts': counts,
    })


# ─── CLIENT RELEASES (Customer Review) ─────────────────────

def client_releases(request):
    reviews = CustomerReview.objects.filter(is_approved=True)

    # Rating filter
    rating_filter = request.GET.get('rating', 'all')
    if rating_filter != 'all':
        try:
            reviews = reviews.filter(rating=int(rating_filter))
        except ValueError:
            pass

    # Stats
    all_reviews = CustomerReview.objects.filter(is_approved=True)
    total = all_reviews.count()
    avg_rating = 0
    if total:
        avg_rating = sum(r.rating for r in all_reviews) / total

    rating_counts = {}
    for i in range(1, 6):
        rating_counts[i] = all_reviews.filter(rating=i).count()

    cars = Car.objects.filter(status="sold").order_by('brand__name', 'model')

    return render(request, 'horizon/client_releases.html', {
        'reviews': reviews,
        'total': total,
        'avg_rating': round(avg_rating, 1),
        'rating_counts': rating_counts,
        'selected_rating': rating_filter,
        'cars': cars,
        'review_submitted': request.GET.get('submitted') == '1',
        'review_error': request.GET.get('error', ''),
    })


def submit_review(request):
    if request.method != 'POST':
        return redirect('client_releases')

    # ── Honeypot anti-bot check ──────────────────────────────
    if request.POST.get('website', '').strip():
        return redirect('client_releases')

    customer_name = request.POST.get('customer_name', '').strip()
    plate_number  = request.POST.get('plate_number', '').strip().upper().replace(' ', '')
    review_text   = request.POST.get('review_text', '').strip()
    rating_val    = request.POST.get('rating', '5').strip()
    car_id        = request.POST.get('car_id', '').strip()

    if not customer_name or not review_text or not plate_number or not car_id:
        return redirect(reverse('client_releases') + '?error=missing')

    try:
        rating_val = int(rating_val)
        if rating_val not in range(1, 6):
            rating_val = 5
    except ValueError:
        rating_val = 5

    # ── Resolve car ──────────────────────────────────────────
    car = None
    vehicle_purchased = ''
    try:
        car = Car.objects.get(pk=int(car_id))
        vehicle_purchased = str(car)
    except (Car.DoesNotExist, ValueError):
        return redirect(reverse('client_releases') + '?error=missing')

    # ── Plate number verification ────────────────────────────
    # Normalize stored plate for comparison (strip spaces, uppercase)
    car_plate = car.plate_number.upper().replace(' ', '')
    is_verified = bool(car_plate) and (car_plate == plate_number)

    if not is_verified:
        return redirect(reverse('client_releases') + '?error=notfound&car_id=' + car_id)

    CustomerReview.objects.create(
        customer_name=customer_name,
        vehicle_purchased=vehicle_purchased,
        car=car,
        rating=rating_val,
        review_text=review_text,
        is_approved=False,
        is_verified=True,
    )
    return redirect(reverse('client_releases') + '?submitted=1')


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
        # Return the pk of the first message so widget sets lastId correctly
        first_msg = session.messages.first()
        return JsonResponse({
            'success':       True,
            'token':         session.token,
            'ticket_number': session.ticket_number,
            'last_id':       first_msg.pk if first_msg else 0,
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
    if session.status == 'closed':
        return JsonResponse({'success': False, 'closed': True})
    ChatMessage.objects.create(session=session, sender='visitor', body=body)
    # Mark unread so admin badge reappears for follow-up messages
    session.is_read = False
    session.save(update_fields=['is_read', 'updated_at'])
    return JsonResponse({'success': True})


def widget_chat_poll(request, token):
    """Visitor polls for new messages — returns all senders so sent messages are confirmed."""
    session  = get_object_or_404(ChatSession, token=token)
    if session.status == 'closed':
        return JsonResponse({'messages': [], 'closed': True})
    after_id = int(request.GET.get('after', 0))
    msgs = session.messages.filter(pk__gt=after_id).values('pk', 'sender', 'body', 'sent_at')
    data = [{'pk': m['pk'], 'sender': m['sender'], 'body': m['body'],
             'sent_at': m['sent_at'].strftime('%H:%M')} for m in msgs]
    session.messages.filter(sender='admin', is_seen=False).update(is_seen=True)
    return JsonResponse({'messages': data, 'closed': False})


@csrf_exempt
def widget_chat_lookup(request):
    """Visitor looks up their existing ticket by ticket number + email.
    Handles both CHT- (ChatSession) and INQ- (Inquiry) ticket numbers."""
    if request.method != 'POST':
        return JsonResponse({'success': False})
    ticket_no = request.POST.get('ticket_no', '').strip().lstrip('#')
    email     = request.POST.get('email', '').strip().lower()
    if not ticket_no or not email:
        return JsonResponse({'success': False, 'error': 'Enter your ticket number and email.'})

    raw = ticket_no.upper().strip()

    # ── INQ- inquiry thread lookup ──
    if raw.startswith('INQ'):
        try:
            digits_str = raw[3:].lstrip('-').lstrip('0') or '0'
            inq_pk = int(digits_str)
            inq = Inquiry.objects.filter(pk=inq_pk, email__iexact=email).first()
            if not inq:
                return JsonResponse({'success': False, 'error': 'No inquiry found with that number and email.'})
            replies = list(inq.replies.values('pk', 'sender', 'body', 'sent_at'))
            data = [{'pk': r['pk'], 'sender': r['sender'], 'body': r['body'],
                     'sent_at': r['sent_at'].strftime('%H:%M')} for r in replies]
            return JsonResponse({
                'success': True,
                'type': 'inquiry',
                'token': inq.reply_token,
                'ticket_number': inq.inquiry_number,
                'name': inq.first_name,
                'closed': inq.status == 'resolved',
                'messages': data,
                'last_id': data[-1]['pk'] if data else 0,
            })
        except (ValueError, Exception):
            return JsonResponse({'success': False, 'error': 'No inquiry found. Check your ticket number and email.'})

    try:
        # Normalise ticket_no to CHT-NNNNN regardless of input format
        raw = ticket_no.upper().lstrip('#').strip()
        if raw.startswith('CHT-'):
            cht_num = raw  # already CHT-00001
        elif raw.startswith('CHT'):
            digits = raw[3:].lstrip('0') or '0'
            cht_num = f'CHT-{int(digits):05d}'
        else:
            cht_num = f'CHT-{int(raw):05d}'

        session = ChatSession.objects.filter(
            ticket_number__iexact=cht_num,
            email__iexact=email
        ).first()
        if not session:
            # fallback: try raw input as-is
            session = ChatSession.objects.filter(
                ticket_number__iexact=raw,
                email__iexact=email
            ).first()
        if session:
            if session.status == 'closed':
                return JsonResponse({'success': False, 'error': 'This ticket has been closed.'})
            msgs = list(session.messages.values('pk', 'sender', 'body', 'sent_at'))
            data = [{'pk': m['pk'], 'sender': m['sender'], 'body': m['body'],
                     'sent_at': m['sent_at'].strftime('%H:%M')} for m in msgs]
            return JsonResponse({
                'success': True, 'token': session.token,
                'ticket_number': session.ticket_number,
                'name': session.name, 'status': session.status,
                'messages': data,
                'last_id': data[-1]['pk'] if data else 0,
            })
        return JsonResponse({'success': False, 'error': 'No ticket found. Check your ticket number and email.'})
    except Exception:
        return JsonResponse({'success': False, 'error': 'No ticket found. Check your ticket number and email.'})


def widget_chat_by_token(request, token=None):
    """Return all messages for a session token — used to restore widget state."""
    if token is None:
        token = request.GET.get('token', '')
    session = get_object_or_404(ChatSession, token=token)
    if session.status == 'closed':
        return JsonResponse({'success': False, 'closed': True})
    msgs = list(session.messages.values('pk', 'sender', 'body', 'sent_at'))
    data = [{'pk': m['pk'], 'sender': m['sender'], 'body': m['body'],
             'sent_at': m['sent_at'].strftime('%H:%M')} for m in msgs]
    session.messages.filter(sender='admin', is_seen=False).update(is_seen=True)
    return JsonResponse({
        'success': True,
        'ticket_number': session.ticket_number,
        'messages': data,
        'last_id': data[-1]['pk'] if data else 0,
    })


# ─── INQUIRY CHAT PAGE (customer accesses via token link) ────



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
    """Poll for new messages in this session (all senders)."""
    session  = get_object_or_404(ChatSession, pk=pk)
    after_id = int(request.GET.get('after', 0))
    msgs     = session.messages.filter(pk__gt=after_id).values('pk', 'sender', 'body', 'sent_at')
    data     = [{'pk': m['pk'], 'sender': m['sender'], 'body': m['body'],
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
def admin_inquiries_unread(request):
    """Return count of unread inquiries for sidebar badge."""
    count = Inquiry.objects.filter(is_read=False).count()
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
    from django.db.models import Count

    # Top 8 cars by page views
    top_viewed = (
        Car.objects.filter(view_count__gt=0)
        .order_by('-view_count')[:8]
    )

    # Top 8 cars by inquiry count (proxy for "most saved/interested")
    top_inquired = (
        Car.objects.annotate(inq_count=Count('inquiries'))
        .filter(inq_count__gt=0)
        .order_by('-inq_count')[:8]
    )

    # Test drive requests per car (top 6)
    top_test_drives = (
        Car.objects.annotate(td_count=Count('test_drives'))
        .filter(td_count__gt=0)
        .order_by('-td_count')[:6]
    )

    return render(request, 'horizon/admin_dashboard.html', {
        'total_inventory':      Car.objects.count(),
        'available_cars':       Car.objects.filter(status='available').count(),
        # Inquiries = Contact Us form submissions
        'new_inquiries':        Inquiry.objects.filter(is_read=False).count(),
        'processing_inquiries': Inquiry.objects.filter(status='processing').count(),
        'recent_inquiries':     Inquiry.objects.select_related('car').order_by('-created_at')[:5],
        # Live Chats = widget chat sessions
        'unread_chats':         ChatSession.objects.filter(is_read=False).count(),
        'open_chats':           ChatSession.objects.filter(status='open').count(),
        'recent_orders':        SaleOrder.objects.select_related('customer', 'car').order_by('-date')[:5],
        'recent_activity':      ActivityLog.objects.order_by('-created_at')[:8],
        # Popularity data
        'top_viewed':           top_viewed,
        'top_inquired':         top_inquired,
        'top_test_drives':      top_test_drives,
    })


@login_required
def admin_cars(request):
    selected_status = request.GET.get('status', 'all')
    cars = Car.objects.all().order_by('-created_at')
    if selected_status != 'all':
        cars = cars.filter(status=selected_status)

    status_tabs = [
        ('all',       'All',       Car.objects.count()),
        ('available', 'Available', Car.objects.filter(status='available').count()),
        ('reserved',  'Reserved',  Car.objects.filter(status='reserved').count()),
        ('sold',      'Sold',      Car.objects.filter(status='sold').count()),
    ]
    return render(request, 'horizon/admin_cars.html', {
        'cars': cars,
        'selected_status': selected_status,
        'status_tabs': status_tabs,
    })


@login_required
def admin_car_add(request):
    if request.method == 'POST':
        # Validate required numeric fields
        try:
            year = int(request.POST.get('year', 0))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid year value.')
            return redirect('admin_car_add')

        brand_obj    = Brand.objects.filter(pk=request.POST.get('brand')).first()
        category_obj = Category.objects.filter(pk=request.POST.get('category')).first()
        car = Car(
            brand=brand_obj,
            model=request.POST.get('model', '').strip(),
            year=year,
            category=category_obj,
            listing_type=request.POST.get('listing_type', 'sale'),
            status=request.POST.get('status', 'available'),
            sale_price=request.POST.get('sale_price') or None,
            mileage=request.POST.get('mileage') or None,
            transmission=request.POST.get('transmission', 'automatic'),
            fuel_type=request.POST.get('fuel_type', 'gasoline'),
            color=request.POST.get('color', '').strip(),
            plate_number=request.POST.get('plate_number', '').strip(),
            description=request.POST.get('description', '').strip(),
            discount_percent=request.POST.get('discount_percent') or None,
            discount_label=request.POST.get('discount_label', '').strip(),
        )
        # Assign images before first save so they are stored correctly
        for slot in ['photo', 'photo_2', 'photo_3', 'photo_4']:
            f = request.FILES.get(slot)
            if f:
                setattr(car, slot, f)
        car.save()
        messages.success(request, 'Car added to inventory!')
        log_action('add', 'Cars', f'Added {car.year} {car.brand} {car.model}')
        return redirect('admin_cars')
    photo_slots = [
        ('photo',   None, 'Front View (Main Photo)'),
        ('photo_2', None, 'Rear View'),
        ('photo_3', None, 'Side View'),
        ('photo_4', None, 'Interior View'),
    ]
    return render(request, 'horizon/admin_car_form.html', {
        'action': 'Add', 'car': None, 'photo_slots': photo_slots,
        'brands': Brand.objects.all(), 'categories': Category.objects.all(),
    })


@login_required
def admin_car_edit(request, pk):
    car = get_object_or_404(Car, pk=pk)
    if request.method == 'POST':
        car.brand        = Brand.objects.filter(pk=request.POST.get('brand')).first()
        car.model        = request.POST.get('model', '').strip()
        car.year         = request.POST.get('year')
        car.category     = Category.objects.filter(pk=request.POST.get('category')).first()
        car.listing_type = request.POST.get('listing_type', 'sale')
        car.sale_price   = request.POST.get('sale_price') or None
        car.status       = request.POST.get('status', 'available')
        car.mileage      = request.POST.get('mileage') or None
        car.transmission = request.POST.get('transmission', 'automatic')
        car.fuel_type    = request.POST.get('fuel_type', 'gasoline')
        car.color        = request.POST.get('color', '').strip()
        car.plate_number = request.POST.get('plate_number', '').strip()
        car.description  = request.POST.get('description', '').strip()
        car.discount_percent = request.POST.get('discount_percent') or None
        car.discount_label   = request.POST.get('discount_label', '').strip()
        import os
        for slot in ['photo', 'photo_2', 'photo_3', 'photo_4']:
            new_file = request.FILES.get(slot)
            clear    = request.POST.get(f'clear_{slot}')
            old_field = getattr(car, slot)
            if clear:
                # Delete old file from disk
                if old_field and old_field.name:
                    try:
                        old_field.delete(save=False)
                    except Exception:
                        pass
                setattr(car, slot, None)
            elif new_file:
                # Delete old file first, then assign new one
                if old_field and old_field.name:
                    try:
                        old_field.delete(save=False)
                    except Exception:
                        pass
                setattr(car, slot, new_file)
        car.save()
        messages.success(request, 'Car updated successfully!')
        log_action('edit', 'Cars', f'Edited {car.year} {car.brand} {car.model}')
        return redirect('admin_cars')
    photo_slots = [
        ('photo',   car.photo,   'Front View (Main Photo)'),
        ('photo_2', car.photo_2, 'Rear View'),
        ('photo_3', car.photo_3, 'Side View'),
        ('photo_4', car.photo_4, 'Interior View'),
    ]
    return render(request, 'horizon/admin_car_form.html', {
        'action': 'Edit', 'car': car, 'photo_slots': photo_slots,
        'brands': Brand.objects.all(), 'categories': Category.objects.all(),
    })


@login_required
def admin_car_delete(request, pk):
    car = get_object_or_404(Car, pk=pk)
    if request.method == 'POST':
        car.delete()
        messages.success(request, 'Car removed from inventory.')
        log_action('delete', 'Cars', f'Deleted car #{pk}')
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

    cars = Car.objects.all().order_by('brand', 'model')
    return render(request, 'horizon/admin_inquiry_detail.html', {
        'inq': inquiry,
        'cars': cars,
        'back_url': request.META.get('HTTP_REFERER', '/admin-panel/inquiries/'),
    })


@login_required
def admin_inquiry_update(request, pk):
    """Update inquiry status, notes, linked car, and optionally update car status."""
    inquiry = get_object_or_404(Inquiry, pk=pk)
    if request.method == 'POST':
        action     = request.POST.get('action', '')
        new_status = request.POST.get('status', '').strip()

        # ── Quick-action buttons (Accept / Decline / Reopen) ──
        if action == 'accept':
            inquiry.status  = 'processing'
            inquiry.is_read = True
            # Optionally mark linked car as reserved
            car_status = request.POST.get('car_status', '').strip()
            if inquiry.car and car_status in ['available', 'reserved', 'sold']:
                inquiry.car.status = car_status
                inquiry.car.save(update_fields=['status'])
            inquiry.save()
            messages.success(request, f'Inquiry from {inquiry.full_name} accepted.')

        elif action == 'decline':
            inquiry.status  = 'resolved'
            inquiry.is_read = True
            inquiry.save()
            messages.success(request, f'Inquiry from {inquiry.full_name} declined.')

        elif action == 'reopen':
            inquiry.status = 'processing'
            inquiry.save()
            messages.success(request, f'Inquiry reopened.')

        elif action == 'resolve':
            inquiry.status = 'resolved'
            inquiry.save()
            messages.success(request, f'Inquiry resolved.')

        else:
            # ── Full form save ──
            if new_status in ['processing', 'resolved']:
                inquiry.status = new_status
            inquiry.admin_notes = request.POST.get('admin_notes', inquiry.admin_notes)
            inquiry.is_read     = True
            car_id = request.POST.get('car_id', '').strip()
            if car_id and car_id.isdigit():
                inquiry.car = Car.objects.filter(pk=int(car_id)).first()
            else:
                inquiry.car = None
            # Update linked car status if provided
            car_status = request.POST.get('car_status', '').strip()
            if inquiry.car and car_status in ['available', 'reserved', 'sold']:
                inquiry.car.status = car_status
                inquiry.car.save(update_fields=['status'])
            inquiry.save()
            messages.success(request, f'Inquiry from {inquiry.full_name} updated.')

    next_url = request.POST.get('next', '').strip()
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect('admin_inquiry_detail', pk=pk)


@login_required
def admin_inquiry_reply(request, pk):
    """Admin sends a reply on an inquiry thread."""
    inquiry = get_object_or_404(Inquiry, pk=pk)
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            reply = InquiryReply.objects.create(inquiry=inquiry, sender='admin', body=body)
            # Auto-set to processing if new or resolved
            if inquiry.status in ('new', 'resolved'):
                inquiry.status = 'processing'
                inquiry.save(update_fields=['status'])
            return JsonResponse({'success': True, 'pk': reply.pk,
                                 'sent_at': reply.sent_at.strftime('%b %d, %H:%M')})
    return JsonResponse({'success': False})


@login_required
def admin_inquiry_thread_poll(request, pk):
    """Admin polls for new visitor replies."""
    inquiry  = get_object_or_404(Inquiry, pk=pk)
    after_id = int(request.GET.get('after', 0))
    replies  = inquiry.replies.filter(pk__gt=after_id).values('pk', 'sender', 'body', 'sent_at')
    data     = [{'pk': r['pk'], 'sender': r['sender'], 'body': r['body'],
                 'sent_at': r['sent_at'].strftime('%b %d, %H:%M')} for r in replies]
    return JsonResponse({'replies': data})





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

        # ── Per-car quick discount (standalone, no event) ──
        if action == 'car_discount_apply':
            car_ids  = request.POST.getlist('car_ids')
            pct      = request.POST.get('discount_percent') or None
            label    = request.POST.get('discount_label', '').strip()
            updated  = 0
            for cid in car_ids:
                try:
                    car = Car.objects.get(pk=cid)
                    car.discount_percent = pct
                    car.discount_label   = label
                    car.save()
                    updated += 1
                except Car.DoesNotExist:
                    pass
            messages.success(request, f'Discount applied to {updated} vehicle(s).')

        elif action == 'car_discount_remove':
            car = get_object_or_404(Car, pk=request.POST.get('car_id'))
            car.discount_percent = None
            car.discount_label   = ''
            car.save()
            messages.success(request, f'Discount removed from {car}.')

        elif action == 'car_discount_edit':
            car = get_object_or_404(Car, pk=request.POST.get('car_id'))
            car.discount_percent = request.POST.get('discount_percent') or None
            car.discount_label   = request.POST.get('discount_label', '').strip()
            car.save()
            messages.success(request, f'Discount updated for {car}.')

        # ── Event CRUD ──
        elif action == 'event_create':
            event = DiscountEvent.objects.create(
                name=request.POST.get('event_name', 'New Event').strip(),
                description=request.POST.get('description', '').strip(),
                banner_title=request.POST.get('banner_title', '').strip(),
                banner_subtitle=request.POST.get('banner_subtitle', '').strip(),
                is_active=False,
            )
            # Attach selected cars with their discounts
            _save_event_cars(request, event)
            messages.success(request, f'Event "{event.name}" created with {event.car_count} vehicle(s).')

        elif action == 'event_edit':
            event = get_object_or_404(DiscountEvent, pk=request.POST.get('event_id'))
            event.name            = request.POST.get('event_name', event.name).strip()
            event.description     = request.POST.get('description', '').strip()
            event.banner_title    = request.POST.get('banner_title', '').strip()
            event.banner_subtitle = request.POST.get('banner_subtitle', '').strip()
            event.save()
            # Replace all car assignments
            event.event_cars.all().delete()
            _save_event_cars(request, event)
            messages.success(request, f'Event "{event.name}" updated.')

        elif action == 'event_toggle':
            event = get_object_or_404(DiscountEvent, pk=request.POST.get('event_id'))
            event.is_active = not event.is_active
            event.save()
            # When activating: push event discounts onto each car
            if event.is_active:
                for ec in event.event_cars.select_related('car'):
                    ec.car.discount_percent = ec.discount_percent
                    ec.car.discount_label   = ec.discount_label or event.name
                    ec.car.save()
            messages.success(request, f'"{event.name}" {"activated — discounts applied to cars." if event.is_active else "deactivated."}')

        elif action == 'event_delete':
            event = get_object_or_404(DiscountEvent, pk=request.POST.get('event_id'))
            name = event.name
            event.delete()
            messages.success(request, f'Event "{name}" deleted.')

        # ── Remove a single car from an event ──
        elif action == 'event_car_remove':
            ec = get_object_or_404(DiscountEventCar,
                                   event_id=request.POST.get('event_id'),
                                   car_id=request.POST.get('car_id'))
            ec.delete()
            messages.success(request, 'Vehicle removed from event.')

        return redirect('admin_discounts')

    # ── GET ──
    cars       = Car.objects.select_related('brand').order_by('brand__name', 'model')
    discounted = cars.filter(discount_percent__isnull=False, discount_percent__gt=0)
    events     = DiscountEvent.objects.prefetch_related('event_cars__car__brand').all()
    return render(request, 'horizon/admin_discounts.html', {
        'cars': cars, 'discounted': discounted, 'events': events,
    })


def _save_event_cars(request, event):
    """Parse car_X_id / car_X_pct / car_X_label fields from POST and create DiscountEventCar rows."""
    import re
    car_ids = request.POST.getlist('event_car_ids')
    for cid in car_ids:
        pct   = request.POST.get(f'event_car_{cid}_pct', '').strip()
        label = request.POST.get(f'event_car_{cid}_label', '').strip()
        if not pct:
            continue
        try:
            car = Car.objects.get(pk=cid)
            DiscountEventCar.objects.update_or_create(
                event=event, car=car,
                defaults={'discount_percent': pct, 'discount_label': label},
            )
        except (Car.DoesNotExist, Exception):
            pass


@login_required
def admin_settings(request):
    settings = DealershipSettings.get()
    if request.method == 'POST':
        settings.dealership_name = request.POST.get('dealership_name', settings.dealership_name).strip()
        settings.phone           = request.POST.get('phone',           settings.phone).strip()
        settings.email           = request.POST.get('email',           settings.email).strip()
        settings.address         = request.POST.get('address',         settings.address).strip()
        settings.weekday_hours   = request.POST.get('weekday_hours',   settings.weekday_hours).strip()
        settings.weekend_hours   = request.POST.get('weekend_hours',   settings.weekend_hours).strip()
        settings.facebook_url    = request.POST.get('facebook_url',    settings.facebook_url).strip()
        settings.instagram_url   = request.POST.get('instagram_url',   settings.instagram_url).strip()
        settings.telegram_url    = request.POST.get('telegram_url',    settings.telegram_url).strip()
        settings.tagline             = request.POST.get('tagline',             settings.tagline).strip()
        settings.brand_name          = request.POST.get('brand_name',          settings.brand_name).strip()
        settings.chat_avatar_letter  = request.POST.get('chat_avatar_letter',  settings.chat_avatar_letter).strip()[:2]
        settings.footer_tagline      = request.POST.get('footer_tagline',      settings.footer_tagline).strip()
        settings.footer_copyright    = request.POST.get('footer_copyright',    settings.footer_copyright).strip()
        settings.footer_show_nav      = 'footer_show_nav'      in request.POST
        settings.footer_show_services = 'footer_show_services' in request.POST
        settings.footer_show_contact  = 'footer_show_contact'  in request.POST
        settings.footer_show_socials  = 'footer_show_socials'  in request.POST
        settings.save()
        messages.success(request, 'Dealership settings saved successfully.')
        return redirect('admin_settings')
    return render(request, 'horizon/admin_settings.html', {'settings': settings})


# ─── PDF EXPORT ─────────────────────────────────────────────

@login_required
def export_cars_pdf(request):
    """PDF inventory: filter by status (available/reserved/sold), grouped by brand then mileage."""
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access denied.")

    status_filter = request.GET.get('status', 'available')

    STATUS_META = {
        'available': {
            'label':     'Available Units',
            'color':     colors.HexColor('#15803d'),
            'bg':        colors.HexColor('#f0fdf4'),
            'header_bg': colors.HexColor('#15803d'),
        },
        'reserved': {
            'label':     'Reserved Units',
            'color':     colors.HexColor('#92400e'),
            'bg':        colors.HexColor('#fffbeb'),
            'header_bg': colors.HexColor('#92400e'),
        },
        'sold': {
            'label':     'Sold Units',
            'color':     colors.HexColor('#374151'),
            'bg':        colors.HexColor('#f3f4f6'),
            'header_bg': colors.HexColor('#374151'),
        },
    }
    sec = STATUS_META.get(status_filter, STATUS_META['available'])

    MILEAGE_BANDS = [
        ('Low Mileage (under 30,000 km)',        lambda m: m is not None and m < 30_000),
        ('Mid Mileage (30,000 – 99,999 km)',     lambda m: m is not None and 30_000 <= m < 100_000),
        ('High Mileage (100,000 km and above)',  lambda m: m is not None and m >= 100_000),
        ('Mileage Not Specified',                lambda m: m is None),
    ]

    now = timezone.localtime(timezone.now())

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=12*mm, bottomMargin=15*mm,
    )

    # ── Styles ───────────────────────────────────────────────
    title_style = ParagraphStyle('HorizonTitle', fontName='Helvetica-Bold', fontSize=20,
                                 textColor=colors.HexColor('#111111'), spaceAfter=2, alignment=TA_LEFT)
    sub_style   = ParagraphStyle('HorizonSub', fontName='Helvetica', fontSize=9,
                                 textColor=colors.HexColor('#555555'), spaceAfter=8, alignment=TA_LEFT)
    brand_style = ParagraphStyle('BrandTitle', fontName='Helvetica-Bold', fontSize=12,
                                 textColor=colors.HexColor('#111111'), spaceAfter=3, spaceBefore=6)
    band_style  = ParagraphStyle('BandTitle', fontName='Helvetica-Bold', fontSize=9,
                                 textColor=sec['color'], spaceAfter=3, spaceBefore=4)
    empty_style = ParagraphStyle('Empty', fontName='Helvetica', fontSize=8,
                                 textColor=colors.HexColor('#aaaaaa'), spaceAfter=4)

    cell_style = ParagraphStyle('Cell', fontName='Helvetica', fontSize=8, leading=11, alignment=TA_LEFT)
    cell_bold  = ParagraphStyle('CellBold', fontName='Helvetica-Bold', fontSize=8, leading=11, alignment=TA_LEFT)

    col_widths = [8*mm, 56*mm, 22*mm, 24*mm, 18*mm, 22*mm, 26*mm, 30*mm, 22*mm, 29*mm]

    def th(text):
        return Paragraph(text, ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8,
                                              textColor=colors.white, alignment=TA_LEFT))

    def make_header():
        return [th(h) for h in ['#', 'Year / Brand / Model', 'Category', 'Transmission',
                                 'Fuel', 'Color', 'Mileage', 'Price (₱)', 'Discount', 'Plate No.']]

    def make_table(rows, sec):
        tbl = Table(rows, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1, 0),  sec['header_bg']),
            ('TEXTCOLOR',      (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',       (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',       (0, 0), (-1, 0),  8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [sec['bg'], colors.white]),
            ('GRID',           (0, 0), (-1, -1), 0.4, colors.HexColor('#cccccc')),
            ('LINEBELOW',      (0, 0), (-1, 0),  1.5, sec['color']),
            ('TOPPADDING',     (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 4),
            ('LEFTPADDING',    (0, 0), (-1, -1), 4),
            ('RIGHTPADDING',   (0, 0), (-1, -1), 4),
            ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
        ]))
        return tbl

    # ── Fetch data ───────────────────────────────────────────
    cars_qs = Car.objects.filter(status=status_filter).order_by('brand__name', 'model', 'year')
    total   = cars_qs.count()

    # Group by brand
    from itertools import groupby as _groupby
    cars_list   = list(cars_qs.select_related('brand'))
    brand_groups = {}
    for car in cars_list:
        brand_name = car.brand.name if car.brand else '— No Brand —'
        brand_groups.setdefault(brand_name, []).append(car)

    # ── Story ────────────────────────────────────────────────
    story = []

    # Document header
    story.append(Paragraph("HORIZON AUTO", title_style))
    story.append(Paragraph(
        f"Vehicle Inventory Report &nbsp;|&nbsp; {sec['label']} &nbsp;|&nbsp; "
        f"Generated: {now.strftime('%B %d, %Y  %I:%M %p')} &nbsp;|&nbsp; "
        f"Total records: {total}",
        sub_style,
    ))
    story.append(HRFlowable(width='100%', thickness=2, color=sec['color'], spaceAfter=8))

    if not cars_list:
        story.append(Spacer(1, 12*mm))
        story.append(Paragraph(f"No vehicles found for: {sec['label']}", empty_style))
    else:
        for brand_name, brand_cars in sorted(brand_groups.items()):

            # ── Brand heading ────────────────────────────────
            story.append(Paragraph(f"▌  {brand_name.upper()}", brand_style))
            story.append(HRFlowable(width='100%', thickness=1,
                                    color=colors.HexColor('#dddddd'), spaceAfter=4))

            brand_had_cars = False

            for band_label, band_fn in MILEAGE_BANDS:
                band_cars = [c for c in brand_cars if band_fn(c.mileage)]
                if not band_cars:
                    continue

                brand_had_cars = True

                # Mileage band sub-heading
                story.append(Paragraph(
                    f"  ◆  {band_label}  ({len(band_cars)} unit{'s' if len(band_cars) != 1 else ''})",
                    band_style,
                ))

                rows = [make_header()]
                for i, car in enumerate(band_cars, 1):
                    price_txt = f"{car.sale_price:,.0f}" if car.sale_price else '—'
                    disc_txt  = f"{car.discount_percent}%  {car.discount_label}" \
                                if car.discount_percent else '—'
                    mileage   = f"{car.mileage:,} km" if car.mileage else '—'

                    rows.append([
                        Paragraph(str(i), cell_style),
                        Paragraph(f"<b>{car.year} {car.get_brand_display()}</b>\n{car.model}", cell_style),
                        Paragraph(car.get_category_display(), cell_style),
                        Paragraph(car.get_transmission_display(), cell_style),
                        Paragraph(car.get_fuel_type_display(), cell_style),
                        Paragraph(car.color or '—', cell_style),
                        Paragraph(mileage, cell_style),
                        Paragraph(price_txt, cell_bold),
                        Paragraph(disc_txt, cell_style),
                        Paragraph(car.plate_number or '—', cell_style),
                    ])

                story.append(make_table(rows, sec))
                story.append(Spacer(1, 3*mm))

            if not brand_had_cars:
                story.append(Paragraph("No vehicles in this category.", empty_style))

            story.append(Spacer(1, 5*mm))

    # ── Footer ───────────────────────────────────────────────
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.grey, spaceAfter=3))
    story.append(Paragraph(
        "This document is auto-generated by the Horizon Auto admin system. "
        "Prices and availability are subject to change without prior notice.",
        ParagraphStyle('Footer', fontName='Helvetica', fontSize=7,
                       textColor=colors.grey, alignment=TA_CENTER),
    ))

    doc.build(story)
    buf.seek(0)

    filename = f"horizon_inventory_{status_filter}_{now.strftime('%Y%m%d_%H%M')}.pdf"
    response = HttpResponse(buf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response



@login_required
def admin_brands(request):
    brands = Brand.objects.all()
    categories = Category.objects.all()
    return render(request, 'horizon/admin_brands.html', {'brands': brands, 'categories': categories})


@login_required
def admin_brand_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Brand name is required.')
            return redirect('admin_brands')
        if Brand.objects.filter(name__iexact=name).exists():
            messages.error(request, f'Brand "{name}" already exists.')
            return redirect('admin_brands')
        brand = Brand(name=name)
        if request.FILES.get('logo'):
            brand.logo = request.FILES['logo']
        brand.save()
        messages.success(request, f'Brand "{name}" added.')
    return redirect('admin_brands')


@login_required
def admin_brand_edit(request, pk):
    import os
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Brand name is required.')
            return redirect('admin_brands')
        if Brand.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, f'Brand "{name}" already exists.')
            return redirect('admin_brands')
        brand.name = name
        from django.utils.text import slugify
        brand.slug = slugify(name)
        if request.FILES.get('logo'):
            if brand.logo:
                try:
                    if os.path.isfile(brand.logo.path):
                        os.remove(brand.logo.path)
                except Exception:
                    pass
            brand.logo = request.FILES['logo']
        elif request.POST.get('remove_logo') == '1' and brand.logo:
            try:
                if os.path.isfile(brand.logo.path):
                    os.remove(brand.logo.path)
            except Exception:
                pass
            brand.logo = None
        brand.save()
        messages.success(request, f'Brand updated to "{name}".')
    return redirect('admin_brands')


@login_required
def admin_brand_delete(request, pk):
    import os
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        if brand.car_set.exists():
            messages.error(request, f'Cannot delete "{brand.name}" — it is used by existing cars.')
        else:
            name = brand.name
            if brand.logo:
                try:
                    if os.path.isfile(brand.logo.path):
                        os.remove(brand.logo.path)
                except Exception:
                    pass
            brand.delete()
            messages.success(request, f'Brand "{name}" deleted.')
    return redirect('admin_brands')


# ─── CATEGORY MANAGEMENT ─────────────────────────────────────

@login_required
def admin_categories(request):
    # Redirect to brands page with categories tab active
    return redirect('/admin-panel/brands/?tab=categories')


@login_required
def admin_category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Category name is required.')
            return redirect('/admin-panel/brands/?tab=categories')
        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, f'Category "{name}" already exists.')
            return redirect('/admin-panel/brands/?tab=categories')
        cat = Category(name=name)
        if request.FILES.get('icon'):
            cat.icon = request.FILES['icon']
        cat.save()
        messages.success(request, f'Category "{name}" added.')
    return redirect('/admin-panel/brands/?tab=categories')


@login_required
def admin_category_edit(request, pk):
    import os
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Category name is required.')
            return redirect('/admin-panel/brands/?tab=categories')
        if Category.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, f'Category "{name}" already exists.')
            return redirect('/admin-panel/brands/?tab=categories')
        category.name = name
        from django.utils.text import slugify
        category.slug = slugify(name)
        if request.FILES.get('icon'):
            if category.icon:
                try:
                    if os.path.isfile(category.icon.path):
                        os.remove(category.icon.path)
                except Exception:
                    pass
            category.icon = request.FILES['icon']
        elif request.POST.get('remove_icon') == '1' and category.icon:
            try:
                if os.path.isfile(category.icon.path):
                    os.remove(category.icon.path)
            except Exception:
                pass
            category.icon = None
        category.save()
        messages.success(request, f'Category updated to "{name}".')
    return redirect('/admin-panel/brands/?tab=categories')


@login_required
def admin_test_drives(request):
    # Mark all unread requests as read when admin visits the page
    TestDriveRequest.objects.filter(is_read=False).update(is_read=True)

    status_filter = request.GET.get('status', 'all')
    qs = TestDriveRequest.objects.select_related('car')
    if status_filter in ('pending', 'confirmed', 'cancelled', 'completed'):
        qs = qs.filter(status=status_filter)
    counts = {
        'total':     TestDriveRequest.objects.count(),
        'pending':   TestDriveRequest.objects.filter(status='pending').count(),
        'confirmed': TestDriveRequest.objects.filter(status='confirmed').count(),
        'completed': TestDriveRequest.objects.filter(status='completed').count(),
        'cancelled': TestDriveRequest.objects.filter(status='cancelled').count(),
    }
    return render(request, 'horizon/admin_test_drives.html', {
        'requests': qs,
        'status_filter': status_filter,
        'counts': counts,
    })


@login_required
def admin_test_drive_update(request, pk):
    td = get_object_or_404(TestDriveRequest, pk=pk)
    if request.method == 'POST':
        new_status  = request.POST.get('status', td.status)
        admin_notes = request.POST.get('admin_notes', td.admin_notes)
        # Never allow reverting back to pending
        valid_transitions = {
            'pending':   ['confirmed', 'cancelled'],
            'confirmed': ['completed', 'cancelled'],
            'completed': [],
            'cancelled': [],
        }
        allowed = valid_transitions.get(td.status, [])
        if new_status in allowed:
            td.status = new_status
        td.admin_notes = admin_notes
        td.save()
        log_action('status', 'Test Drives', f'Test drive #{pk} → {td.status}')
    return redirect('admin_test_drives')


@login_required
def admin_test_drive_delete(request, pk):
    td = get_object_or_404(TestDriveRequest, pk=pk)
    if request.method == 'POST':
        log_action('delete', 'Test Drives', f'Deleted test drive #{pk} ({td.name})')
        td.delete()
    return redirect('admin_test_drives')


@login_required
def admin_reviews(request):
    reviews = CustomerReview.objects.all().order_by('-date_submitted')
    return render(request, 'horizon/admin_reviews.html', {'reviews': reviews})


@login_required
def admin_review_add(request):
    if request.method == 'POST':
        customer_name     = request.POST.get('customer_name', '').strip()
        vehicle_purchased = request.POST.get('vehicle_purchased', '').strip()
        rating_val        = request.POST.get('rating', '5')
        review_text       = request.POST.get('review_text', '').strip()
        is_approved       = request.POST.get('is_approved') == 'on'
        photo             = request.FILES.get('photo')
        if customer_name and vehicle_purchased and review_text:
            try:
                rating_int = int(rating_val)
                if 1 <= rating_int <= 5:
                    CustomerReview.objects.create(
                        customer_name=customer_name,
                        vehicle_purchased=vehicle_purchased,
                        rating=rating_int,
                        review_text=review_text,
                        photo=photo,
                        is_approved=is_approved,
                    )
                    messages.success(request, 'Review added successfully.')
            except ValueError:
                pass
        return redirect('admin_reviews')
    cars = Car.objects.filter(status="sold").order_by('brand__name', 'model')
    return render(request, 'horizon/admin_review_form.html', {'cars': cars})


@login_required
def admin_review_toggle(request, pk):
    review = get_object_or_404(CustomerReview, pk=pk)
    review.is_approved = not review.is_approved
    review.save(update_fields=['is_approved'])
    return redirect('admin_reviews')


@login_required
def admin_review_delete(request, pk):
    review = get_object_or_404(CustomerReview, pk=pk)
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted.')
    return redirect('admin_reviews')


@login_required
def admin_category_delete(request, pk):
    import os
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        if category.car_set.exists():
            messages.error(request, f'Cannot delete "{category.name}" — it is used by existing cars.')
        else:
            name = category.name
            if category.icon:
                try:
                    if os.path.isfile(category.icon.path):
                        os.remove(category.icon.path)
                except Exception:
                    pass
            category.delete()
            messages.success(request, f'Category "{name}" deleted.')
    return redirect('/admin-panel/brands/?tab=categories')


# ─── WISHLIST VIEWS (session-based) ──────────────────────────────────────────

def _get_wishlist(request):
    return request.session.get('wishlist', [])

def _save_wishlist(request, ids):
    request.session['wishlist'] = list(ids)
    request.session.modified = True

def wishlist(request):
    ids = _get_wishlist(request)
    cars = Car.objects.filter(pk__in=ids).select_related('brand', 'category')
    # Preserve order
    car_map = {c.pk: c for c in cars}
    ordered = [car_map[i] for i in ids if i in car_map]
    return render(request, 'horizon/wishlist.html', {'cars': ordered})

@csrf_exempt
def wishlist_toggle(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    car = get_object_or_404(Car, pk=pk)
    ids = _get_wishlist(request)
    if pk in ids:
        ids.remove(pk)
        saved = False
    else:
        ids.append(pk)
        saved = True
    _save_wishlist(request, ids)
    return JsonResponse({'saved': saved, 'count': len(ids)})

def wishlist_status(request):
    ids = _get_wishlist(request)
    return JsonResponse({'ids': ids, 'count': len(ids)})


# ─── COMPARISON VIEWS (session-based) ────────────────────────────────────────

MAX_COMPARE = 3

def _get_compare(request):
    return request.session.get('compare_list', [])

def _save_compare(request, ids):
    request.session['compare_list'] = list(ids)
    request.session.modified = True

def compare(request):
    ids = _get_compare(request)
    cars = Car.objects.filter(pk__in=ids).select_related('brand', 'category')
    car_map = {c.pk: c for c in cars}
    ordered = [car_map[i] for i in ids if i in car_map]
    return render(request, 'horizon/compare.html', {'cars': ordered, 'max_compare': MAX_COMPARE})

@csrf_exempt
def compare_add(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    car = get_object_or_404(Car, pk=pk)
    ids = _get_compare(request)
    if pk in ids:
        return JsonResponse({'added': False, 'already': True, 'count': len(ids)})
    if len(ids) >= MAX_COMPARE:
        return JsonResponse({'added': False, 'full': True, 'count': len(ids), 'max': MAX_COMPARE})
    ids.append(pk)
    _save_compare(request, ids)
    return JsonResponse({'added': True, 'count': len(ids), 'max': MAX_COMPARE})

@csrf_exempt
def compare_remove(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    ids = _get_compare(request)
    if pk in ids:
        ids.remove(pk)
    _save_compare(request, ids)
    return JsonResponse({'removed': True, 'count': len(ids)})

@csrf_exempt
def compare_clear(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    _save_compare(request, [])
    return JsonResponse({'cleared': True})

def compare_status(request):
    ids = _get_compare(request)
    return JsonResponse({'ids': ids, 'count': len(ids), 'max': MAX_COMPARE})


# ══════════════════════════════════════════════════════════════
# ACTIVITY LOG VIEWS
# ══════════════════════════════════════════════════════════════

def log_action(action, section, detail=''):
    """Helper to record an admin action in the ActivityLog."""
    ActivityLog.objects.create(
        action=action,
        section=section,
        detail=detail,
    )


@login_required
def admin_activity_log(request):
    """Display the staff activity log with optional filters."""
    section_filter = request.GET.get('section', '').strip()
    action_filter  = request.GET.get('action', '').strip()

    logs = ActivityLog.objects.all()

    if section_filter:
        logs = logs.filter(section__icontains=section_filter)
    if action_filter:
        logs = logs.filter(action=action_filter)

    # Paginate — 50 per page
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    sections = ActivityLog.objects.values_list('section', flat=True).distinct().order_by('section')

    return render(request, 'horizon/admin_activity_log.html', {
        'page_obj':       page_obj,
        'sections':       sections,
        'action_choices': ActivityLog.ACTION_CHOICES,
        'section_filter': section_filter,
        'action_filter':  action_filter,
    })


@login_required
def admin_activity_log_clear(request):
    """Allow superuser to clear all log entries."""
    if request.method == 'POST':
        ActivityLog.objects.all().delete()
        messages.success(request, 'Activity log cleared.')
    return redirect('admin_activity_log')


# ─── VEHICLE WARRANTY / CERTIFICATE PDF ──────────────────────────────────────

def vehicle_warranty_pdf(request, pk):
    """Generate a print-ready Vehicle Certificate & Warranty PDF for a single car."""
    car = get_object_or_404(Car, pk=pk)
    ds  = DealershipSettings.get()
    now = timezone.localtime(timezone.now())

    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, Image as RLImage,
    )
    from reportlab.graphics.shapes import Drawing, Rect, String, Line
    from reportlab.graphics import renderPDF
    import io, os

    # ── Palette ──────────────────────────────────────────────
    BLACK      = colors.HexColor('#0d0d0d')
    GOLD       = colors.HexColor('#b8a46e')
    GOLD_LIGHT = colors.HexColor('#e8dfc0')
    WHITE      = colors.white
    GREY_DARK  = colors.HexColor('#333333')
    GREY_MID   = colors.HexColor('#666666')
    GREY_LIGHT = colors.HexColor('#f5f5f5')
    GREY_LINE  = colors.HexColor('#e0e0e0')
    RED_WARN   = colors.HexColor('#c62828')

    W, H = A4   # 595 x 842 pts

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=14*mm, bottomMargin=14*mm,
        title=f"Vehicle Certificate — {car}",
        author=ds.dealership_name,
    )

    story = []

    # ── Helper styles ─────────────────────────────────────────
    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    eyebrow  = S('ey',  fontName='Helvetica',      fontSize=7,  textColor=GOLD,      leading=9,  spaceAfter=1,  letterSpacing=2.5, alignment=TA_CENTER)
    title_s  = S('ti',  fontName='Helvetica-Bold', fontSize=22, textColor=BLACK,      leading=26, spaceAfter=2,  alignment=TA_CENTER)
    sub_s    = S('su',  fontName='Helvetica',      fontSize=9,  textColor=GREY_MID,  leading=12, spaceAfter=0,  alignment=TA_CENTER)
    sec_head = S('sh',  fontName='Helvetica-Bold', fontSize=7.5,textColor=GOLD,      leading=10, spaceBefore=6, spaceAfter=3,  letterSpacing=2)
    body_s   = S('bo',  fontName='Helvetica',      fontSize=8.5,textColor=GREY_DARK, leading=12)
    val_s    = S('va',  fontName='Helvetica-Bold', fontSize=9,  textColor=BLACK,     leading=12)
    small_s  = S('sm',  fontName='Helvetica',      fontSize=7,  textColor=GREY_MID,  leading=9,  alignment=TA_CENTER)
    warn_s   = S('wa',  fontName='Helvetica-Bold', fontSize=7.5,textColor=RED_WARN,  leading=10, alignment=TA_CENTER)
    footer_s = S('fo',  fontName='Helvetica',      fontSize=6.5,textColor=GREY_MID,  leading=9,  alignment=TA_CENTER)
    right_s  = S('ri',  fontName='Helvetica',      fontSize=7,  textColor=GREY_MID,  leading=9,  alignment=TA_RIGHT)

    # ── Doc-number & date block ───────────────────────────────
    cert_no = f"HRZ-{car.pk:06d}-{now.year}"
    date_str = now.strftime("%B %d, %Y")

    # ── TOP HEADER BANNER ─────────────────────────────────────
    # Gold bar drawn via a 1-row Table with background
    banner_data = [[
        Paragraph(f'<font color="#b8a46e">■</font>  {ds.dealership_name.upper()}', S('bn', fontName='Helvetica-Bold', fontSize=11, textColor=WHITE, leading=14)),
        Paragraph(f'CERT. NO. {cert_no}<br/>{date_str}', S('bn2', fontName='Helvetica', fontSize=7, textColor=GOLD_LIGHT, leading=10, alignment=TA_RIGHT)),
    ]]
    banner_table = Table(banner_data, colWidths=[doc.width * 0.6, doc.width * 0.4])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BLACK),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',(0,0), (-1,-1), 8),
        ('RIGHTPADDING',(0,0),(-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0),(-1,-1), 8),
    ]))
    story.append(banner_table)

    # Gold rule under banner
    story.append(HRFlowable(width='100%', thickness=2.5, color=GOLD, spaceAfter=6, spaceBefore=0))

    # ── DOCUMENT TITLE ────────────────────────────────────────
    story.append(Paragraph('VEHICLE CERTIFICATE OF SALE &amp; WARRANTY', eyebrow))
    story.append(Paragraph(str(car).upper(), title_s))
    story.append(Paragraph(f'{ds.tagline or "Premium vehicles, exceptional service."}', sub_s))
    story.append(HRFlowable(width='60%', thickness=0.5, color=GOLD_LIGHT, spaceAfter=10, spaceBefore=4))

    # ── CAR PHOTO + SPECS SIDE BY SIDE ───────────────────────
    photo_cell_content = []
    photo_path = None
    if car.photo and hasattr(car.photo, 'path'):
        try:
            photo_path = car.photo.path
            if os.path.exists(photo_path):
                img = RLImage(photo_path, width=72*mm, height=52*mm)
                img.hAlign = 'CENTER'
                photo_cell_content.append(img)
        except Exception:
            photo_path = None

    if not photo_path:
        # Placeholder box
        placeholder = Drawing(72*mm, 52*mm)
        placeholder.add(Rect(0, 0, 72*mm, 52*mm, fillColor=GREY_LIGHT, strokeColor=GREY_LINE, strokeWidth=0.5))
        placeholder.add(String(36*mm, 26*mm, 'NO IMAGE', fontSize=8, fillColor=GREY_MID, textAnchor='middle'))
        photo_cell_content.append(placeholder)

    photo_cell_content.append(Spacer(1, 3))
    status_color = {'available': '#15803d', 'reserved': '#b45309', 'sold': '#374151'}.get(car.status, '#374151')
    photo_cell_content.append(
        Paragraph(f'<font color="{status_color}">● {car.get_status_display().upper()}</font>',
                  S('st', fontName='Helvetica-Bold', fontSize=7.5, textColor=BLACK, leading=10, alignment=TA_CENTER, letterSpacing=1.5))
    )

    # Specs grid
    def spec_row(label, value):
        return [
            Paragraph(label.upper(), S('sl', fontName='Helvetica', fontSize=6.5, textColor=GREY_MID, leading=9, letterSpacing=1)),
            Paragraph(str(value) if value else '—', S('sv', fontName='Helvetica-Bold', fontSize=8.5, textColor=BLACK, leading=11)),
        ]

    price_val = '—'
    if car.sale_price:
        if car.has_discount and car.discounted_price:
            price_val = f'PHP {car.discounted_price:,.2f}  ({car.discount_percent}% off)'
        else:
            price_val = f'PHP {car.sale_price:,.2f}'

    specs_data = [
        spec_row('Brand',        car.brand or '—'),
        spec_row('Model',        car.model),
        spec_row('Year',         car.year),
        spec_row('Category',     car.category or '—'),
        spec_row('Color',        car.color or '—'),
        spec_row('Transmission', car.get_transmission_display()),
        spec_row('Fuel Type',    car.get_fuel_type_display()),
        spec_row('Mileage',      f'{car.mileage:,} km' if car.mileage else '—'),
        spec_row('Plate No.',    car.plate_number or '—'),
        spec_row('Sale Price',   price_val),
    ]
    specs_table = Table(specs_data, colWidths=[28*mm, 60*mm])
    specs_table.setStyle(TableStyle([
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
        ('LINEBELOW',     (0,0), (-1,-2), 0.3, GREY_LINE),
    ]))

    top_table = Table(
        [[photo_cell_content, specs_table]],
        colWidths=[78*mm, doc.width - 78*mm],
    )
    top_table.setStyle(TableStyle([
        ('VALIGN',       (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',  (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING',   (0,0), (-1,-1), 0),
        ('BOTTOMPADDING',(0,0), (-1,-1), 0),
        ('LINEAFTER',    (0,0), (0,-1), 0.5, GREY_LINE),
        ('RIGHTPADDING', (0,0), (0,-1), 8),
        ('LEFTPADDING',  (1,0), (1,-1), 10),
    ]))
    story.append(top_table)
    story.append(Spacer(1, 8))

    # ── DESCRIPTION ───────────────────────────────────────────
    if car.description:
        story.append(HRFlowable(width='100%', thickness=0.4, color=GREY_LINE, spaceAfter=6, spaceBefore=2))
        story.append(Paragraph('VEHICLE DESCRIPTION', sec_head))
        story.append(Paragraph(car.description, body_s))
        story.append(Spacer(1, 6))

    # ── WARRANTY TERMS ────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=0.4, color=GREY_LINE, spaceAfter=6, spaceBefore=2))
    story.append(Paragraph('WARRANTY &amp; COVERAGE TERMS', sec_head))

    warranty_items = [
        ('Engine &amp; Drivetrain', '12 months / 20,000 km (whichever comes first) — covers mechanical defects in engine internals, transmission, and drivetrain components under normal use.'),
        ('Electrical Systems',      '6 months — covers factory-installed electrical components including alternator, starter motor, and ECU under normal operating conditions.'),
        ('Air Conditioning',        '6 months — covers compressor, condenser, and evaporator defects not caused by refrigerant leaks due to physical damage.'),
        ('Chassis &amp; Suspension','6 months — covers structural defects in frame, control arms, and suspension mounts.'),
        ('Body &amp; Paint',        '3 months — covers factory paint defects and panel corrosion arising from manufacturing faults.'),
        ('After-Sales Service',     'Complimentary 1,000 km check-up included. Priority scheduling at Horizon service center.'),
    ]

    for term, desc in warranty_items:
        row = Table(
            [[Paragraph(f'<b>{term}</b>', S('wt', fontName='Helvetica-Bold', fontSize=8, textColor=BLACK, leading=11)),
              Paragraph(desc, S('wd', fontName='Helvetica', fontSize=7.5, textColor=GREY_DARK, leading=11))]],
            colWidths=[42*mm, doc.width - 42*mm],
        )
        row.setStyle(TableStyle([
            ('VALIGN',       (0,0),(-1,-1),'TOP'),
            ('TOPPADDING',   (0,0),(-1,-1), 3),
            ('BOTTOMPADDING',(0,0),(-1,-1), 3),
            ('LEFTPADDING',  (0,0),(-1,-1), 0),
            ('RIGHTPADDING', (0,0),(-1,-1), 0),
            ('LINEBELOW',    (0,0),(-1,-1), 0.3, GREY_LINE),
        ]))
        story.append(row)

    story.append(Spacer(1, 6))

    # ── EXCLUSIONS ────────────────────────────────────────────
    story.append(Paragraph('WARRANTY EXCLUSIONS', sec_head))
    exclusions = (
        'This warranty does not cover: (1) damage caused by accidents, negligence, or improper use; '
        '(2) normal wear items such as tires, brake pads, filters, and belts; '
        '(3) modifications or repairs performed by unauthorized service centers; '
        '(4) damage from floods, fires, or other force majeure events; '
        '(5) cosmetic damage not present at time of purchase.'
    )
    story.append(Paragraph(exclusions, S('ex', fontName='Helvetica', fontSize=7.5, textColor=GREY_DARK, leading=11)))
    story.append(Spacer(1, 8))

    # ── SIGNATURE BLOCK ───────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=0.4, color=GREY_LINE, spaceAfter=8, spaceBefore=2))
    sig_data = [
        [
            Paragraph('AUTHORIZED BY', S('sl2', fontName='Helvetica', fontSize=6.5, textColor=GREY_MID, leading=9, letterSpacing=1, alignment=TA_CENTER)),
            Paragraph('', body_s),
            Paragraph('RECEIVED BY', S('sl2', fontName='Helvetica', fontSize=6.5, textColor=GREY_MID, leading=9, letterSpacing=1, alignment=TA_CENTER)),
        ],
        [
            Paragraph('<br/><br/>', body_s),
            Paragraph('', body_s),
            Paragraph('<br/><br/>', body_s),
        ],
        [
            HRFlowable(width='100%', thickness=0.5, color=BLACK),
            Paragraph('', body_s),
            HRFlowable(width='100%', thickness=0.5, color=BLACK),
        ],
        [
            Paragraph(f'{ds.dealership_name}<br/><font color="#666666" size="7">Authorized Dealer Representative</font>',
                      S('si', fontName='Helvetica-Bold', fontSize=8, textColor=BLACK, leading=11, alignment=TA_CENTER)),
            Paragraph('', body_s),
            Paragraph('Customer / Buyer<br/><font color="#666666" size="7">Print name &amp; signature above</font>',
                      S('si2', fontName='Helvetica', fontSize=8, textColor=GREY_DARK, leading=11, alignment=TA_CENTER)),
        ],
    ]
    sig_table = Table(sig_data, colWidths=[70*mm, 20*mm, 70*mm])
    sig_table.setStyle(TableStyle([
        ('VALIGN',       (0,0),(-1,-1),'MIDDLE'),
        ('ALIGN',        (0,0),(-1,-1),'CENTER'),
        ('TOPPADDING',   (0,0),(-1,-1), 2),
        ('BOTTOMPADDING',(0,0),(-1,-1), 2),
        ('LEFTPADDING',  (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 8))

    # ── DEALERSHIP CONTACT FOOTER ─────────────────────────────
    story.append(HRFlowable(width='100%', thickness=2, color=BLACK, spaceAfter=5, spaceBefore=0))
    contact_data = [[
        Paragraph(f'📍 {ds.address}',             footer_s),
        Paragraph(f'📞 {ds.phone}',               footer_s),
        Paragraph(f'✉ {ds.email}',                footer_s),
        Paragraph(f'Mon–Fri {ds.weekday_hours}',  footer_s),
    ]]
    contact_table = Table(contact_data, colWidths=[doc.width / 4] * 4)
    contact_table.setStyle(TableStyle([
        ('ALIGN',        (0,0),(-1,-1),'CENTER'),
        ('VALIGN',       (0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',   (0,0),(-1,-1), 2),
        ('BOTTOMPADDING',(0,0),(-1,-1), 2),
        ('LINEBEFORE',   (1,0),(3,-1), 0.3, GREY_LINE),
    ]))
    story.append(contact_table)
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        f'This document is computer-generated and valid without a physical seal. '
        f'Cert. No. {cert_no} · Issued {date_str} · {ds.dealership_name}',
        footer_s,
    ))

    doc.build(story)
    buf.seek(0)

    filename = f"vehicle-certificate-{car.pk}-{car.model.replace(' ', '-').lower()}.pdf"
    response = HttpResponse(buf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
