import random
import string
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from railways.models import RailwayStation

def generate_food_order_ref():
    """Generates unique food order reference like FOOD-2026-X9812A"""
    prefix = f"FOOD-{timezone.now().year}-"
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}{suffix}"

class StationRestaurant(models.Model):
    station = models.ForeignKey(RailwayStation, on_delete=models.CASCADE, related_name='restaurants')
    name = models.CharField(max_length=150)
    cuisine = models.CharField(max_length=150, help_text="e.g. North Indian, Thalis, Biryani, Street Food")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=Decimal('4.8'))
    review_count = models.PositiveIntegerField(default=120)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text="Free delivery or nominal charge")
    min_order = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('99.00'))
    is_pure_veg = models.BooleanField(default=False)
    fssai_license = models.CharField(max_length=50, default='FSSAI-10020089123841')
    image_url = models.CharField(max_length=500, blank=True, default='https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-rating', 'name']
        verbose_name = "Station Restaurant"
        verbose_name_plural = "Station Restaurants"

    def __str__(self):
        return f"{self.name} - {self.station.name} ({self.station.code})"


class FoodCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, default='fa-utensils')
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Food Category"
        verbose_name_plural = "Food Categories"

    def __str__(self):
        return self.name


class FoodItem(models.Model):
    restaurant = models.ForeignKey(StationRestaurant, on_delete=models.CASCADE, related_name='menu_items')
    category = models.ForeignKey(FoodCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default='')
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('150.00'))
    is_veg = models.BooleanField(default=True, help_text="True for Veg (Green), False for Non-Veg (Red)")
    is_jain = models.BooleanField(default=False, help_text="Prepared without onion, garlic, or root vegetables")
    is_bestseller = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=Decimal('4.8'))
    preparation_time = models.PositiveIntegerField(default=15, help_text="Minutes needed to prepare")
    image_url = models.CharField(max_length=500, blank=True, default='https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_bestseller', 'price']
        verbose_name = "Food Item"
        verbose_name_plural = "Food Items"

    def __str__(self):
        veg_tag = "[VEG]" if self.is_veg else "[NON-VEG]"
        return f"{veg_tag} {self.name} (₹{self.price}) - {self.restaurant.name}"


class FoodOrder(models.Model):
    STATUS_CHOICES = (
        ('CONFIRMED', 'Order Confirmed'),
        ('PREPARING', 'Preparing in Kitchen'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery at Station'),
        ('DELIVERED', 'Delivered to Seat'),
        ('CANCELLED', 'Cancelled'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid Online'),
        ('CASH_ON_DELIVERY', 'Pay on Delivery (Cash/UPI to Delivery Agent)'),
        ('REFUNDED', 'Refunded'),
    )

    order_ref = models.CharField(max_length=40, unique=True, default=generate_food_order_ref, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='food_orders')
    restaurant = models.ForeignKey(StationRestaurant, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    # Train Journey Delivery Coordinates
    pnr = models.CharField(max_length=30, blank=True, default='', db_index=True)
    train_number = models.CharField(max_length=30)
    train_name = models.CharField(max_length=150)
    delivery_station = models.ForeignKey(RailwayStation, on_delete=models.CASCADE, related_name='food_deliveries')
    delivery_date = models.DateField(default=timezone.now)
    delivery_time_slot = models.CharField(max_length=50, blank=True, default='Estimated on train arrival')
    coach = models.CharField(max_length=10, help_text="e.g. B1, S4, A1")
    seat_number = models.CharField(max_length=10, help_text="e.g. 12, 45")
    
    # Passenger Contact
    passenger_name = models.CharField(max_length=120)
    passenger_phone = models.CharField(max_length=20)
    special_instructions = models.TextField(blank=True, default='')

    # Financials
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    gst = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='CONFIRMED', db_index=True)
    payment_method = models.CharField(max_length=30, default='UPI')
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='PAID')
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Food Order"
        verbose_name_plural = "Food Orders"

    def __str__(self):
        return f"{self.order_ref} - {self.train_number} ({self.coach}-{self.seat_number}) @ {self.delivery_station.code} - ₹{self.total_amount}"

    @property
    def is_active(self):
        return self.status in ['CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY']


class FoodOrderItem(models.Model):
    order = models.ForeignKey(FoodOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(FoodItem, on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=150)
    is_veg = models.BooleanField(default=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    total_price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.item_name} x {self.quantity} (₹{self.total_price})"
