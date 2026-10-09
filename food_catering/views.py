import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_POST

from .models import StationRestaurant, FoodCategory, FoodItem, FoodOrder, FoodOrderItem
from railways.models import RailwayStation, TrainSchedule, Train
from bookings.models import Booking

def food_index(request):
    """
    Landing page for Order Food in Train (E-Catering).
    Allows searching by PNR or Station/Train, and showcases popular restaurants & meals.
    """
    stations = RailwayStation.objects.filter(is_active=True).order_by('city')
    categories = FoodCategory.objects.all().order_by('display_order')
    featured_items = FoodItem.objects.filter(is_available=True, is_bestseller=True).select_related('restaurant', 'restaurant__station', 'category')[:8]
    if not featured_items.exists():
        featured_items = FoodItem.objects.filter(is_available=True).select_related('restaurant', 'restaurant__station', 'category')[:8]
    
    top_restaurants = StationRestaurant.objects.filter(is_active=True).select_related('station')[:6]

    # Preload user's latest train booking if logged in
    user_train_booking = None
    if request.user.is_authenticated:
        user_train_booking = Booking.objects.filter(
            user=request.user, transport_type='TRAIN', booking_status='CONFIRMED', journey_date__gte=timezone.now().date()
        ).order_by('journey_date').first()

    context = {
        'stations': stations,
        'categories': categories,
        'featured_items': featured_items,
        'top_restaurants': top_restaurants,
        'user_train_booking': user_train_booking,
    }
    return render(request, 'food_catering/index.html', context)


def restaurant_menu(request, restaurant_id=None, station_code=None):
    """
    Displays restaurant menu with category tabs, dietary filter (Veg/Non-Veg/Jain), and interactive cart.
    """
    restaurant = None
    station = None
    
    if restaurant_id:
        restaurant = get_object_or_404(StationRestaurant.objects.select_related('station'), id=restaurant_id, is_active=True)
        station = restaurant.station
        items = FoodItem.objects.filter(restaurant=restaurant, is_available=True).select_related('category', 'restaurant')
    elif station_code:
        station = get_object_or_404(RailwayStation, code__iexact=station_code)
        restaurant = StationRestaurant.objects.filter(station=station, is_active=True).first()
        items = FoodItem.objects.filter(restaurant__station=station, is_available=True).select_related('category', 'restaurant')
    else:
        # Default to first active restaurant
        restaurant = StationRestaurant.objects.filter(is_active=True).select_related('station').first()
        if restaurant:
            station = restaurant.station
            items = FoodItem.objects.filter(restaurant=restaurant, is_available=True).select_related('category', 'restaurant')
        else:
            items = FoodItem.objects.none()

    # Filters
    diet_filter = request.GET.get('diet', 'ALL').upper() # ALL, VEG, NON_VEG, JAIN
    if diet_filter == 'VEG':
        items = items.filter(is_veg=True)
    elif diet_filter == 'NON_VEG':
        items = items.filter(is_veg=False)
    elif diet_filter == 'JAIN':
        items = items.filter(is_jain=True)

    category_slug = request.GET.get('category')
    if category_slug:
        items = items.filter(category__slug=category_slug)

    categories = FoodCategory.objects.all().order_by('display_order')

    # Read existing cart from session
    cart = request.session.get('food_cart', {})
    cart_items = []
    cart_total = Decimal('0.00')
    cart_count = 0

    if cart:
        for item_id_str, qty in cart.items():
            try:
                f_item = FoodItem.objects.get(id=int(item_id_str), is_available=True)
                item_subtotal = f_item.price * Decimal(qty)
                cart_items.append({
                    'item': f_item,
                    'quantity': qty,
                    'subtotal': item_subtotal,
                })
                cart_total += item_subtotal
                cart_count += qty
            except (FoodItem.DoesNotExist, ValueError):
                pass

    # Optional pre-filled PNR parameters
    pnr_param = request.GET.get('pnr', '')
    train_param = request.GET.get('train', '')
    coach_param = request.GET.get('coach', '')
    seat_param = request.GET.get('seat', '')

    context = {
        'restaurant': restaurant,
        'station': station,
        'items': items,
        'categories': categories,
        'current_diet': diet_filter,
        'current_category': category_slug,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': cart_count,
        'pnr_param': pnr_param,
        'train_param': train_param,
        'coach_param': coach_param,
        'seat_param': seat_param,
    }
    return render(request, 'food_catering/menu.html', context)


