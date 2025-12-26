from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.


class Order(models.Model):

    DEVICE_CHOICES = [
        ('CNC insole', 'کفی طبی CNC'),
        ('Functional insole', 'کفی طبی فانکشنال'),
        ('Pu insole', 'کفی طبی Pu'),
        ('SandalA', 'صندل آرامو'),
        ('SandalB', 'صندل بیات'),
        ('SandalO', 'صندل ارسی'),
    ]

    SIDE_CHOICES = [
        ('both', 'هر دو'),
        ('right', 'راست'),
        ('left', 'چپ'),
    ]

    PRIORITY_CHOICES = [
        ('normal', 'عادی'),
        ('urgent', 'اورژانسی'),
    ]

    STATUS_CHOICES = [
        ('registered', 'ثبت شده'),
        ("ordered", "سفارش داده شده"),
        ('received', 'دریافت شده از تأمین‌کننده'),
        ('in_progress', 'در حال ساخت'),
        ('ready', 'آماده تحویل'),
        ('canceled', 'لغو شده'),
        ('delivered', 'تحویل داده شده'),
    ]

    SEND_TO_CHOICES = [
        ('workshop', 'کارگاه'),
        ('examiner', 'اتاق معاینه'),
    ]
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_orders',
        verbose_name='ثبت‌کننده'
    )

    ready_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ready_orders',
        verbose_name='آماده‌کننده'
    )
    case_number = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='شماره پرونده')

    patient_name = models.CharField(max_length=100, verbose_name='نام بیمار')

    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_CHOICES,
        verbose_name='نوع ارتوز'
    )

    side = models.CharField(
        max_length=10,
        choices=SIDE_CHOICES,
        verbose_name='اندام مورد نظر'
    )

    technical_notes = models.CharField(
        blank=False, verbose_name='خلاصه پرونده', editable=True,)

    designes = models.CharField(
        blank=False, verbose_name='طراحی‌ها', default='', editable=True, )

    different_designs = models.BooleanField(
        default=False, verbose_name="آیا دو پا متفاوت هستند؟")
    
    different_technical_notes = models.BooleanField(
        default=False,
        verbose_name="آیا خلاصه پرونده برای پای چپ و راست متفاوت است؟"
    )
    
    designes_left = models.TextField(blank=True, null=True)
    designes_right = models.TextField(blank=True, null=True)
    technical_notes_left = models.TextField(blank=True, null=True)
    technical_notes_right = models.TextField(blank=True, null=True)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name='اولویت'
    )

    send_to = models.CharField(
        max_length=60,
        choices=SEND_TO_CHOICES,
        default='workshop',
        verbose_name='ارسال به'
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='registered', verbose_name='وضعیت')

    delivered_at = models.DateTimeField(null=True, blank=True)
    delivered_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='delivered_orders'
    )
    workshop_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    ready_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.patient_name} - {self.get_device_type_display()}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        'Order', on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, verbose_name="توضیحات کارگاه")  # اضافه شد
    
class Measurement(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='measurements')
    parameter = models.CharField(max_length=100, verbose_name="پارامتر")
    right_foot_size = models.CharField(
        max_length=50, verbose_name="اندازه پای راست")
    left_foot_size = models.CharField(
        max_length=50, verbose_name="اندازه پای چپ")
