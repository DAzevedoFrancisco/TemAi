from django.urls import reverse

ACTIVE_PROFILE_SESSION_KEY = 'active_profile'


class Profile:
    CLIENTE = 'cliente'
    VENDEDOR = 'vendedor'
    ADMINISTRADOR = 'administrador'


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


def is_administrador_profile(request):
    return get_active_profile(request) == Profile.ADMINISTRADOR


def can_use_client_catalog(request):
    if not request.user.is_authenticated:
        return True
    return get_active_profile(request) == Profile.CLIENTE


def get_client_catalog_redirect_name(request):
    if get_active_profile(request) == Profile.ADMINISTRADOR:
        return 'admin_panel:dashboard'
    return 'vendor:dashboard'


def get_client_nav_home_url(request):
    if not request.user.is_authenticated:
        return reverse('home')
    profile = get_active_profile(request)
    if profile == Profile.VENDEDOR:
        return reverse('vendor:dashboard')
    if profile == Profile.ADMINISTRADOR:
        return reverse('admin_panel:dashboard')
    return reverse('home')
