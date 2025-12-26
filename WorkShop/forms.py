from django import forms
from .models import Order


class Select2Widget(forms.SelectMultiple):
    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/select2@4.1.0/dist/css/select2.min.css',)
        }
        js = ('https://cdn.jsdelivr.net/npm/select2@4.1.0/dist/js/select2.min.js',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({'class': 'form-control select2'})



class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'case_number',
            'patient_name',
            'device_type',
            'status',
            'side',
            'technical_notes',
            'designes',
            'different_designs',
            'priority',
            'send_to',
        ]

        widgets = {
            'case_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'شماره پرونده'
            }),
            'patient_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام بیمار',

            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'device_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'side': forms.Select(attrs={
                'class': 'form-control'
            }),
            'technical_notes': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'id': 'technical-notes-select',
            }),
            'designes': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'id': 'designes-select',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'send_to': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
