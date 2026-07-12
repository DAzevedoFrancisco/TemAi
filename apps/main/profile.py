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
