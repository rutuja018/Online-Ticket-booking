from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import HotelBooking, HotelGuest


class HotelSearchForm(forms.Form):
    city = forms.CharField(required=False, max_length=100)
    check_in = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    check_out = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    rooms = forms.IntegerField(required=False, min_value=1, max_value=10, initial=1)
    guests = forms.IntegerField(required=False, min_value=1, max_value=30, initial=2)
    star_rating = forms.CharField(required=False)
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    amenities = forms.CharField(required=False)
    sort_by = forms.CharField(required=False, initial='recommended')


class HotelBookingForm(forms.ModelForm):
    check_in_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'id': 'checkInInput'}),
        required=True
    )
    check_out_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'id': 'checkOutInput'}),
        required=True
    )
    room_count = forms.IntegerField(
        min_value=1, max_value=10, initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'id': 'roomCountInput'}),
        required=True
    )
    guest_count = forms.IntegerField(
        min_value=1, max_value=20, initial=2,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'id': 'guestCountInput'}),
        required=True
    )
    primary_guest_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Rahul Sharma'}),
        required=True
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'e.g. rahul@example.com'}),
        required=True
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 9876543210'}),
        required=True
    )
    special_requests = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'rows': 3,
            'placeholder': 'e.g. Late check-in, quiet room on upper floor, twin beds preference (subject to hotel availability)'
        }),
        required=False
    )
    promo_code = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter Promo Code (e.g. TIRANGA100)'})
    )

    class Meta:
        model = HotelBooking
        fields = [
            'primary_guest_name', 'email', 'phone', 'check_in_date',
            'check_out_date', 'room_count', 'guest_count',
            'special_requests', 'promo_code'
        ]

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in_date')
        check_out = cleaned_data.get('check_out_date')
        today = timezone.now().date()

        if check_in:
            if check_in < today:
                self.add_error('check_in_date', "Check-in date cannot be in the past.")

        if check_in and check_out:
            if check_out <= check_in:
                self.add_error('check_out_date', "Check-out date must be strictly after check-in date.")

        return cleaned_data
