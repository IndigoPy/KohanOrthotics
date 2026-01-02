# reception/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Patient, Document, Examination
from WorkShop.forms import OrderCreateForm
from WorkShop.models import Order
from WorkShop.decorators import group_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db import IntegrityError
from django.utils import timezone
from jdatetime import date as jdate
import json
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
            underlying_diseases=','.join(
                request.POST.getlist('underlying_diseases')),
            orthotic_history=','.join(
                request.POST.getlist('orthotic_history')),
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

    last_patient = Patient.objects.filter(
        case_number__startswith=prefix).order_by('-case_number').first()
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
    examinations = patient.examinations.all().order_by('-exam_date')
    latest_exam = examinations.first()  # آخرین معاینه
    attached_patients = Patient.objects.filter(attached_to=patient)
    documents = patient.documents.all()

    context = {
        'patient': patient,
        'orders': orders,
        'examinations': examinations,
        'latest_exam': latest_exam,  # اضافه شد
        'attached_patients': attached_patients,
        'documents': documents,
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

# ------------------Examination Room Views------------------ #


@group_required('Examiner')
def create_examination(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    # لیست‌های پیشنهادی برای Select2 (می‌تونی از دیتابیس بگیری)
    observations_list = [
        'صافی کف پا', 'قوس زیاد', 'پرونیشن بیش از حد', 'سوپینیشن', 'درد پاشنه',
        'پلانتار فاشییت', 'متاتارسالژیا', 'درد آشیل', 'هالوکس والگوس', 'چنگالی انگشت',
        'درد زانو', 'درد لگن', 'کمردرد', 'کوتاهی پا', 'ناپایداری مچ', 'مشکلات وضعیتی',
        'پای دیابتی', 'مشکلات راه رفتن کودکان', 'مشکلات پس از سکته'
    ]

    services_list = [
        'کفی طبی', 'کفش طبی', 'صندل طبی', 'ارتز مچ پا', 'ارتز زانو', 'ارتز کمر'
    ]

    designs_list = [
        'مدیال ودج', 'لترال ودج', 'هیلیوس', 'متاتارسال پد', 'پشتیبانی قوس',
        'شوک آبسوربر', 'ساپورت انگشتان', 'ارتفاع پاشنه'
    ]

    exercises_list = [
        'Toe Curls', 'Heel Raises', 'Ankle Circles', 'Calf Stretches', 'Foot Rolls',
        'Towel Scrunches', 'Marble Pickup', 'Resistance Band Exercises',
        'Balance Exercises', 'Arch Strengthening Exercises'
    ]

    if request.method == 'POST':
        # جمع‌آوری مشاهدات (با یا بدون چپ/راست)
        observations = ''
        if 'observations_left' in request.POST or 'observations_right' in request.POST:
            left = request.POST.get('observations_left', '')
            right = request.POST.get('observations_right', '')
            observations = f"چپ: {left} | راست: {right}".strip(' |')
        else:
            observations = ','.join(request.POST.getlist('observations'))

        # جمع‌آوری تمرین‌ها
        exercises = ','.join(request.POST.getlist('exercises'))

        # جمع‌آوری یادداشت
        notes = request.POST.get('notes', '')

        # جمع‌آوری تجویز خدمات و جزئیات (تعداد کلی + طراحی چپ/راست اگر متفاوت)
        prescription_data = {}
        for key in request.POST:
            if key.startswith('quantity_'):
                service_raw = key.replace('quantity_', '')
                service = service_raw.replace('-', ' ')  # برگرداندن به نام اصلی
                quantity = request.POST.get(key, 0)

                # طراحی‌ها
                designs = ''
                if 'designs_' + service_raw + '_left' in request.POST or 'designs_' + service_raw + '_right' in request.POST:
                    left_designs = request.POST.get(f'designs_{service_raw}_left', '')
                    right_designs = request.POST.get(f'designs_{service_raw}_right', '')
                    designs = f"چپ: {left_designs} | راست: {right_designs}".strip(' |')
                else:
                    designs = ','.join(request.POST.getlist(f'designs_{service_raw}'))

                prescription_data[service] = {
                    'quantity': int(quantity),
                    'designs': designs
                }

        # ایجاد معاینه
        examination = Examination(
            patient=patient,
            exam_date=timezone.now(),
            doctor=request.user,
            observations=observations,
            prescription_services=json.dumps(prescription_data, ensure_ascii=False, indent=2),
            exercises=exercises,
            notes=notes,
            created_by=request.user
        )
        examination.save()

        messages.success(request, 'معاینه با موفقیت ثبت شد.')
        return redirect('reception:patient-detail', patient_id=patient.id)

    context = {
        'patient': patient,
        'observations_list': observations_list,
        'services_list': services_list,
        'designs_list': designs_list,
        'exercises_list': exercises_list,
    }
    return render(request, 'reception/create_examination.html', context)

@group_required('Reception')
@login_required
def edit_examination(request, exam_id):
    exam = get_object_or_404(Examination, id=exam_id)
    patient = exam.patient

    # لیست‌های پیشنهادی (می‌تونی از دیتابیس بگیری یا ثابت نگه داری)
    observations_list = [
        'صافی کف پا', 'قوس زیاد', 'پرونیشن بیش از حد', 'سوپینیشن', 'درد پاشنه',
        'پلانتار فاشییت', 'متاتارسالژیا', 'درد آشیل', 'هالوکس والگوس', 'چنگالی انگشت',
        'درد زانو', 'درد لگن', 'کمردرد', 'کوتاهی پا', 'ناپایداری مچ', 'مشکلات وضعیتی',
        'پای دیابتی', 'مشکلات راه رفتن کودکان', 'مشکلات پس از سکته'
    ]

    services_list = [
        'کفی طبی', 'کفش طبی', 'صندل طبی', 'ارتز مچ پا', 'ارتز زانو', 'ارتز کمر'
    ]

    designs_list = [
        'مدیال ودج', 'لترال ودج', 'هیلیوس', 'متاتارسال پد', 'پشتیبانی قوس',
        'شوک آبسوربر', 'ساپورت انگشتان', 'ارتفاع پاشنه'
    ]

    exercises_list = [
        'Toe Curls', 'Heel Raises', 'Ankle Circles', 'Calf Stretches', 'Foot Rolls',
        'Towel Scrunches', 'Marble Pickup', 'Resistance Band Exercises',
        'Balance Exercises', 'Arch Strengthening Exercises'
    ]

    if request.method == 'POST':
        # جمع‌آوری مشاهدات (با یا بدون چپ/راست)
        observations = ''
        if 'observations_left' in request.POST or 'observations_right' in request.POST:
            left = request.POST.get('observations_left', '')
            right = request.POST.get('observations_right', '')
            observations = f"چپ: {left} | راست: {right}".strip(' |')
        else:
            observations = ','.join(request.POST.getlist('observations'))

        # جمع‌آوری تمرین‌ها
        exercises = ','.join(request.POST.getlist('exercises'))

        # جمع‌آوری یادداشت
        notes = request.POST.get('notes', '')

        # جمع‌آوری تجویز خدمات و جزئیات (تعداد کلی + طراحی چپ/راست اگر متفاوت)
        prescription_data = {}
        for key in request.POST:
            if key.startswith('quantity_'):
                service_raw = key.replace('quantity_', '')
                service = service_raw.replace('-', ' ')  # برگرداندن به نام اصلی
                quantity = request.POST.get(key, 0)

                # طراحی‌ها
                designs = ''
                if f'designs_{service_raw}_left' in request.POST or f'designs_{service_raw}_right' in request.POST:
                    left_designs = request.POST.get(f'designs_{service_raw}_left', '')
                    right_designs = request.POST.get(f'designs_{service_raw}_right', '')
                    designs = f"چپ: {left_designs} | راست: {right_designs}".strip(' |')
                else:
                    designs = ','.join(request.POST.getlist(f'designs_{service_raw}'))

                prescription_data[service] = {
                    'quantity': int(quantity),
                    'designs': designs
                }

        # به‌روزرسانی معاینه
        exam.observations = observations
        exam.prescription_services = json.dumps(prescription_data, ensure_ascii=False, indent=2)
        exam.exercises = exercises
        exam.notes = notes
        exam.save()

        messages.success(request, 'معاینه با موفقیت ویرایش شد.')
        return redirect('reception:patient-detail', patient_id=patient.id)

    context = {
        'exam': exam,
        'patient': patient,
        'observations_list': observations_list,
        'services_list': services_list,
        'designs_list': designs_list,
        'exercises_list': exercises_list,
    }
    return render(request, 'reception/edit_examination.html', context)  


@group_required('Reception')
@login_required
def delete_examination(request, exam_id):
    exam = get_object_or_404(Examination, id=exam_id)
    patient_id = exam.patient.id

    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'معاینه با موفقیت حذف شد.')
        return redirect('reception:patient-detail', patient_id=patient_id)

    return redirect('reception:patient-detail', patient_id=patient_id)
