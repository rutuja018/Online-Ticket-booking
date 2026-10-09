import time
from django.test import TestCase, Client
from django.contrib.auth.models import User
from accounts.models import UserProfile


class EmailJsOtpAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.email = "traveler@example.com"

    def test_send_otp_success(self):
        """Test sending OTP generates a 6-digit code with 2-minute validity."""
        response = self.client.post('/accounts/send-otp/', {'email': self.email})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['expiry_seconds'], 120)
        self.assertEqual(data['cooldown_seconds'], 30)

        # Verify session storage
        session = self.client.session
        self.assertIn('email_auth_otp', session)
        otp_data = session['email_auth_otp']
        self.assertEqual(len(otp_data['otp']), 6)
        self.assertTrue(otp_data['otp'].isdigit())
        self.assertEqual(otp_data['email'], self.email)
        self.assertEqual(otp_data['attempts'], 0)
        self.assertGreater(otp_data['expires_at'], time.time())

    def test_send_otp_invalid_email(self):
        """Test sending OTP with invalid email returns 400 error."""
        response = self.client.post('/accounts/send-otp/', {'email': 'invalid-email-format'})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('valid email', data['error'].lower())

    def test_send_otp_cooldown_rate_limit(self):
        """Test sending OTP within cooldown period (30s) is rate limited (429)."""
        # First request
        r1 = self.client.post('/accounts/send-otp/', {'email': self.email})
        self.assertEqual(r1.status_code, 200)

        # Immediate second request
        r2 = self.client.post('/accounts/send-otp/', {'email': self.email})
        self.assertEqual(r2.status_code, 429)
        data = r2.json()
        self.assertFalse(data['success'])
        self.assertIn('wait', data['error'].lower())

    def test_verify_otp_success_new_user(self):
        """Test verifying valid OTP creates a new user, profile, and logs in."""
        self.client.post('/accounts/send-otp/', {'email': self.email})
        session = self.client.session
        otp = session['email_auth_otp']['otp']

        verify_response = self.client.post('/accounts/verify-otp/', {
            'email': self.email,
            'otp': otp,
            'next': '/accounts/dashboard/'
        })
        self.assertEqual(verify_response.status_code, 200)
        data = verify_response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['redirect_url'], '/accounts/dashboard/')

        # User is created & authenticated
        user = User.objects.filter(email=self.email).first()
        self.assertIsNotNone(user)
        self.assertTrue(hasattr(user, 'profile'))

        # Session OTP should be cleared
        session = self.client.session
        self.assertNotIn('email_auth_otp', session)

    def test_verify_otp_success_existing_user(self):
        """Test verifying valid OTP logs into existing user account."""
        user = User.objects.create_user(
            username='existing_customer',
            email=self.email,
            first_name='Existing'
        )
        user.profile.phone = '9876543210'
        user.profile.save()

        self.client.post('/accounts/send-otp/', {'email': self.email})
        session = self.client.session
        otp = session['email_auth_otp']['otp']

        verify_response = self.client.post('/accounts/verify-otp/', {
            'email': self.email,
            'otp': otp,
            'next': '/bookings/history/'
        })
        self.assertEqual(verify_response.status_code, 200)
        self.assertTrue(verify_response.json()['success'])
        self.assertEqual(verify_response.json()['redirect_url'], '/bookings/history/')

    def test_verify_otp_incorrect(self):
        """Test incorrect OTP is rejected with error and increments attempts."""
        self.client.post('/accounts/send-otp/', {'email': self.email})
        session = self.client.session
        real_otp = session['email_auth_otp']['otp']
        fake_otp = '000000' if real_otp != '000000' else '111111'

        verify_response = self.client.post('/accounts/verify-otp/', {
            'email': self.email,
            'otp': fake_otp
        })
        self.assertEqual(verify_response.status_code, 400)
        data = verify_response.json()
        self.assertFalse(data['success'])
        self.assertIn('incorrect', data['error'].lower())

        # Check attempt count incremented
        session = self.client.session
        self.assertEqual(session['email_auth_otp']['attempts'], 1)

    def test_verify_otp_expired(self):
        """Test expired OTP (> 2 mins) is rejected and marked as expired."""
        self.client.post('/accounts/send-otp/', {'email': self.email})
        session = self.client.session
        otp = session['email_auth_otp']['otp']

        # Force expire by manipulating expires_at in session
        otp_data = session['email_auth_otp']
        otp_data['expires_at'] = time.time() - 10
        session['email_auth_otp'] = otp_data
        session.save()

        verify_response = self.client.post('/accounts/verify-otp/', {
            'email': self.email,
            'otp': otp
        })
        self.assertEqual(verify_response.status_code, 400)
        data = verify_response.json()
        self.assertFalse(data['success'])
        self.assertTrue(data.get('expired'))
        self.assertIn('expired', data['error'].lower())

        # Session OTP is cleared on expiry
        session = self.client.session
        self.assertNotIn('email_auth_otp', session)

    def test_verify_otp_max_failed_attempts(self):
        """Test OTP is invalidated after 5 consecutive failed attempts."""
        self.client.post('/accounts/send-otp/', {'email': self.email})
        session = self.client.session
        real_otp = session['email_auth_otp']['otp']
        fake_otp = '000000' if real_otp != '000000' else '111111'

        for i in range(4):
            r = self.client.post('/accounts/verify-otp/', {'email': self.email, 'otp': fake_otp})
            self.assertEqual(r.status_code, 400)

        # 5th failed attempt should trigger lockout
        r5 = self.client.post('/accounts/verify-otp/', {'email': self.email, 'otp': fake_otp})
        self.assertEqual(r5.status_code, 400)
        self.assertIn('too many failed attempts', r5.json()['error'].lower())

        # Session OTP is now wiped
        session = self.client.session
        self.assertNotIn('email_auth_otp', session)

    def test_resend_otp_invalidates_previous_otp(self):
        """Test requesting a new OTP after cooldown invalidates previous OTP."""
        self.client.post('/accounts/send-otp/', {'email': self.email})
        session = self.client.session
        old_otp = session['email_auth_otp']['otp']

        # Simulate cooldown elapsed
        otp_data = session['email_auth_otp']
        otp_data['last_sent_at'] = time.time() - 35
        session['email_auth_otp'] = otp_data
        session.save()

        # Request new OTP
        self.client.post('/accounts/send-otp/', {'email': self.email})
        session = self.client.session
        new_otp = session['email_auth_otp']['otp']

        # Old OTP must fail
        if old_otp != new_otp:
            r = self.client.post('/accounts/verify-otp/', {'email': self.email, 'otp': old_otp})
            self.assertEqual(r.status_code, 400)

        # New OTP must succeed
        r_new = self.client.post('/accounts/verify-otp/', {'email': self.email, 'otp': new_otp})
        self.assertEqual(r_new.status_code, 200)
        self.assertTrue(r_new.json()['success'])

    def test_send_otp_registration_existing_email_fails(self):
        """Test sending registration OTP fails if account already exists."""
        User.objects.create_user(username='existing_user', email=self.email, password='testpassword123')
        response = self.client.post('/accounts/send-otp/', {'email': self.email, 'purpose': 'registration'})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('already exists', data['error'].lower())

    def test_registration_blocked_without_verified_otp(self):
        """Test user registration is blocked if email OTP verification was not completed."""
        response = self.client.post('/accounts/register/', {
            'first_name': 'Rutuja',
            'last_name': 'Pawal',
            'username': 'rutuja_p',
            'phone': '9876543210',
            'email': 'new.user@example.com',
            'email_otp': '',
            'password': 'StrongPassword@123',
            'confirm_password': 'StrongPassword@123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'verify your email address')
        self.assertFalse(User.objects.filter(username='rutuja_p').exists())


    def test_registration_succeeds_with_verified_email_otp(self):
        """Test full user registration succeeds once email OTP is verified."""
        reg_email = 'new.user@example.com'
        # 1. Send registration OTP
        self.client.post('/accounts/send-otp/', {'email': reg_email, 'purpose': 'registration'})
        session = self.client.session
        otp = session['email_auth_otp']['otp']

        # 2. Verify OTP for registration
        verify_r = self.client.post('/accounts/verify-otp/', {
            'email': reg_email,
            'otp': otp,
            'action': 'verify_only'
        })
        self.assertEqual(verify_r.status_code, 200)
        self.assertTrue(verify_r.json()['verified'])

        # 3. Submit registration form
        reg_r = self.client.post('/accounts/register/', {
            'first_name': 'Rutuja',
            'last_name': 'Pawal',
            'username': 'rutuja_p',
            'phone': '9876543210',
            'email': reg_email,
            'password': 'StrongPassword@123',
            'confirm_password': 'StrongPassword@123'
        })
        self.assertEqual(reg_r.status_code, 302)  # Redirects to dashboard
        self.assertTrue(User.objects.filter(username='rutuja_p').exists())

    def test_registration_blocked_if_email_altered_after_otp(self):
        """Test user cannot verify OTP for one email and register with a different email."""
        reg_email = 'verified.email@example.com'
        different_email = 'attacker@example.com'

        self.client.post('/accounts/send-otp/', {'email': reg_email, 'purpose': 'registration'})
        otp = self.client.session['email_auth_otp']['otp']
        self.client.post('/accounts/verify-otp/', {'email': reg_email, 'otp': otp, 'action': 'verify_only'})

        # Try submitting with a different email
        response = self.client.post('/accounts/register/', {
            'first_name': 'Rutuja',
            'last_name': 'Pawal',
            'username': 'rutuja_p2',
            'phone': '9876543210',
            'email': different_email,
            'email_otp': '',
            'password': 'StrongPassword@123',
            'confirm_password': 'StrongPassword@123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'verify your email address')
        self.assertFalse(User.objects.filter(username='rutuja_p2').exists())


