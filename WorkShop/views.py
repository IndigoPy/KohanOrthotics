from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from urllib3 import request
from .models import Order, WorkshopStatusHistory, Measurement
from reception.models import ReceptionStatusHistory, Patient, Notification  # اگر هنوز استفاده می‌کنی
from .forms import OrderCreateForm, ReceptionStatusForm
from .decorators import group_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Order
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth.models import User, Group
from django.urls import reverse
from jdatetime import datetime as jdatetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt  # یا از csrf_protect استفاده کن و توکن رو چک کن
@login_required
def mark_notification_read(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        notification_id = data.get('id')
        try:
            notification = request.user.notifications.get(id=notification_id)
            notification.is_read = True
            notification.save()
            return JsonResponse({'success': True})
        except:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})


def shamsi_to_gregorian(shamsi_str):
    """
    تبدیل تاریخ شمسی به میلادی
    ورودی: '1404/10/05' یا '1404-10-05'
    خروجی: datetime.date میلادی یا None اگر نامعتبر باشه
    """
    if not shamsi_str:
        return None
    try:
        # جایگزینی اسلش با خط تیره برای یکسان‌سازی
        shamsi_str = shamsi_str.replace('/', '-')
        year, month, day = map(int, shamsi_str.split('-'))
        jalali_date = jdatetime(year, month, day)
        return jalali_date.togregorian()  # تبدیل به میلادی
    except (ValueError, TypeError):
        return None


def create_notification(user, message, url=None):
    Notification.objects.create(
        user=user,
        message=message,
        url=url,
    )


@login_required
def dashboard(request):
    user = request.user
    context = {
        'user_name': user.get_full_name() or user.username,
    }
    now = timezone.now().date()
    if user.groups.filter(name='Reception').exists():
        context['role'] = 'reception'
        context['ready_orders_count'] = Order.objects.filter(
            status='ready').count()
        context['today_orders_count'] = Order.objects.filter(
            created_at__date=timezone.now().date()).count()
        context['today_delivered_count'] = Order.objects.filter(
            delivered_at__date=timezone.now().date()).count()

        # تعداد اورژانسی‌های آماده برای پذیرش
        context['urgent_ready_count'] = Order.objects.filter(
            status='ready', priority='urgent').count()

    elif user.groups.filter(name='Workshop').exists():
        context['role'] = 'workshop'
        context['in_progress_count'] = Order.objects.filter(
            status='in_progress').count()
        context['my_ready_count'] = Order.objects.filter(
            status='ready', ready_by=user).count()
        context['my_ready_url'] = f"{reverse('workshop-list')}?status=ready&ready_by={user.username}"
        # تعداد اورژانسی‌های در حال کار یا آماده برای کارگاه
        context['urgent_in_workshop_count'] = Order.objects.filter(
            priority='urgent',
            status__in=['in_progress', 'ready']
        ).count()
    else:
        context['role'] = 'none'
# —————————————— محاسبه تعداد اعلان‌های خوانده‌نشده ——————————————
    unread_count = user.notifications.filter(is_read=False).count()
    context['unread_notifications_count'] = unread_count
    context['notifications'] = user.notifications.all().order_by(
        '-created_at')[:10]
    return render(request, 'workshop/dashboard.html', context)