@require_POST
def api_update_cart(request):
    """
    AJAX API to add, update, or remove items in the session food cart.
    """
    try:
        data = json.loads(request.body)
        item_id = str(data.get('item_id'))
        action = data.get('action') # 'add', 'remove', 'set', 'clear'
        quantity = int(data.get('quantity', 1))
    except Exception:
        return JsonResponse({'success': False, 'message': 'Invalid payload.'}, status=400)

    cart = request.session.get('food_cart', {})

    if action == 'add':
        cart[item_id] = cart.get(item_id, 0) + quantity
    elif action == 'remove':
        if item_id in cart:
            cart[item_id] -= 1
            if cart[item_id] <= 0:
                del cart[item_id]
    elif action == 'set':
        if quantity <= 0:
            cart.pop(item_id, None)
        else:
            cart[item_id] = quantity
    elif action == 'clear':
        cart = {}

    request.session['food_cart'] = cart
    request.session.modified = True

    # Recalculate totals
    total_amount = Decimal('0.00')
    total_count = 0
    items_data = []

    for i_id, qty in cart.items():
        try:
            it = FoodItem.objects.get(id=int(i_id))
            sub = it.price * Decimal(qty)
            total_amount += sub
            total_count += qty
            items_data.append({
                'id': it.id,
                'name': it.name,
                'price': float(it.price),
                'quantity': qty,
                'subtotal': float(sub),
                'is_veg': it.is_veg,
            })
        except Exception:
            pass

    return JsonResponse({
        'success': True,
        'cart_count': total_count,
        'cart_total': float(total_amount),
        'items': items_data,
    })


def food_checkout(request):
    """
    Review meal cart and enter Passenger Coach/Seat & Station Delivery details.
    """
    cart = request.session.get('food_cart', {})
    if not cart:
        messages.warning(request, "Your meal cart is currently empty. Please select dishes to proceed.")
        return redirect('food_catering:index')

    cart_items = []
    base_total = Decimal('0.00')
    first_restaurant = None

    for item_id_str, qty in cart.items():
        try:
            f_item = FoodItem.objects.select_related('restaurant', 'restaurant__station').get(id=int(item_id_str))
            if not first_restaurant:
                first_restaurant = f_item.restaurant
            subtotal = f_item.price * Decimal(qty)
            base_total += subtotal
            cart_items.append({
                'item': f_item,
                'quantity': qty,
                'subtotal': subtotal,
            })
        except FoodItem.DoesNotExist:
            pass

    if not cart_items:
        messages.error(request, "Invalid cart contents.")
        return redirect('food_catering:index')

    # Calculations: 5% GST, Delivery Fee (Free if base >= 200)
    gst = round(base_total * Decimal('0.05'), 2)
    delivery_fee = Decimal('0.00') if base_total >= Decimal('200.00') else Decimal('29.00')
    grand_total = base_total + gst + delivery_fee

    stations = RailwayStation.objects.filter(is_active=True).order_by('city')

    # Pre-fill data from query params or user booking
    pnr = request.GET.get('pnr', '').strip().upper()
    train_number = request.GET.get('train_number', '').strip()
    train_name = request.GET.get('train_name', '').strip()
    coach = request.GET.get('coach', '').strip().upper()
    seat_number = request.GET.get('seat', '').strip()
    passenger_name = ''
    passenger_phone = ''

    if request.user.is_authenticated:
        passenger_name = request.user.get_full_name() or request.user.username
        if hasattr(request.user, 'profile') and request.user.profile.phone:
            passenger_phone = request.user.profile.phone

    # If PNR is passed, try auto-filling from existing RailAway booking
    if pnr:
        b = Booking.objects.filter(pnr=pnr).first()
        if b:
            train_number = b.train_schedule.train.train_number if b.train_schedule else ''
            train_name = b.service_title
            passengers = b.passengers.all()
            if passengers.exists():
                first_p = passengers.first()
                passenger_name = first_p.full_name
                passenger_phone = first_p.phone or passenger_phone
                allocated = b.allocated_seats.split(',')[0].strip()
                if '-' in allocated:
                    coach, seat_number = allocated.split('-', 1)
                else:
                    seat_number = allocated

    context = {
        'cart_items': cart_items,
        'base_total': base_total,
        'gst': gst,
        'delivery_fee': delivery_fee,
        'grand_total': grand_total,
        'restaurant': first_restaurant,
        'stations': stations,
        'pnr': pnr,
        'train_number': train_number,
        'train_name': train_name,
        'coach': coach,
        'seat_number': seat_number,
        'passenger_name': passenger_name,
        'passenger_phone': passenger_phone,
    }
    return render(request, 'food_catering/checkout.html', context)


