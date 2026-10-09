import time
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseForbidden

from .models import Payment, generate_transaction_id
from bookings.models import Booking
from railways.models import TrainSeat
from airlines.models import FlightSeat
from buses.models import BusSeat

@login_required
def process_payment(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related('user').prefetch_related('passengers'),
        id=booking_id
    )

    if booking.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You do not have access to this payment session.")

    if booking.booking_status == 'CONFIRMED':
        messages.info(request, "This booking has already been paid for and confirmed.")
        return redirect('bookings:ticket', pnr=booking.pnr)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'CREDIT_CARD')
        simulate_action = request.POST.get('simulate_action', 'SUCCESS') # SUCCESS or FAIL

        card_number = request.POST.get('card_number', '').replace(' ', '')
        card_network = request.POST.get('card_network', 'Visa')
        bank_name = request.POST.get('bank_name', 'State Bank of India')
        upi_id = request.POST.get('upi_id', 'user@upi')

        if simulate_action == 'FAIL':
            # Create failed payment log
            Payment.objects.update_or_create(
                booking=booking,
                defaults={
                    'payment_method': payment_method,
                    'amount': booking.total_amount,
                    'payment_status': 'FAILED',
                    'gateway_response': 'Declined by simulated bank: Insufficient funds or invalid PIN simulation',
                    'card_last4': card_number[-4:] if len(card_number) >= 4 else '0000',
                    'bank_name': bank_name,
                    'upi_id': upi_id,
                }
            )
            booking.payment_status = 'FAILED'
            booking.save()
            messages.error(request, "Simulated payment failed as requested. You can retry with another method.")
            return render(request, 'payments/process.html', {'booking': booking})

        # Process SUCCESS transaction atomically
        with transaction.atomic():
            # 1. Mark seats as booked
            seat_list = [s.strip() for s in booking.allocated_seats.split(',') if s.strip()]

            if booking.transport_type == 'TRAIN' and booking.train_schedule:
                for s_str in seat_list:
                    parts = s_str.split('-')
                    if len(parts) == 2:
                        TrainSeat.objects.filter(
                            schedule=booking.train_schedule,
                            coach=parts[0].strip(),
                            seat_number=parts[1].strip()
                        ).update(is_booked=True)
                    else:
                        TrainSeat.objects.filter(
                            schedule=booking.train_schedule,
                            seat_number=s_str
                        ).update(is_booked=True)

            elif booking.transport_type == 'FLIGHT' and booking.flight_schedule:
                for s_str in seat_list:
                    FlightSeat.objects.filter(
                        schedule=booking.flight_schedule,
                        seat_number=s_str
                    ).update(is_booked=True)

            elif booking.transport_type == 'BUS' and booking.bus_schedule:
                for s_str in seat_list:
                    BusSeat.objects.filter(
                        schedule=booking.bus_schedule,
                        seat_number=s_str
                    ).update(is_booked=True)

            # 2. Update Booking Status & Promo Usage
            booking.booking_status = 'CONFIRMED'
            booking.payment_status = 'SUCCESS'
            booking.save()

            if booking.promo_code_obj:
                from bookings.models import PromoCode
                from django.db.models import F
                PromoCode.objects.filter(id=booking.promo_code_obj_id).update(used_count=F('used_count') + 1)

            # 3. Create or Update Payment Record
            payment, _ = Payment.objects.update_or_create(
                booking=booking,
                defaults={
                    'payment_method': payment_method,
                    'amount': booking.total_amount,
                    'payment_status': 'SUCCESS',
                    'gateway_response': 'Simulated Payment Gateway Authorization Approved: AUTH_CODE_98762',
                    'card_last4': card_number[-4:] if len(card_number) >= 4 else '8821',
                    'card_network': card_network,
                    'bank_name': bank_name,
                    'upi_id': upi_id,
                }
            )

        messages.success(request, f"Payment of ₹{booking.total_amount} processed successfully! Your PNR is {booking.pnr}.")
        return redirect('bookings:ticket', pnr=booking.pnr)

    context = {
        'booking': booking,
    }
    return render(request, 'payments/process.html', context)
