from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .services import get_post_login_redirect_name


def is_safe_redirect_url(request, url):
    if not url:
        return False
    return url_has_allowed_host_and_scheme(
        url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )


def get_safe_redirect_url(request, *candidates, fallback=None):
    for candidate in candidates:
        if is_safe_redirect_url(request, candidate):
            return candidate
    if fallback:
        return fallback
    return reverse('home')


def redirect_safely(request, *candidates, fallback=None):
    for candidate in candidates:
        if is_safe_redirect_url(request, candidate):
            return redirect(candidate)
    if fallback is not None:
        return redirect(fallback)
    return redirect('home')


def get_post_auth_redirect(request, user):
    default = reverse(get_post_login_redirect_name(user))
    return get_safe_redirect_url(
        request,
        request.POST.get('next'),
        request.GET.get('next'),
        fallback=default,
    )
