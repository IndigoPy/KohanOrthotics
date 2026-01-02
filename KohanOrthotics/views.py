# KohanOrthotics/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from WorkShop.models import Order
from reception.models import Notification


def custom_login(request):
    if request.user.is_authenticated:
            return redirect('main-dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # هدایت بر اساس نقش
            if user.groups.filter(name='Reception').exists():
                # هدایت بر اساس نقش
                messages.success(
                    request, f'خوش آمدید {user.get_full_name() or user.username}')
                return redirect('main-dashboard')

            if user.groups.filter(name='Workshop').exists():
                # هدایت بر اساس نقش
                messages.success(
                    request, f'خوش آمدید {user.get_full_name() or user.username}')
                return redirect('main-dashboard')

            # اگر نقش نداشت
            logout(request)
            messages.error(request, 'نقش کاربری برای شما تعریف نشده است')

        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است')

    return render(request, 'workshop/login.html')


def custom_logout(request):
    logout(request)
    return redirect('login')


# KohanOrthotics/views.py


@login_required
def main_dashboard(request):
    user = request.user

    # آمار کلی سفارش‌ها
    ready_orders_count = Order.objects.filter(status='ready').count()
    urgent_ready_count = Order.objects.filter(
        status='ready', priority='urgent').count()
    today_orders_count = Order.objects.filter(
        created_at__date__gte=timezone.now().date()).count()
    today_delivered_count = Order.objects.filter(
        delivered_at__date__gte=timezone.now().date()).count()

    # نوتیفیکیشن‌های کاربر (۱۰ تای آخر، خوانده‌نشده اول)
    notifications = request.user.notifications.order_by(
        '-is_read', '-created_at')[:10]
    unread_notifications_count = request.user.notifications.filter(
        is_read=False).count()

    context = {
        'user': user,
        'ready_orders_count': ready_orders_count,
        'urgent_ready_count': urgent_ready_count,
        'today_orders_count': today_orders_count,
        'today_delivered_count': today_delivered_count,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
    }
    return render(request, 'base_dashboard.html', context)          
