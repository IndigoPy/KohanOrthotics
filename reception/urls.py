# reception/urls.py

from django.urls import path
from . import views

app_name = 'reception'

urlpatterns = [
    path('', views.reception_dashboard, name='dashboard'),
    path('new-patient/', views.create_patient_and_order, name='new-patient'),
    path('patient/<int:patient_id>/create-order/', views.create_order_for_patient, name='create-order'),
    path('patient/<int:patient_id>/', views.patient_detail, name='patient-detail'),
]