@require_POST
def food_process_order(request):
    """
    Submits and confirms the meal order with simulated payment.
    """
    cart = request.session.get('food_cart', {})
    if not cart:
        messages.error(request, "Your meal cart is empty.")
        return redirect('food_catering:index')

    pnr = request.POST.get('pnr', '').strip().upper()
    train_number = request.POST.get('train_number', '').strip()
    train_name = request.POST.get('train_name', '').strip() or f"Train {train_number}"
    delivery_station_id = request.POST.get('delivery_station')
    coach = request.POST.get('coach', '').strip().upper()
    seat_number = request.POST.get('seat_number', '').strip().upper()
    passenger_name = request.POST.get('passenger_name', '').strip()
    passenger_phone = request.POST.get('passenger_phone', '').strip()
    payment_method = request.POST.get('payment_method', 'UPI')
    special_instructions = request.POST.get('special_instructions', '').strip()

    if not train_number or not coach or not seat_number or not passenger_name or not passenger_phone:
        messages.error(request, "Please fill in all passenger and seat delivery information.")
        return redirect('food_catering:checkout')

    delivery_station = get_object_or_404(RailwayStation, id=delivery_station_id) if delivery_station_id else RailwayStation.objects.first()

    with transaction.atomic():
        # Calculate items and total
        base_total = Decimal('0.00')
        order_items_to_create = []
        restaurant_obj = None

        for item_id_str, qty in cart.items():
            f_item = FoodItem.objects.select_related('restaurant').get(id=int(item_id_str))
            if not restaurant_obj:
                restaurant_obj = f_item.restaurant
            subtotal = f_item.price * Decimal(qty)
            base_total += subtotal
            order_items_to_create.append({
                'item': f_item,
                'name': f_item.name,
                'is_veg': f_item.is_veg,
                'quantity': qty,
                'price': f_item.price,
                'subtotal': subtotal,
            })

        gst = round(base_total * Decimal('0.05'), 2)
        delivery_fee = Decimal('0.00') if base_total >= Decimal('200.00') else Decimal('29.00')
        grand_total = base_total + gst + delivery_fee

        payment_status = 'CASH_ON_DELIVERY' if payment_method == 'COD' else 'PAID'

        order = FoodOrder.objects.create(
            user=request.user if request.user.is_authenticated else None,
            restaurant=restaurant_obj,
            pnr=pnr,
            train_number=train_number,
            train_name=train_name,
            delivery_station=delivery_station,
            delivery_date=timezone.now().date(),
            delivery_time_slot=f"On arrival at {delivery_station.name}",
            coach=coach,
            seat_number=seat_number,
            passenger_name=passenger_name,
            passenger_phone=passenger_phone,
            special_instructions=special_instructions,
            base_amount=base_total,
            gst=gst,
            delivery_fee=delivery_fee,
            total_amount=grand_total,
            status='CONFIRMED',
            payment_method=payment_method,
            payment_status=payment_status,
        )

        for oi in order_items_to_create:
            FoodOrderItem.objects.create(
                order=order,
                item=oi['item'],
                item_name=oi['name'],
                is_veg=oi['is_veg'],
                quantity=oi['quantity'],
                unit_price=oi['price'],
                total_price=oi['subtotal'],
            )

        # Clear session cart
        request.session['food_cart'] = {}
        request.session.modified = True

    messages.success(request, f"Meal order confirmed! Reference #{order.order_ref}. Hot food will be delivered to Coach {order.coach}, Seat {order.seat_number} at {delivery_station.name}.")
    return redirect('food_catering:order_tracker', order_ref=order.order_ref)


