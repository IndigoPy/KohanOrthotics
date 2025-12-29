from django.db import models

# reception/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Patient(models.Model):
    GENDER_CHOICES = [
        ('male', 'مرد'),
        ('female', 'زن'),
        ('other', 'سایر'),
    ]

    # شماره پرونده منحصر به فرد
    case_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='شماره پرونده'
    )

    full_name = models.CharField(
        max_length=150,
        verbose_name='نام و نام خانوادگی'
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='تلفن همراه'
    )

    alternative_phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='تلفن ثابت یا همراه دیگر'
    )

    age = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='سن'
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        verbose_name='جنسیت'
    )

    address = models.TextField(
        blank=True,
        verbose_name='آدرس'
    )

    medical_notes = models.TextField(
        blank=True,
        verbose_name='یادداشت‌های پزشکی یا عمومی'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ثبت'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_patients',
        verbose_name='ثبت‌کننده'
    )

    PATIENT_TYPE_CHOICES = (
        ('good', 'بیمار خوب'),
        ('medium', 'بیمار متوسط'),
        ('bad', 'بیمار بد'),
    )

    patient_type = models.CharField(max_length=10, choices=PATIENT_TYPE_CHOICES, default='medium', verbose_name='نوع بیمار')
    last_visit = models.DateField(null=True, blank=True, verbose_name='تاریخ آخرین مراجعه')
    
    
    def __str__(self):
        return f"{self.full_name} ({self.case_number})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'بیمار'
        verbose_name_plural = 'بیماران'


# تاریخچه اقدامات و تماس‌های پذیرش (جدا از کارگاه)
class ReceptionStatusHistory(models.Model):
    order = models.ForeignKey('WorkShop.Order', on_delete=models.CASCADE, related_name='reception_history')
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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'اعلان'
        verbose_name_plural = 'اعلان‌ها'

    def __str__(self):
        return self.message[:50]