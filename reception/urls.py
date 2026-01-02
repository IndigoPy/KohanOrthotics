# reception/urls.py

from django.urls import path
from . import views

app_name = 'reception'

urlpatterns = [
    path('', views.reception_dashboard, name='dashboard'),
    path('new-patient/', views.create_patient_and_order, name='new-patient'),
    path('patient/<int:patient_id>/create-order/',
         views.create_order_for_patient, name='create-order'),
    path('patient/<int:patient_id>/', views.patient_detail, name='patient-detail'),
    path('search-patients-ajax/', views.search_patients_ajax,name='search-patients-ajax'),
    path('patient/<int:patient_id>/edit/', views.edit_patient, name='edit-patient'),
    path('patient/<int:patient_id>/print/', views.print_patient, name='print-patient'),
    path('patient/<int:patient_id>/create-order/', views.create_order_for_patient, name='create-order'),
    path('patient/<int:patient_id>/exam/create/', views.create_examination, name='create-exam'),
    path('exam/<int:exam_id>/edit/', views.edit_examination, name='edit-exam'),
    path('exam/<int:exam_id>/delete/', views.delete_examination, name='delete-exam'),
]
