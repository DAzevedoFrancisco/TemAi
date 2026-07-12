from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def login_required_view(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('auth')
        return view_func(request, *args, **kwargs)
    return wrapper


def administrador_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('auth')
        if not request.user.is_administrador:
            messages.error(request, 'Precisa de ser administrador para aceder a esta área.', extra_tags='admin')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
