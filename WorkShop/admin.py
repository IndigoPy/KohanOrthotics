# WorkShop/admin.py

from django.contrib import admin
from .models import Order, WorkshopStatusHistory, Measurement

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_patient_name', 'get_device_type_display', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'device_type', 'created_at')
    search_fields = ('id', 'patient__full_name', 'patient__case_number')
    readonly_fields = ('created_at', 'ready_at', 'delivered_at')

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else '-'
    get_patient_name.short_description = 'نام بیمار'

    def get_patient_case_number(self, obj):
        return obj.patient.case_number if obj.patient else '-'
    get_patient_case_number.short_description = 'شماره پرونده'
