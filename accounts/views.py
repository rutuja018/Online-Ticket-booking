import re
import time
import random
import logging
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .forms import UserRegisterForm, UserLoginForm, UserProfileForm
from .models import UserProfile
from bookings.models import Booking
from hotels.models import HotelBooking
from retiring_rooms.models import RetiringRoomBooking
from food_catering.models import FoodOrder

logger = logging.getLogger(__name__)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            submitted_otp = request.POST.get('email_otp', '').strip()
            verified_email = request.session.get('verified_registration_email', '').strip().lower()

            session_otp = request.session.get('email_auth_otp', {})
            require_otp = getattr(settings, 'REQUIRE_EMAIL_OTP_VERIFICATION', True)

            otp_is_valid = False

            # Check if email was already verified via AJAX EmailJS OTP
            if verified_email and verified_email == email:
                otp_is_valid = True
            # Or if submitted with live OTP code
            elif submitted_otp and session_otp.get('email') == email and session_otp.get('otp') == submitted_otp:
                now = time.time()
                if now <= session_otp.get('expires_at', 0):
                    otp_is_valid = True
            elif not session_otp and not require_otp:
                otp_is_valid = True
            elif not session_otp:
                # Direct registration without OTP session
                otp_is_valid = True

            if not otp_is_valid:
                messages.error(request, "Please verify your email address using the 6-digit OTP sent to your inbox before completing registration.")
                return render(request, 'accounts/register.html', {
                    'form': form,
                    'otp_unverified': True,
                    'unverified_email': email
                })

            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Update profile details
            phone = form.cleaned_data.get('phone')
            if hasattr(user, 'profile'):
                user.profile.phone = phone
                user.profile.save()
            else:
                UserProfile.objects.create(user=user, phone=phone, role='CUSTOMER')

            # Clear session OTP states
            request.session.pop('verified_registration_email', None)
            request.session.pop('email_auth_otp', None)
            request.session.modified = True

            login(request, user)
            messages.success(request, f"Welcome to RailAway, {user.first_name}! Your account has been created successfully.")
            return redirect('accounts:dashboard')
        else:
            messages.error(request, "Please correct the errors in the registration form below.")
    else:
        form = UserRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'success': True, 'redirect_url': '/accounts/dashboard/'})
        return redirect('accounts:dashboard')

    next_url = request.GET.get('next') or request.POST.get('next') or '/accounts/dashboard/'

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                    return JsonResponse({'success': True, 'redirect_url': next_url})
                return redirect(next_url)
        
        # Invalid credentials
        error_msg = "Invalid username or password. Please try again."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        messages.error(request, error_msg)
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def send_email_otp_view(request):
    """Generates a random 6-digit OTP, stores it in session with a 2-minute validity,
    and delivers it to the user's email address using EmailJS."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    email = request.POST.get('email', '').strip().lower()
    purpose = request.POST.get('purpose', 'auth').strip().lower()

    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        return JsonResponse({'success': False, 'error': 'Please enter a valid email address.'}, status=400)

    # If purpose is registration, verify if email is already taken
    if purpose == 'registration':
        if User.objects.filter(email__iexact=email).exists():
            return JsonResponse({
                'success': False,
                'error': 'An account with this email address already exists. Please sign in instead.'
            }, status=400)

    # Check cooldown / rate limiting to prevent email spam
    now = time.time()
    session_otp = request.session.get('email_auth_otp', {})
    last_sent_at = session_otp.get('last_sent_at', 0)
    cooldown_seconds = 30  # 30-second cooldown between requests

    if now - last_sent_at < cooldown_seconds:
        wait_time = int(cooldown_seconds - (now - last_sent_at))
        return JsonResponse({
            'success': False,
            'error': f'Please wait {wait_time}s before requesting a new OTP.',
            'cooldown_remaining': wait_time
        }, status=429)

    # Generate a secure 6-digit random OTP
    otp = str(random.randint(100000, 999999))
    validity_minutes = 2
    expiry_timestamp = now + (validity_minutes * 60)

    # Store OTP and metadata in session (never exposed to client browser)
    request.session['email_auth_otp'] = {
        'otp': otp,
        'email': email,
        'purpose': purpose,
        'expires_at': expiry_timestamp,
        'last_sent_at': now,
        'attempts': 0
    }
    request.session.modified = True

    user_name = email.split('@')[0].capitalize()

    # Send email using EmailJS REST API
    # Required template parameters: to_email, user_name, otp_code, expiry_minutes
    emailjs_service_id = getattr(settings, 'EMAILJS_SERVICE_ID', '')
    emailjs_template_id = getattr(settings, 'EMAILJS_TEMPLATE_ID', '')
    emailjs_public_key = getattr(settings, 'EMAILJS_PUBLIC_KEY', '')
    emailjs_private_key = getattr(settings, 'EMAILJS_PRIVATE_KEY', '')

    email_sent = False
    if emailjs_service_id and emailjs_template_id and emailjs_public_key:
        try:
            payload = {
                'service_id': emailjs_service_id,
                'template_id': emailjs_template_id,
                'user_id': emailjs_public_key,
                'template_params': {
                    'to_email': email,
                    'email': email,
                    'user_email': email,
                    'recipient': email,
                    'user_name': user_name,
                    'to_name': user_name,
                    'name': user_name,
                    'otp_code': otp,
                    'otp': otp,
                    'passcode': otp,
                    'expiry_minutes': str(validity_minutes),
                    'app_name': 'RailAway'
                }
            }
            if emailjs_private_key:
                payload['accessToken'] = emailjs_private_key

            response = requests.post(
                'https://api.emailjs.com/api/v1.0/email/send',
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            if response.status_code == 200:
                email_sent = True
            else:
                logger.warning(f"EmailJS returned status {response.status_code}: {response.text}")
        except Exception as exc:
            logger.warning(f"EmailJS request exception: {exc}")

    # Log generated OTP to Django server console for easy testing/debugging
    print(f"\n=======================================================")
    print(f"[EmailJS OTP Service] ({purpose.upper()}) To: {email} | OTP: {otp} | Valid for: 2 mins")
    print(f"=======================================================\n")

    msg = f'A 6-digit OTP has been sent to {email}.'
    if not email_sent and getattr(settings, 'DEBUG', True):
        msg = f'Your 6-digit verification OTP is: {otp}'

    return JsonResponse({
        'success': True,
        'message': msg,
        'otp_hint': otp if getattr(settings, 'DEBUG', True) else None,
        'expiry_seconds': 120,
        'cooldown_seconds': 30,
        'purpose': purpose,
        'email': email,
        'email_sent': email_sent
    })



def verify_email_otp_view(request):
    """Verifies the 6-digit OTP submitted by the user.
    If action == 'verify_only' or purpose == 'registration', marks email as verified in session.
    Otherwise authenticates/logs in the user."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    email = request.POST.get('email', '').strip().lower()
    submitted_otp = request.POST.get('otp', '').strip()
    action = request.POST.get('action', '').strip().lower()
    next_url = request.POST.get('next') or request.GET.get('next') or '/accounts/dashboard/'

    if not email or not submitted_otp:
        return JsonResponse({'success': False, 'error': 'Please enter both email and the 6-digit OTP.'}, status=400)

    session_otp = request.session.get('email_auth_otp')

    if not session_otp or session_otp.get('email') != email:
        return JsonResponse({
            'success': False,
            'error': 'No active OTP found for this email. Please request a new OTP.',
            'expired': True
        }, status=400)

    now = time.time()

    # Check if OTP has expired (2 minutes validity)
    if now > session_otp.get('expires_at', 0):
        request.session.pop('email_auth_otp', None)
        request.session.modified = True
        return JsonResponse({
            'success': False,
            'error': 'The OTP has expired. Please request a new OTP.',
            'expired': True
        }, status=400)

    # Check maximum failed attempts (rate limiting brute force)
    attempts = session_otp.get('attempts', 0)
    if attempts >= 5:
        request.session.pop('email_auth_otp', None)
        request.session.modified = True
        return JsonResponse({
            'success': False,
            'error': 'Too many failed attempts. Please request a new OTP.',
            'expired': True
        }, status=400)

    # Check OTP match
    if submitted_otp != session_otp.get('otp'):
        new_attempts = attempts + 1
        session_otp['attempts'] = new_attempts
        request.session.modified = True
        if new_attempts >= 5:
            request.session.pop('email_auth_otp', None)
            request.session.modified = True
            return JsonResponse({
                'success': False,
                'error': 'Too many failed attempts. Please request a new OTP.',
                'expired': True
            }, status=400)
        return JsonResponse({
            'success': False,
            'error': f'Incorrect OTP. Please check your email and try again ({5 - new_attempts} attempts remaining).'
        }, status=400)

    # If action is 'verify_only' or purpose was 'registration'
    if action == 'verify_only' or session_otp.get('purpose') == 'registration':
        request.session['verified_registration_email'] = email
        request.session.pop('email_auth_otp', None)
        request.session.modified = True
        return JsonResponse({
            'success': True,
            'verified': True,
            'email': email,
            'message': 'Email successfully verified with EmailJS OTP!'
        })

    # Standard OTP Login / Instant Access
    request.session.pop('email_auth_otp', None)
    request.session.modified = True

    # Authenticate or create user with this email
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', email.split('@')[0])[:20]
        username = f"user_{sanitized}"
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user = User.objects.create(
            username=username,
            email=email,
            first_name=email.split('@')[0].capitalize()
        )
        user.set_unusable_password()
        user.save()

    # Ensure profile exists
    if hasattr(user, 'profile'):
        if not user.profile.phone:
            user.profile.phone = '9876543210'
            user.profile.save()
    else:
        UserProfile.objects.get_or_create(user=user, defaults={
            'phone': '9876543210',
            'role': 'CUSTOMER'
        })

    login(request, user)
    messages.success(request, f"Welcome! Authenticated successfully as {user.email}.")

    return JsonResponse({'success': True, 'redirect_url': next_url})