def food_order_tracker(request, order_ref):
    """
    Live real-time order tracking visualizer with stepper progress, invoice breakdown, and delivery contact.
    """
    order = get_object_or_404(
        FoodOrder.objects.select_related('restaurant', 'delivery_station').prefetch_related('items'),
        order_ref=order_ref
    )
    return render(request, 'food_catering/order_tracker.html', {'order': order})


def api_pnr_lookup(request):
    """
    AJAX API: Look up train journey info from an existing RailAway PNR.
    """
    pnr = request.GET.get('pnr', '').strip().upper()
    if not pnr:
        return JsonResponse({'found': False, 'message': 'PNR required'})

    booking = Booking.objects.filter(pnr=pnr).first()
    if not booking:
        return JsonResponse({'found': False, 'message': f"No booking found for PNR '{pnr}'"})

    passengers = booking.passengers.all()
    first_pass = passengers.first()
    p_name = first_pass.full_name if first_pass else booking.user.get_full_name()
    p_phone = first_pass.phone if first_pass else ''

    coach = 'B1'
    seat = '12'
    if booking.allocated_seats:
        first_seat = booking.allocated_seats.split(',')[0].strip()
        if '-' in first_seat:
            coach, seat = first_seat.split('-', 1)
        else:
            seat = first_seat

    train_no = booking.train_schedule.train.train_number if booking.train_schedule else '22436'
    src_station = booking.source_location
    dst_station = booking.destination_location

    return JsonResponse({
        'found': True,
        'pnr': booking.pnr,
        'train_number': train_no,
        'train_name': booking.service_title,
        'source_station': src_station,
        'destination_station': dst_station,
        'passenger_name': p_name,
        'passenger_phone': p_phone,
        'coach': coach,
        'seat_number': seat,
        'journey_date': booking.journey_date.strftime('%d %b %Y'),
    })


def cancel_food_order(request, order_ref):
    """
    1-Click automated cancellation for meal orders with 100% refund before dispatch.
    """
    order = get_object_or_404(FoodOrder, order_ref=order_ref)
    
    if request.user.is_authenticated and order.user and order.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Not authorized to cancel this meal order.")

    if order.status == 'CANCELLED':
        messages.info(request, "This meal order is already cancelled.")
        return redirect('food_catering:order_tracker', order_ref=order.order_ref)

    if order.status in ['OUT_FOR_DELIVERY', 'DELIVERED']:
        messages.error(request, "Orders already dispatched or delivered cannot be cancelled.")
        return redirect('food_catering:order_tracker', order_ref=order.order_ref)

    # 100% refund for meal orders cancelled prior to dispatch
    order.status = 'CANCELLED'
    if order.payment_status in ['PAID', 'SUCCESS']:
        order.payment_status = 'REFUNDED'
    order.save()

    messages.success(request, f"Meal order #{order.order_ref} cancelled successfully. Full refund of ₹{order.total_amount} initiated.")
    return redirect('food_catering:order_tracker', order_ref=order.order_ref)