@group_required('Reception')
def reception_create_order(request):
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)

            different_feet = request.POST.get('different_designs') == 'on'

            if different_feet:
                order.different_designs = True

                # ذخیره فیلدهای جداگانه (حتی اگر خالی باشن)
                order.designes_left = ', '.join(
                    request.POST.getlist('designes_left'))
                order.designes_right = ', '.join(
                    request.POST.getlist('designes_right'))
                order.technical_notes_left = ', '.join(
                    request.POST.getlist('technical_notes_left'))
                order.technical_notes_right = ', '.join(
                    request.POST.getlist('technical_notes_right'))

                order.designes = ''
                order.technical_notes = ''

                # اختیاری: اگر می‌خوای حداقل یکی پر شده باشه
                # if not (order.designes_left or order.designes_right or order.technical_notes_left or order.technical_notes_right):
                #     messages.error(request, 'لطفاً حداقل یکی از بخش‌های چپ یا راست را پر کنید.')
                #     return render(request, 'workshop/reception_create.html', {'form': form})

            else:
                order.different_designs = False
                order.designes_left = order.designes_right = ''
                order.technical_notes_left = order.technical_notes_right = ''

                # چک می‌کنیم فیلدهای اصلی پر شده باشن
                designes = request.POST.getlist('designes')
                technical_notes = request.POST.getlist('technical_notes')

                if not designes:
                    messages.error(request, 'فیلد "طراحی‌ها" الزامی است.')
                    return render(request, 'workshop/reception_create.html', {'form': form})

                if not technical_notes:
                    messages.error(request, 'فیلد "خلاصه پرونده" الزامی است.')
                    return render(request, 'workshop/reception_create.html', {'form': form})

                order.designes = ', '.join(designes)
                order.technical_notes = ', '.join(technical_notes)

            order.save()

            # # اعلان برای کارگاه
            # create_notification(
            #     user=User.objects.filter(
            #         groups__name='Workshop').first(),  # یا گروه خاص
            #     message=f"سفارش جدید برای {order.patient_name} ثبت شد",
            #     url=reverse('workshop-update', args=[order.id])
            # )
            # —————————————— ذخیره اندازه‌ها (همون قبلی، بدون تغییر) ——————————————
            index = 0
            while f'sizes[{index}][parameter]' in request.POST:
                param = request.POST.get(f'sizes[{index}][parameter]')
                right_size = request.POST.get(f'sizes[{index}][right]', '')
                left_size = request.POST.get(f'sizes[{index}][left]', '')

                if param:
                    Measurement.objects.create(
                        order=order,
                        parameter=param,
                        right_foot_size=right_size or None,
                        left_foot_size=left_size or None
                    )
                index += 1

            # —————————————— تاریخچه وضعیت ——————————————
            status = request.POST.get('status', 'registered')
            OrderStatusHistory.objects.create(
                order=order,
                status=status,
                changed_by=request.user,
            )

            messages.success(
                request, f'سفارش برای {order.patient_name} با موفقیت ثبت شد! شماره سفارش: {order.id}')
            return redirect('order-create')
    else:
        form = OrderCreateForm()

    return render(request, 'workshop/reception_create.html', {'form': form})


@group_required('Workshop')
def workshop_order_list(request):
    orders = Order.objects.filter(send_to='workshop')

    # فیلتر نام بیمار
    search = request.GET.get('search')
    if search:
        orders = orders.filter(patient_name__icontains=search)

    # فیلتر شماره پرونده
    case_number = request.GET.get('case_number')
    if case_number:
        orders = orders.filter(case_number__icontains=case_number)

    # فیلتر وضعیت
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)

# فیلتر آماده‌کننده (فقط برای کارهای آماده)
    ready_by = request.GET.get('ready_by')
    if ready_by and status == 'ready':
        orders = orders.filter(ready_by__username=ready_by)

    # فیلتر نوع وسیله
    device_type = request.GET.get('device_type')
    if device_type:
        orders = orders.filter(device_type=device_type)

    orders = Order.objects.exclude(
        status='delivered').order_by('-priority', '-created_at')

    # دریافت تعداد رکورد در هر صفحه
    records_per_page = request.GET.get('per_page', 15)

    # صفحه‌بندی
    paginator = Paginator(orders, records_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'workshop/workshop_list.html', {
        'orders': page_obj,  # اینجا page_obj را به عنوان orders می‌فرستیم
        'search': search,
        'case_number': case_number,
        'status': status,
        'device_type': device_type,
        'status_choices': Order.STATUS_CHOICES,
        'device_choices': Order.DEVICE_CHOICES,
        'records_per_page': records_per_page,
        'page_obj': page_obj,
    })


