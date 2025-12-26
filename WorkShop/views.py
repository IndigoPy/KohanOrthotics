from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Order, OrderStatusHistory, Measurement
from .forms import OrderCreateForm
from .decorators import group_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Order
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator


@login_required
def dashboard(request):
    user = request.user

    context = {}

    # داشبورد پذیرش
    if user.groups.filter(name='Reception').exists():
        context['role'] = 'reception'
        context['new_orders_count'] = Order.objects.filter(
            status='new').count()
        context['ready_orders_count'] = Order.objects.filter(
            status='ready').count()

    # داشبورد کارگاه
    elif user.groups.filter(name='Workshop').exists():
        context['role'] = 'workshop'
        context['in_progress_count'] = Order.objects.filter(
            status='in_progress').count()
        context['my_ready_count'] = Order.objects.filter(
            status='ready',
            ready_by=user
        ).count()

    return render(request, 'workshop/dashboard.html', context)


@group_required('Reception')
def reception_create_order(request):
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.technical_notes = ', '.join(
                request.POST.getlist('technical_notes', []))
            order.designes = ', '.join(
                request.POST.getlist('designes', []))
            order.save()
            print(request.POST)
            status = request.POST.get('status')
            index = 0
            while f'sizes[{index}][right]' in request.POST:
                right_size = request.POST.get(f'sizes[{index}][right]')
                left_size = request.POST.get(f'sizes[{index}][left]')
                param = request.POST.get(f'sizes[{index}][parameter]')
                # هر اندازه را ذخیره می‌کنیم
                Measurement.objects.create(
                    order=order,
                    parameter=param,
                    right_foot_size=right_size,
                    left_foot_size=left_size
                )
                index += 1
             # اضافه کردن رکورد تاریخچه وضعیت اولیه
            OrderStatusHistory.objects.create(
                order=order,
                status=status,
                changed_by=request.user,  # کاربری که سفارش رو ثبت کرده
            )
            messages.success(
                request, f'سفارش برای {order.patient_name} با موفقیت ثبت شد! شماره سفارش: {order.id}')
            return redirect('order-create')
    else:
        form = OrderCreateForm()

    return render(request, 'workshop/reception_create.html', {
        'form': form,
    })


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
    # اندازه‌های مرتبط با این سفارش را دریافت می‌کنیم
    technical_notes_list = order.technical_notes.split(",") if order.technical_notes != "" else ""
    designes_list = order.designes.split(",") if order.designes != "" else ""
    measurements = order.measurements.all()
    if request.method == 'POST':
        new_status = request.POST.get('status')

        if new_status and new_status != order.status:
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                changed_by=request.user
            )
            order.status = new_status
            order.save()

        return redirect('workshop-list')  # ریدایرکت به صفحه مورد نظر

    return render(request, 'workshop/workshop_update.html', {
        'order': order,
        'current_status': order.status,
        'measurements': measurements,
        'technical_notes_list': technical_notes_list,
        'designes_list': designes_list,
    })


def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # هدایت بر اساس نقش
            if user.groups.filter(name='Reception').exists():
                return redirect('dashboard')

            if user.groups.filter(name='Workshop').exists():
                return redirect('dashboard')

            # اگر نقش نداشت
            logout(request)
            messages.error(request, 'نقش کاربری برای شما تعریف نشده است')

        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است')

    return render(request, 'workshop/login.html')


def custom_logout(request):
    logout(request)
    return redirect('login')


@group_required('Reception')
def reception_ready_orders(request):
    orders = Order.objects.filter(status='ready').order_by('-ready_at')

    return render(request, 'workshop/reception_ready.html', {
        'orders': orders
    })


@group_required('Reception')
def deliver_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, status='ready')

    if request.method == 'POST':
        order.status = 'delivered'
        order.delivered_at = timezone.now()
        order.delivered_by = request.user
        order.save()

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
