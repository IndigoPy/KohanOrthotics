# reception/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Patient
from WorkShop.forms import OrderCreateForm
from WorkShop.models import Order
from WorkShop.decorators import group_required  
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db import IntegrityError


# reception/views.py

@group_required('Reception')
@login_required
def reception_dashboard(request):
    search_query = request.GET.get('q', '').strip()

    patients = Patient.objects.all().order_by('-created_at')

    if search_query:
        patients = patients.filter(
            Q(full_name__icontains=search_query) |
            Q(case_number__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(medical_notes__icontains=search_query)
        )

    # اضافه کردن اطلاعات اضافی به هر بیمار
    for patient in patients:
        patient.has_order = Order.objects.filter(patient=patient).exists()
        patient.last_order_date = Order.objects.filter(patient=patient).order_by('-created_at').first().created_at if patient.has_order else None

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # درخواست AJAX
        html = render_to_string('reception/partials/patients_list.html', {
            'patients': patients,
            'search_query': search_query,
        }, request=request)
        return JsonResponse({'html': html})

    # درخواست معمولی
    paginator = Paginator(patients, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'patients': page_obj,
        'search_query': search_query,
    }
    return render(request, 'reception/dashboard.html', context)

@group_required('Reception')
@login_required
def create_patient_and_order(request):
    if request.method == 'POST':
        case_number = request.POST.get('case_number')

        # چک کردن تکراری بودن شماره پرونده
        if Patient.objects.filter(case_number=case_number).exists():
            messages.error(request, f'شماره پرونده "{case_number}" قبلاً برای بیمار دیگری ثبت شده است. لطفاً شماره جدیدی وارد کنید.')
            return render(request, 'reception/create_patient.html', {
                'form_data': request.POST  # برای نگه داشتن داده‌های وارد شده
            })

        try:
            patient = Patient(
                case_number=case_number,
                full_name=request.POST['full_name'],
                phone=request.POST['phone'] or None,
                alternative_phone=request.POST['alternative_phone'] or None,
                age=request.POST['age'] or None,
                gender=request.POST['gender'],
                address=request.POST['address'] or None,
                medical_notes=request.POST['medical_notes'] or None,
                created_by=request.user
            )
            patient.save()

            messages.success(request, f'بیمار {patient.full_name} با موفقیت ثبت شد.')
            return redirect('reception:create-order', patient_id=patient.id)

        except IntegrityError:
            messages.error(request, 'خطا در ثبت بیمار. احتمالاً شماره پرونده تکراری است.')
            return render(request, 'reception/create_patient.html', {
                'form_data': request.POST
            })

    # GET request
    return render(request, 'reception/create_patient.html')

@group_required('Reception')
@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    # همه سفارش‌های این بیمار (جدید به قدیمی)
    orders = Order.objects.filter(patient=patient).order_by('-created_at')

    context = {
        'patient': patient,
        'orders': orders,
    }
    return render(request, 'reception/patient_detail.html', context)

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