@group_required('Workshop')
def workshop_update_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    measurements = order.measurements.all()
    patient_orders = Order.objects.filter(case_number=order.case_number).exclude(
        id=order.id).order_by('-created_at')

    # آماده‌سازی لیست‌ها برای نمایش (چپ/راست یا مشترک)
    if order.different_designs:
        technical_notes_left = order.technical_notes_left.split(
            ', ') if order.technical_notes_left else []
        technical_notes_right = order.technical_notes_right.split(
            ', ') if order.technical_notes_right else []
        technical_notes = None
        designes_left = order.designes_left.split(
            ', ') if order.designes_left else []
        designes_right = order.designes_right.split(
            ', ') if order.designes_right else []
        designes = None
    else:
        technical_notes = order.technical_notes.split(
            ', ') if order.technical_notes else []
        technical_notes_left = technical_notes_right = None
        designes = order.designes.split(', ') if order.designes else []
        designes_left = designes_right = None

    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        new_notes = request.POST.get('workshop_notes', '').strip()

        status_changed = new_status != order.status
        notes_changed = new_notes != (order.workshop_notes or '')

        if status_changed or notes_changed:
            # ذخیره توضیحات کارگاه
            order.workshop_notes = new_notes
            order.save()

            if new_status != order.status:
                WorkshopStatusHistory.objects.create(
                    order=order,
                    status=new_status,
                    changed_by=request.user,
                    notes=new_notes
                )

                order.status = new_status

                if new_status == 'ready':
                    order.ready_by = request.user
                    order.ready_at = timezone.now()

                order.save()

                # —————— نوتیفیکیشن به پذیرش ——————
                # if new_status == 'ready':
                #     # try:
                #     #     reception_group = Group.objects.get(name='Reception')
                #     #     reception_users = reception_group.user_set.all()

                #     #     for user in reception_users:
                #     #         # create_notification(
                #     #         #     user=user,
                #     #         #     message=f"سفارش آماده تحویل شد: #{order.id} - {order.patient_name} ({order.get_device_type_display()})",
                #     #         #     url=reverse('reception-order-detail', args=[order.id])
                #     #         # )
                #     #     # messages.success(request, 'سفارش آماده شد و پذیرش مطلع گردید.')
                #     # except Group.DoesNotExist:
                #     #     messages.warning(request, 'گروه Reception وجود ندارد. نوتیفیکیشن ارسال نشد.')
                # else:
                #     messages.success(request, f'وضعیت سفارش به "{order.get_status_display()}" تغییر کرد.')

                # اعلان به پذیرش
                def create_notification(user, message, url=None):
                    if user:  # اضافه کردن چک برای جلوگیری از خطا
                        Notification.objects.create(
                            user=user,
                            message=message,
                            url=url,
                        )
                messages.success(
                    request, f'وضعیت سفارش به "{order.get_status_display()}" تغییر کرد و پذیرش مطلع شد.')
            else:
                messages.success(request, 'یادداشت کارگاه ذخیره شد.')

        return redirect('workshop-list')

    return render(request, 'workshop/workshop_update.html', {
        'order': order,
        'measurements': measurements,
        'patient_orders': patient_orders,
        'technical_notes_list': technical_notes,
        'technical_notes_list_left': technical_notes_left,
        'technical_notes_list_right': technical_notes_right,
        'designes_list': designes,
        'designes_list_left': designes_left,
        'designes_list_right': designes_right,
        # اختیاری: نمایش تاریخچه کارگاه در صفحه کارگاه
        'workshop_history': order.workshop_history.all(),
    })








@group_required('Reception')
def reception_ready_orders(request):
    # شروع با سفارشات آماده
    orders = Order.objects.filter(status='ready')

    # —————————————— سورت: اورژانسی اول، سپس تاریخ جدیدترین ——————————————
    # urgent اول (اگر priority='urgent' باشه و فیلد CharField باشه، 'urgent' > 'normal' در مرتب‌سازی)
    orders = orders.order_by('-priority', '-ready_at')

    # —————————————— فیلتر جستجو (نام بیمار یا شماره پرونده) ——————————————
    search = request.GET.get('search', '').strip()
    if search:
        orders = orders.filter(
            Q(patient_name__icontains=search) |
            Q(case_number__icontains=search)
        )

    # —————————————— فیلتر اولویت ——————————————
    priority = request.GET.get('priority')
    if priority in ['urgent', 'normal']:
        orders = orders.filter(priority=priority)

    # —————————————— فیلتر تاریخ آماده شدن (شمسی به میلادی) ——————————————
    start_date_shamsi = request.GET.get('start_date')
    end_date_shamsi = request.GET.get('end_date')

    start_greg = shamsi_to_gregorian(start_date_shamsi)
    end_greg = shamsi_to_gregorian(end_date_shamsi)

    if start_greg:
        orders = orders.filter(ready_at__date__gte=start_greg)

    if end_greg:
        orders = orders.filter(ready_at__date__lte=end_greg)

    # —————————————— تعداد رکورد در صفحه ——————————————
    records_per_page = request.GET.get('per_page')
    if records_per_page:
        try:
            records_per_page = int(records_per_page)
            if records_per_page not in [5, 10, 20, 50, 100]:
                records_per_page = 15
        except (ValueError, TypeError):
            records_per_page = 15
    else:
        records_per_page = 15

    # —————————————— صفحه‌بندی ——————————————
    paginator = Paginator(orders, records_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # —————————————— ساخت query string برای حفظ فیلترها در صفحه‌بندی ——————————————
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    current_query_string = '&' + query_params.urlencode() if query_params else ''

    context = {
        'page_obj': page_obj,
        'search': search,
        'priority': priority,
        'start_date': start_date_shamsi,  # برای نمایش در input شمسی
        'end_date': end_date_shamsi,
        'records_per_page': records_per_page,
        'current_query_string': current_query_string,  # برای صفحه‌بندی
    }

    return render(request, 'workshop/reception_ready.html', context)


@group_required('Reception')
def deliver_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, status='ready')

    if request.method == 'POST':
        order.status = 'delivered'
        order.delivered_at = timezone.now()
        order.delivered_by = request.user
        order.save()

        # ثبت در تاریخچه پذیرش
        ReceptionStatusHistory.objects.create(
            order=order,
            status='delivered',
            changed_by=request.user,
            notes="تحویل به بیمار انجام شد."
        )

        messages.success(
            request, f'سفارش #{order.id} با موفقیت تحویل داده شد.')
        return redirect('reception-ready')

    return redirect('reception-ready')


