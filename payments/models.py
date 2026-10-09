import random
import string
from django.db import models
from django.utils import timezone
from bookings.models import Booking

def generate_transaction_id():
    """Generates a realistic transaction ID format like TXN-2026-98127394"""
    rand_digits = ''.join(random.choices(string.digits, k=8))
    return f"TXN-{timezone.now().year}-{rand_digits}"

class Payment(models.Model):
    METHOD_CHOICES = (
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('UPI', 'UPI / QR Payment'),
        ('NET_BANKING', 'Internet Banking'),
        ('WALLET', 'Digital Wallet'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    )

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    transaction_id = models.CharField(max_length=50, unique=True, default=generate_transaction_id, db_index=True)
    payment_method = models.CharField(max_length=30, choices=METHOD_CHOICES, default='CREDIT_CARD')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    gateway_response = models.TextField(blank=True, null=True)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_network = models.CharField(max_length=30, blank=True, null=True, help_text="e.g. Visa, Mastercard, RuPay")
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"

    def __str__(self):
        return f"{self.transaction_id} - ₹{self.amount} ({self.payment_status}) for PNR {self.booking.pnr}"
