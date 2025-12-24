from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Order
from .forms import OrderCreateForm
from .decorators import group_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .decorators import group_required
from .models import Order
from django.db.models import Q
from django.contrib.auth.decorators import login_required


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
            order.created_by = request.user
            order.save()
            return redirect('order-create')
    else:
        form = OrderCreateForm()

    return render(request, 'workshop/reception_create.html', {
        'form': form
    })


@group_required('Workshop')
def workshop_order_list(request):
    orders = Order.objects.all()

    # فیلتر نام بیمار
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            Q(patient_name__icontains=search) |
            Q(phone__icontains=search)
        )

    # فیلتر وضعیت
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)

    # فیلتر نوع وسیله
    device_type = request.GET.get('device_type')
    if device_type:
        orders = orders.filter(device_type=device_type)

    orders = orders.order_by('-created_at')

    return render(
        request,
        'workshop/workshop_list.html',
        {
            'orders': orders,
            'search': search,
            'status': status,
            'device_type': device_type,
            'status_choices': Order.STATUS_CHOICES,
            'device_choices': Order.DEVICE_CHOICES,
        }
    )


@group_required('Workshop')
def workshop_update_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        status = request.POST.get('status')
        workshop_notes = request.POST.get('workshop_notes')

        order.status = status
        order.workshop_notes = workshop_notes

        if status == 'ready' and order.ready_at is None:
            order.ready_at = timezone.now()
            order.ready_by = request.user

        order.save()
        return redirect('workshop-list')

    return render(request, 'workshop/workshop_update.html', {
        'order': order
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
            Q(patient_name__icontains=search) |
            Q(phone__icontains=search)
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
