from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

def group_required(group_name):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            if request.user.groups.filter(name=group_name).exists():
                return view_func(request, *args, **kwargs)

            return redirect('login')
        return wrapper
    return decorator
