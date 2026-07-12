from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from apps.main.profile import Profile, set_active_profile


def login_required_view(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('auth')
        return view_func(request, *args, **kwargs)
    return wrapper


def vendedor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('auth')
        if not request.user.is_vendedor:
            messages.info(request, 'Precisa de ser vendedor para aceder a esta área.', extra_tags='vendor')
            return redirect('vendor:become_seller')
        set_active_profile(request, Profile.VENDEDOR)
        return view_func(request, *args, **kwargs)
    return wrapper
