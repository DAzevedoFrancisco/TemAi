from django.urls import reverse

ACTIVE_PROFILE_SESSION_KEY = 'active_profile'


class Profile:
    CLIENTE = 'cliente'
    VENDEDOR = 'vendedor'


def get_active_profile(request):
    if not request.user.is_authenticated:
        return None
    return request.session.get(ACTIVE_PROFILE_SESSION_KEY, Profile.CLIENTE)


def set_active_profile(request, profile):
    request.session[ACTIVE_PROFILE_SESSION_KEY] = profile


def is_cliente_profile(request):
    return get_active_profile(request) == Profile.CLIENTE


def is_vendedor_profile(request):
    return get_active_profile(request) == Profile.VENDEDOR


def can_use_client_catalog(request):
    if not request.user.is_authenticated:
        return True
    if request.user.is_administrador:
        return False
    return get_active_profile(request) == Profile.CLIENTE


def get_client_catalog_redirect_name(request):
    if request.user.is_authenticated and request.user.is_administrador:
        return 'admin_panel:dashboard'
    return 'vendor:dashboard'


def get_client_nav_home_url(request):
    if request.user.is_authenticated:
        if request.user.is_administrador:
            return reverse('admin_panel:dashboard')
        if get_active_profile(request) == Profile.VENDEDOR:
            return reverse('vendor:dashboard')
    return reverse('home')
