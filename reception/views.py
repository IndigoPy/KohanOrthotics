# reception/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Patient
from WorkShop.forms import OrderCreateForm
from WorkShop.models import Order
from WorkShop.decorators import group_required  # اگر داری، وگرنه از WorkShop import کن یا خودت بساز

@group_required('Reception')
@login_required
def reception_dashboard(request):
    patients = None
    search_query = None

    if request.GET.get('q'):
        search_query = request.GET.get('q')
        patients = Patient.objects.filter(
            Q(full_name__icontains=search_query) |
            Q(case_number__icontains=search_query) |
            Q(phone__icontains=search_query)
        ).order_by('-created_at')

        # صفحه‌بندی نتایج جستجو
        paginator = Paginator(patients, 15)
        page_number = request.GET.get('page')
        patients = paginator.get_page(page_number)

    context = {
        'search_query': search_query,
        'patients': patients,
    }
    return render(request, 'reception/dashboard.html', context)


@group_required('Reception')
@login_required
def create_patient_and_order(request):
    if request.method == 'POST':
        # اول بیمار رو بساز
        patient = Patient(
            case_number=request.POST['case_number'],
            full_name=request.POST['full_name'],
            phone=request.POST['phone'] or None,
            alternative_phone=request.POST['alternative_phone'] or None,
            age=request.POST['age'] or None,
            gender=request.POST['gender'],
            address=request.POST['address'],
            medical_notes=request.POST['medical_notes'],
            created_by=request.user
        )
        patient.save()

        messages.success(request, f'بیمار {patient.full_name} با موفقیت ثبت شد.')
        return redirect('reception-create-order', patient_id=patient.id)

    return render(request, 'reception/create_patient.html')


@group_required('Reception')
@login_required
def create_order_for_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.patient = patient
            order.created_by = request.user
            order.save()
            messages.success(request, f'سفارش برای {patient.full_name} با موفقیت ثبت شد.')
            return redirect('reception-ready')  # یا هر صفحه‌ای که لیست آماده‌ها هست
    else:
        form = OrderCreateForm(initial={'patient': patient})

    context = {
        'form': form,
        'patient': patient,
    }
    return render(request, 'reception/create_order.html', context)