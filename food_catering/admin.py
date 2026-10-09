from django.contrib import admin
from .models import StationRestaurant, FoodCategory, FoodItem, FoodOrder, FoodOrderItem

class FoodOrderItemInline(admin.TabularInline):
    model = FoodOrderItem
    extra = 0

@admin.register(StationRestaurant)
class StationRestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'station', 'cuisine', 'rating', 'is_pure_veg', 'is_active')
    list_filter = ('is_pure_veg', 'is_active', 'station__city')
    search_fields = ('name', 'station__name', 'station__code', 'cuisine')

@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'display_order')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'category', 'price', 'is_veg', 'is_jain', 'is_bestseller', 'is_available')
    list_filter = ('is_veg', 'is_jain', 'is_bestseller', 'is_available', 'category')
    search_fields = ('name', 'restaurant__name', 'description')

@admin.register(FoodOrder)
class FoodOrderAdmin(admin.ModelAdmin):
    list_display = ('order_ref', 'passenger_name', 'train_number', 'coach', 'seat_number', 'delivery_station', 'total_amount', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'delivery_station')
    search_fields = ('order_ref', 'pnr', 'passenger_name', 'passenger_phone', 'train_number')
    inlines = [FoodOrderItemInline]
