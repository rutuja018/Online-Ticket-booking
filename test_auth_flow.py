import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'railaway.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

def test_registration_and_auth():
    print("=== Testing Registration & OTP Verification Flow ===")
    client = Client()

    # 1. Clean up test user if exists
    User.objects.filter(username='new_user_123').delete()
    User.objects.filter(email='newuser123@example.com').delete()

    # 2. Test Sending OTP for registration
    send_otp_url = reverse('accounts:send_otp')
    resp = client.post(send_otp_url, {
        'email': 'newuser123@example.com',
        'purpose': 'registration'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.content}"
    data = resp.json()
    assert data.get('success') is True, f"Failed sending OTP: {data}"
    otp_code = data.get('otp_hint')
    print(f" [PASS] OTP Generated and sent for newuser123@example.com (OTP: {otp_code})")

    # 3. Test Verifying OTP (verify_only)
    verify_otp_url = reverse('accounts:verify_otp')
    resp = client.post(verify_otp_url, {
        'email': 'newuser123@example.com',
        'otp': otp_code,
        'action': 'verify_only'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    
    assert resp.status_code == 200
    v_data = resp.json()
    assert v_data.get('success') is True
    assert v_data.get('verified') is True
    print(" [PASS] OTP Verified successfully via AJAX endpoint")

    # 4. Test Submitting Registration Form
    reg_url = reverse('accounts:register')
    resp = client.post(reg_url, {
        'first_name': 'Rutuja',
        'last_name': 'Pawal',
        'username': 'new_user_123',
        'email': 'newuser123@example.com',
        'phone': '9876543210',
        'password': 'Password@123',
        'confirm_password': 'Password@123',
        'email_otp': otp_code
    })

    # Should redirect to dashboard on successful registration
    assert resp.status_code == 302, f"Expected redirect 302, got {resp.status_code}"
    assert resp.url == '/accounts/dashboard/' or resp.url == reverse('accounts:dashboard')
    print(" [PASS] Registration form submitted and account created successfully -> Redirected to dashboard")

    # 5. Verify user created in DB
    user = User.objects.filter(username='new_user_123').first()
    assert user is not None
    assert user.email == 'newuser123@example.com'
    assert user.profile.phone == '9876543210'
    print(f" [PASS] User record and profile verified in DB: {user.username} ({user.email})")

    # 6. Test Direct Registration (without prior AJAX OTP request)
    client.logout()
    User.objects.filter(username='direct_user_456').delete()
    User.objects.filter(email='direct456@example.com').delete()
    
    resp_direct = client.post(reg_url, {
        'first_name': 'Direct',
        'last_name': 'User',
        'username': 'direct_user_456',
        'email': 'direct456@example.com',
        'phone': '9123456780',
        'password': 'Password@123',
        'confirm_password': 'Password@123',
    })
    assert resp_direct.status_code == 302
    assert User.objects.filter(username='direct_user_456').exists()
    print(" [PASS] Direct standard registration works seamlessly without blocking")

    print("\n ALL AUTHENTICATION & REGISTRATION TESTS PASSED! ")

if __name__ == '__main__':
    test_registration_and_auth()
