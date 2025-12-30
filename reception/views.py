# reception/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Patient, Document
from WorkShop.forms import OrderCreateForm
from WorkShop.models import Order
from WorkShop.decorators import group_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db import IntegrityError
from django.utils import timezone
from jdatetime import date as jdate

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
        patient.last_order_date = Order.objects.filter(patient=patient).order_by(
            '-created_at').first().created_at if patient.has_order else None

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
        if Patient.objects.filter(case_number=case_number).exists():
            messages.error(request, 'شماره پرونده تکراری است.')
            return render(request, 'reception/create_patient.html', {'suggested_case_number': case_number})

        patient = Patient(
            case_number=case_number,
            full_name=request.POST.get('full_name'),
            phone=request.POST.get('phone'),
            alternative_phone=request.POST.get('alternative_phone'),
            national_id=request.POST.get('national_id'),
            birth_date=request.POST.get('birth_date'),
            age=request.POST.get('age'),
            gender=request.POST.get('gender'),
            foot_size=request.POST.get('foot_size'),
            referrer=request.POST.get('referrer'),
            attached_to_id=request.POST.get('attached_to'),
            visit_reason=request.POST.get('visit_reason'),
            underlying_diseases=','.join(request.POST.getlist('underlying_diseases')),
            orthotic_history=','.join(request.POST.getlist('orthotic_history')),
            short_address=request.POST.get('short_address'),
            reception_notes=request.POST.get('reception_notes'),
            photo=request.FILES.get('photo'),
            admission_date=timezone.now(),
            created_at=timezone.now(),
            created_by=request.user,
        )
        patient.save()

        # ذخیره مدارک
        documents = request.FILES.getlist('documents')
        for doc in documents:
            Document.objects.create(
                patient=patient,
                title=doc.name,
                file=doc,
                uploaded_by=request.user
            )

        messages.success(request, 'بیمار با موفقیت ثبت شد.')
        return redirect('reception:patient-detail', patient_id=patient.id)

    # GET - محاسبه شماره پیشنهادی
    today = jdate.today()
    prefix = f"{today.year}-{today.month:02d}"

    last_patient = Patient.objects.filter(case_number__startswith=prefix).order_by('-case_number').first()
    if last_patient:
        try:
            last_num = int(last_patient.case_number.split('-')[-1])
            next_num = last_num + 1
        except:
            next_num = 1000
    else:
        next_num = 1000

    suggested_case_number = f"{prefix}-{next_num:04d}"

    return render(request, 'reception/create_patient.html', {'suggested_case_number': suggested_case_number})


@group_required('Reception')
@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    orders = Order.objects.filter(patient=patient).order_by('-created_at')
    attached_patients = Patient.objects.filter(attached_to=patient)
    documents = patient.documents.all()  # از related_name='documents'

    context = {
        'patient': patient,
        'orders': orders,
        'attached_patients': attached_patients,
        'documents': documents,
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
            messages.success(
                request, f'سفارش برای {patient.full_name} با موفقیت ثبت شد.')
            # یا هر صفحه‌ای که لیست آماده‌ها هست
            return redirect('reception-ready')
    else:
        form = OrderCreateForm(initial={'patient': patient})

    context = {
        'form': form,
        'patient': patient,
    }
    return render(request, 'reception/create_order.html', context)

def edit_patient(request):
    # اینجا باید منطق ویرایش بیمار را اضافه کنی
    pass

def print_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    context = {
        'patient': patient,
    }
    return render(request, 'reception/print_patient.html', context)

def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    orders = Order.objects.filter(patient=patient).order_by('-created_at')
    attached = Patient.objects.filter(attached_to=patient)
    patient.attached_patients = attached  # برای تمپلیت

    context = {
        'patient': patient,
        'orders': orders,
    }
    return render(request, 'reception/patient_detail.html', context)

def search_patients_ajax(request):
    q = request.GET.get('q', '')
    patients = Patient.objects.filter(
        Q(full_name__icontains=q) | Q(case_number__icontains=q)
    )[:20]
    return JsonResponse([{'id': p.id, 'full_name': p.full_name, 'case_number': p.case_number} for p in patients], safe=False)


def search_patients_ajax(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse([], safe=False)

    patients = Patient.objects.filter(
        Q(full_name__icontains=query) |
        Q(case_number__icontains=query) |
        Q(phone__icontains=query)
    ).values('id', 'full_name', 'case_number')[:20]

    return JsonResponse(list(patients), safe=False)
