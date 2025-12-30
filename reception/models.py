from django.db import models

# reception/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# reception/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Patient(models.Model):
    case_number = models.CharField(max_length=50, unique=True, verbose_name="شماره پرونده")
    full_name = models.CharField(max_length=200, verbose_name="نام و نام خانوادگی")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="تلفن همراه اصلی")
    alternative_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="تلفن همراه دوم")
    national_id = models.CharField(max_length=10, blank=True, null=True, verbose_name="کد ملی")
    birth_date = models.CharField(max_length=10, blank=True, null=True, verbose_name="تاریخ تولد (شمسی)")
    age = models.PositiveIntegerField(blank=True, null=True, verbose_name="سن")
    gender = models.CharField(max_length=10, choices=[('male', 'مرد'), ('female', 'زن'), ('other', 'سایر')], blank=True, verbose_name="جنسیت")
    foot_size = models.CharField(max_length=10, blank=True, null=True, verbose_name="سایز پا")
    referrer = models.CharField(max_length=200, blank=True, null=True, verbose_name="معرف")
    attached_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="پیوست به بیمار دیگر")
    visit_reason = models.TextField(blank=True, null=True, verbose_name="علت مراجعه")
    underlying_diseases = models.TextField(blank=True, null=True, verbose_name="بیماری‌های زمینه‌ای")
    orthotic_history = models.TextField(blank=True, null=True, verbose_name="سوابق استفاده از ارتوتیک")
    short_address = models.CharField(max_length=200, blank=True, null=True, verbose_name="آدرس مختصر")
    reception_notes = models.TextField(blank=True, null=True, verbose_name="یادداشت پذیرش")
    photo = models.ImageField(upload_to='patients/photos/', blank=True, null=True, verbose_name="عکس بیمار")
    admission_date = models.DateTimeField(default=timezone.now, verbose_name="تاریخ پذیرش")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ثبت شده توسط")

    def __str__(self):
        return f"{self.full_name} ({self.case_number})"

    class Meta:
        verbose_name = "بیمار"
        verbose_name_plural = "بیماران"
        ordering = ['-created_at']

# مدل Document اگر نداری
class Document(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents', null= True, blank=True, verbose_name="بیمار")
    title = models.CharField(max_length=200, blank=True, verbose_name="عنوان مدرک")
    file = models.FileField(upload_to='patients/documents/%Y/%m/', verbose_name="فایل")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ آپلود")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="آپلود شده توسط")

    def __str__(self):
        return self.title or self.file.name

    class Meta:
        verbose_name = "مدرک"
        verbose_name_plural = "مدارک"
        ordering = ['-uploaded_at']


# تاریخچه اقدامات و تماس‌های پذیرش (جدا از کارگاه)
class ReceptionStatusHistory(models.Model):
    order = models.ForeignKey(
        'WorkShop.Order', on_delete=models.CASCADE, related_name='reception_history')
    status = models.CharField(
        max_length=20,
        choices=[
            ('registered', 'ثبت شده'),
            ('ordered', 'سفارش داده شده'),
            ('canceled', 'لغو شده'),
            ('contacted', 'تماس گرفته شد'),
            ('patient_notified', 'اطلاع‌رسانی به بیمار'),
            ('patient_arrived', 'بیمار مراجعه کرد'),
            ('delayed', 'تأخیر در مراجعه'),
            ('delivered', 'تحویل داده شده'),
            # می‌تونی بعداً بیشتر اضافه کنی
        ],
        verbose_name='وضعیت'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='یادداشت پذیرش / نتیجه تماس'
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='تغییر توسط'
    )

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'تاریخچه اقدامات پذیرش'
        verbose_name_plural = 'تاریخچه اقدامات پذیرش'

    def __str__(self):
        return f"{self.order} - {self.get_status_display()} ({self.changed_at.date()})"

    # reception/models.py - در انتهای فایل اضافه کن


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='کاربر'
    )
    message = models.TextField(verbose_name='پیام')
    url = models.URLField(blank=True, null=True, verbose_name='لینک')
    is_read = models.BooleanField(default=False, verbose_name='خوانده شده')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='زمان ایجاد')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'اعلان'
        verbose_name_plural = 'اعلان‌ها'

    def __str__(self):
        return self.message[:50]
