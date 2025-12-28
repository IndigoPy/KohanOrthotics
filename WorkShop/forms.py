# WorkShop/forms.py

from django import forms
from .models import Order
from reception.models import Patient  # برای جستجو یا انتخاب بیمار اگر لازم بشه


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'patient',           # جدید — به جای patient_name و case_number
            'device_type',
            'side',
            'different_designs',
            'designes_left',     # اگر different_designs=True باشه
            'designes_right',
            'technical_notes_left',
            'technical_notes_right',
            'priority',
            'send_to',
            'status',
        ]

        widgets = {
            'patient': forms.Select(attrs={
                'class': 'form-control select2',
                'id': 'patient-select'
            }),
            'device_type': forms.Select(attrs={'class': 'form-control'}),
            'side': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'send_to': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'different_designs': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # محدود کردن patient به لیست بیماران (یا بعداً با Select2 جستجو کنیم)
        self.fields['patient'].queryset = Patient.objects.all().order_by('-created_at')

        # فیلدهای چپ/راست اختیاری
        self.fields['designes_left'].required = False
        self.fields['designes_right'].required = False
        self.fields['technical_notes_left'].required = False
        self.fields['technical_notes_right'].required = False


# اگر هنوز ReceptionStatusForm داری، اون رو به reception منتقل کن
# یا موقتاً نگه دار، اما بعداً منتقل می‌کنیم
class ReceptionStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            ('registered', 'ثبت شده'),
            ('ordered', 'سفارش داده شده'),
            ('canceled', 'لغو شده'),
            ('contacted', 'تماس گرفته شد'),
            ('patient_notified', 'اطلاع‌رسانی به بیمار'),
            ('patient_arrived', 'بیمار مراجعه کرد'),
            ('delayed', 'تأخیر در مراجعه'),
            ('delivered', 'تحویل داده شده'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="وضعیت جدید"
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'نتیجه تماس، یادداشت هماهنگی و ...'}),
        required=False,
        label="یادداشت پذیرش"
    )