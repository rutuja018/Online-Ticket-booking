from django import forms
from .models import ContactInquiry


class ContactInquiryForm(forms.ModelForm):
    name = forms.CharField(
        max_length=120,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Your full name',
            'id': 'contactName',
            'autocomplete': 'name',
        }),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'you@example.com',
            'id': 'contactEmail',
            'autocomplete': 'email',
        }),
    )
    message = forms.CharField(
        required=True,
        min_length=10,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'placeholder': 'How can we help with your booking, PNR, or stay?',
            'id': 'contactMessage',
            'rows': 6,
        }),
    )

    class Meta:
        model = ContactInquiry
        fields = ['name', 'email', 'message']
