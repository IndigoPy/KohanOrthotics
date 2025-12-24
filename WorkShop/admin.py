from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'patient_name',
        'device_type',
        'status',
        'created_by',
        'ready_by',
        'created_at',
    )


    list_filter = (
        'status',
        'priority',
        'device_type'
    )

    search_fields = (
        'patient_name',
        'phone'
    )