@group_required('Reception')
def delivered_orders_archive(request):
    orders = Order.objects.filter(status='delivered')

    # فیلتر نام بیمار یا تلفن
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            Q(patient_name__icontains=search)
        )

    # فیلتر تاریخ تحویل
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        orders = orders.filter(delivered_at__date__gte=start_date)

    if end_date:
        orders = orders.filter(delivered_at__date__lte=end_date)

    orders = orders.select_related(
        'ready_by', 'delivered_by'
    ).order_by('-delivered_at')

    return render(
        request,
        'workshop/delivered_archive.html',
        {
            'orders': orders,
            'search': search,
            'start_date': start_date,
            'end_date': end_date,
        }
    )


@group_required('Reception')
def workshop_delete(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    # همیشه یک پاسخ redirect برگردانید
    return redirect('workshop-list')


def examination_order_list(request):
    orders = Order.objects.filter(send_to='examination')
    return render(request, 'examination_order_list.html', {'orders': orders})


@group_required('Reception')
def reception_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    measurements = order.measurements.all()

    # تاریخچه سفارشات قبلی بیمار
    patient_orders = Order.objects.filter(case_number=order.case_number).exclude(
        id=order.id).order_by('-created_at')

    # آماده‌سازی لیست‌های طراحی و خلاصه پرونده
    if order.different_designs:
        technical_notes_left = order.technical_notes_left.split(
            ', ') if order.technical_notes_left else []
        technical_notes_right = order.technical_notes_right.split(
            ', ') if order.technical_notes_right else []
        technical_notes = None
        designes_left = order.designes_left.split(
            ', ') if order.designes_left else []
        designes_right = order.designes_right.split(
            ', ') if order.designes_right else []
        designes = None
    else:
        technical_notes = order.technical_notes.split(
            ', ') if order.technical_notes else []
        technical_notes_left = technical_notes_right = None
        designes = order.designes.split(', ') if order.designes else []
        designes_left = designes_right = None

    # فرم برای ثبت تغییرات پذیرش
    if request.method == 'POST':
        form = ReceptionStatusForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            new_notes = form.cleaned_data['notes']

            # همیشه یک رکورد در تاریخچه پذیرش ثبت می‌کنیم (حتی اگر وضعیت تغییر نکرده باشد)
            ReceptionStatusHistory.objects.create(
                order=order,
                status=new_status,
                changed_by=request.user,
                notes=new_notes or "بدون توضیح"
            )

            # فقط اگر وضعیت تغییر کرده باشد، وضعیت اصلی سفارش را به‌روزرسانی می‌کنیم
            if new_status != order.status:
                order.status = new_status
                order.save()

                # اعلان به کارگاه در صورت نیاز
                create_notification(
                    user=order.ready_by if order.ready_by else None,
                    message=f"پذیرش وضعیت سفارش #{order.id} را به «{order.get_status_display()}» تغییر داد.\nتوضیح: {new_notes}",
                    url=reverse('workshop-update', args=[order.id])
                )

            messages.success(request, 'تغییرات پذیرش با موفقیت ثبت شد.')
            return redirect('reception-order-detail', order_id=order.id)
    else:
        form = ReceptionStatusForm(initial={'status': order.status})  # درست
    context = {
        'order': order,
        'measurements': measurements,
        'patient_orders': patient_orders,
        'technical_notes': technical_notes,
        'technical_notes_left': technical_notes_left,
        'technical_notes_right': technical_notes_right,
        'designes': designes,
        'designes_left': designes_left,
        'designes_right': designes_right,

        # دو تاریخچه جداگانه
        'workshop_history': order.workshop_history.all(),
        'reception_history': order.reception_history.all(),

        'form': form,  # برای سایدبار
    }

    return render(request, 'workshop/reception_order_detail.html', context)
