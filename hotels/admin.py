from django.contrib import admin
from .models import HotelAmenity, Hotel, HotelImage, Room, HotelBooking, HotelGuest, HotelReview


class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 1
    fields = ('image_url', 'caption', 'is_primary', 'display_order')


class RoomInline(admin.StackedInline):
    model = Room
    extra = 1
    fields = (
        ('room_type', 'bed_type'),
        ('price_per_night', 'discounted_price'),
        ('total_rooms', 'available_rooms'),
        ('max_adults', 'max_children', 'max_occupancy'),
        ('has_free_breakfast', 'has_free_cancellation', 'has_ac', 'has_wifi', 'has_balcony'),
        'image_url', 'custom_facilities', 'is_active'
    )


@admin.register(HotelAmenity)
class HotelAmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_class', 'is_featured')
    list_filter = ('is_featured',)
    search_fields = ('name',)
    list_editable = ('is_featured',)


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'city', 'state', 'hotel_type', 'star_rating',
        'guest_rating', 'review_count', 'is_featured', 'is_active'
    )
    list_filter = ('star_rating', 'hotel_type', 'is_featured', 'is_active', 'city', 'state')
    search_fields = ('name', 'city', 'state', 'address', 'landmark')
    prepopulated_fields = {'slug': ('name', 'city')}
    filter_horizontal = ('amenities',)
    list_editable = ('is_featured', 'is_active')
    inlines = [HotelImageInline, RoomInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'tagline', 'hotel_type', 'star_rating', 'guest_rating', 'review_count', 'is_featured', 'is_active')
        }),
        ('Location Details', {
            'fields': ('city', 'state', 'address', 'pincode', 'landmark')
        }),
        ('Media & Description', {
            'fields': ('main_image', 'description')
        }),
        ('Amenities & Features', {
            'fields': ('amenities',)
        }),
        ('Policies & Rules', {
            'fields': ('check_in_time', 'check_out_time', 'cancellation_policy', 'house_rules')
        }),
    )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'room_type', 'hotel', 'price_per_night', 'discounted_price',
        'total_rooms', 'available_rooms', 'max_occupancy', 'is_active'
    )
    list_filter = ('is_active', 'has_free_breakfast', 'has_ac', 'hotel__city')
    search_fields = ('room_type', 'hotel__name', 'hotel__city')
    list_editable = ('price_per_night', 'available_rooms', 'is_active')


class HotelGuestInline(admin.TabularInline):
    model = HotelGuest
    extra = 0
    fields = ('full_name', 'age', 'gender', 'is_primary')


@admin.register(HotelBooking)
class HotelBookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_reference', 'primary_guest_name', 'hotel', 'room',
        'check_in_date', 'check_out_date', 'nights', 'room_count',
        'total_amount', 'booking_status', 'payment_status', 'created_at'
    )
    list_filter = ('booking_status', 'payment_status', 'check_in_date', 'hotel__city')
    search_fields = (
        'booking_reference', 'primary_guest_name', 'email', 'phone',
        'hotel__name', 'promo_code'
    )
    readonly_fields = ('booking_reference', 'created_at', 'updated_at')
    inlines = [HotelGuestInline]
    actions = ['mark_confirmed', 'mark_cancelled']

    @admin.action(description="Mark selected bookings as Confirmed")
    def mark_confirmed(self, request, queryset):
        queryset.update(booking_status='CONFIRMED', payment_status='SUCCESS')
        self.message_user(request, "Selected bookings marked as Confirmed.")

    @admin.action(description="Cancel selected bookings & release room inventory")
    def mark_cancelled(self, request, queryset):
        for b in queryset:
            b.cancel_and_release_rooms(reason="Admin panel bulk cancellation")
        self.message_user(request, "Selected bookings cancelled and rooms released back to inventory.")


@admin.register(HotelGuest)
class HotelGuestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'booking', 'gender', 'age', 'is_primary')
    search_fields = ('full_name', 'booking__booking_reference')


@admin.register(HotelReview)
class HotelReviewAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'user', 'rating', 'title', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('hotel__name', 'user__username', 'title', 'comment')