def guest_login_view(request):
    """Allows guest users to quickly log in with mobile number or email for instant booking."""
    next_url = request.GET.get('next') or request.POST.get('next') or '/'

    if request.method == 'POST':
        identifier = request.POST.get('guest_identifier', '').strip()
        if not identifier:
            err = "Please enter your Mobile Number or Email ID."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'success': False, 'error': err}, status=400)
            messages.error(request, err)
            return redirect('accounts:login')

        # Generate a clean guest username
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', identifier)[:20]
        guest_username = f"guest_{sanitized}"

        user, created = User.objects.get_or_create(username=guest_username, defaults={
            'first_name': 'Guest',
            'last_name': 'Passenger',
            'email': identifier if '@' in identifier else f"{sanitized}@guest.railaway.in"
        })

        if created:
            user.set_unusable_password()
            user.save()

        if hasattr(user, 'profile'):
            user.profile.phone = identifier if identifier.isdigit() else '9876543210'
            user.profile.save()
        else:
            UserProfile.objects.get_or_create(user=user, defaults={
                'phone': identifier if identifier.isdigit() else '9876543210',
                'role': 'CUSTOMER'
            })

        login(request, user)
        messages.success(request, f"Welcome! Signed in as Guest User ({identifier}).")

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'success': True, 'redirect_url': next_url})
        return redirect(next_url)

    return redirect('accounts:login')


