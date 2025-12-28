# workshop/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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
        ('ordered', 'سفارش داده شده'),
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

    # لینک به بیمار (از اپ reception)
    patient = models.ForeignKey(
        'reception.Patient',  # اپ reception مدل Patient رو داره
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='بیمار'
    )

    # اطلاعات سفارش
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

    different_designs = models.BooleanField(
        default=False,
        verbose_name="آیا دو پا متفاوت هستند؟"
    )

    designes_left = models.TextField(blank=True, null=True, verbose_name='طراحی‌ها - پای چپ')
    designes_right = models.TextField(blank=True, null=True, verbose_name='طراحی‌ها - پای راست')

    technical_notes_left = models.TextField(blank=True, null=True, verbose_name='خلاصه پرونده - پای چپ')
    technical_notes_right = models.TextField(blank=True, null=True, verbose_name='خلاصه پرونده - پای راست')

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
        max_length=20,
        choices=STATUS_CHOICES,
        default='registered',
        verbose_name='وضعیت'
    )

    # کاربران مرتبط
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

    delivered_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='delivered_orders',
        verbose_name='تحویل‌دهنده'
    )

    # زمان‌بندی
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان تحویل')
    ready_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان آماده‌سازی')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')

    # یادداشت کارگاه
    workshop_notes = models.TextField(blank=True, verbose_name='یادداشت‌های کارگاه')

    def __str__(self):
        return f"#{self.id} - {self.patient.full_name} - {self.get_device_type_display()}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارش‌ها'


# تاریخچه تغییرات وضعیت توسط کارگاه
class WorkshopStatusHistory(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='workshop_history'
    )
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True, verbose_name="توضیحات کارگاه")

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'تاریخچه وضعیت کارگاه'
        verbose_name_plural = 'تاریخچه وضعیت‌های کارگاه'

    def __str__(self):
        return f"{self.order} → {self.get_status_display()} ({self.changed_at})"


# اندازه‌های ثبت شده برای هر سفارش
class Measurement(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='measurements'
    )
    parameter = models.CharField(max_length=100, verbose_name="پارامتر")
    right_foot_size = models.CharField(max_length=50, blank=True, null=True, verbose_name="اندازه پای راست")
    left_foot_size = models.CharField(max_length=50, blank=True, null=True, verbose_name="اندازه پای چپ")

    def __str__(self):
        return f"{self.parameter} - {self.order}"

    class Meta:
        verbose_name = 'اندازه‌گیری'
        verbose_name_plural = 'اندازه‌گیری‌ها'