from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'patient_name',
            'phone',
            'device_type',
            'side',
            'technical_notes',
            'priority',
        ]

        widgets = {
            'patient_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام بیمار',
            
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره تماس'
            }),
            'device_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'side': forms.Select(attrs={
                'class': 'form-control'
            }),
            'technical_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
