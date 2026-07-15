from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from .jwt_utils import ACCESS_COOKIE, add_no_cache_headers

User = get_user_model()


class DevNetworkCsrfMiddleware:
    """Aceita o origin do pedido em DEBUG para testes no telemovel/rede local."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.conf import settings

        if settings.DEBUG:
            host = request.get_host()
            scheme = 'https' if request.is_secure() else 'http'
            origin = f'{scheme}://{host}'
            if origin not in settings.CSRF_TRUSTED_ORIGINS:
                settings.CSRF_TRUSTED_ORIGINS.append(origin)

        return self.get_response(request)


class JWTCookieAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            token = request.COOKIES.get(ACCESS_COOKIE)
            if token:
                try:
                    validated = AccessToken(token)
                    user = (
                        User.objects
                        .prefetch_related('user_roles')
                        .get(pk=validated['user_id'])
                    )
                    if user.is_active:
                        request.user = user
                except (InvalidToken, TokenError, User.DoesNotExist, KeyError):
                    pass

        response = self.get_response(request)

        if request.user.is_authenticated:
            add_no_cache_headers(response)

        return response