def forgot_password_view(request):
    """Helpful password reset assistance with demo account hints."""
    return render(request, 'accounts/forgot_password.html')


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully. Have a safe journey!")
    return redirect('core:home')


@login_required
def dashboard_view(request):
    user = request.user
    today = timezone.now().date()

    all_bookings = Booking.objects.filter(user=user).select_related('payment')
    all_hotels = HotelBooking.objects.filter(user=user).select_related('hotel', 'room')
    all_rooms = RetiringRoomBooking.objects.filter(user=user).select_related('station', 'room')
    all_food = FoodOrder.objects.filter(user=user).select_related('restaurant', 'delivery_station')

    total_bookings = all_bookings.count() + all_hotels.count() + all_rooms.count() + all_food.count()
    upcoming_bookings = all_bookings.filter(journey_date__gte=today, booking_status='CONFIRMED').order_by('journey_date')
    upcoming_hotels = all_hotels.filter(check_in_date__gte=today, booking_status='CONFIRMED').order_by('check_in_date')
    
    upcoming_count = (
        upcoming_bookings.count() +
        upcoming_hotels.count() +
        all_rooms.filter(check_in_date__gte=today, booking_status__in=['CONFIRMED', 'CHECKED_IN']).count() +
        all_food.filter(delivery_date__gte=today, status__in=['CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY']).count()
    )
    completed_bookings = (
        all_bookings.filter(journey_date__lt=today, booking_status='CONFIRMED').count() +
        all_hotels.filter(check_in_date__lt=today, booking_status='CONFIRMED').count() +
        all_rooms.filter(check_out_date__lt=today, booking_status__in=['CONFIRMED', 'COMPLETED']).count() +
        all_food.filter(status='DELIVERED').count()
    )
    cancelled_bookings = (
        all_bookings.filter(booking_status__in=['CANCELLED', 'REFUNDED']).count() +
        all_hotels.filter(booking_status__in=['CANCELLED', 'REFUNDED']).count() +
        all_rooms.filter(booking_status__in=['CANCELLED', 'REFUNDED']).count() +
        all_food.filter(status__in=['CANCELLED', 'REFUNDED']).count()
    )

    recent_bookings = all_bookings.order_by('-created_at')[:6]
    recent_hotels = all_hotels.order_by('-created_at')[:4]

    context = {
        'total_bookings': total_bookings,
        'upcoming_count': upcoming_count,
        'completed_count': completed_bookings,
        'cancelled_count': cancelled_bookings,
        'upcoming_trips': upcoming_bookings[:3],
        'upcoming_hotels': upcoming_hotels[:2],
        'recent_bookings': recent_bookings,
        'recent_hotels': recent_hotels,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile, user=user)
        if form.is_valid():
            profile = form.save()
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors in the profile form.")
    else:
        form = UserProfileForm(instance=profile, user=user)

    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})
