from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.


class Order(models.Model):

    DEVICE_CHOICES = [
        ('insole', 'کفی طبی'),
        ('afo', 'AFO'),
        ('ucbl', 'UCBL'),
        ('brace', 'بریس'),
    ]

    SIDE_CHOICES = [
        ('right', 'راست'),
        ('left', 'چپ'),
        ('both', 'هر دو'),
    ]

    PRIORITY_CHOICES = [
        ('normal', 'عادی'),
        ('urgent', 'فوری'),
    ]

    STATUS_CHOICES = [
        ('registered', 'ثبت شده'),
        ('in_progress', 'در حال ساخت'),
        ('ready', 'آماده'),
        ('delivered', 'تحویل شد'),
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
    patient_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)

    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_CHOICES
    )

    side = models.CharField(
        max_length=10,
        choices=SIDE_CHOICES
    )

    technical_notes = models.TextField(blank=True)

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='registered'
    )

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
