from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from .jwt_utils import ACCESS_COOKIE, add_no_cache_headers

User = get_user_model()


class JWTCookieAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            token = request.COOKIES.get(ACCESS_COOKIE)
            if token:
                try:
                    validated = AccessToken(token)
                    user = User.objects.get(pk=validated['user_id'])
                    if user.is_active:
                        request.user = user
                except (InvalidToken, TokenError, User.DoesNotExist, KeyError):
                    pass

        response = self.get_response(request)

        if request.user.is_authenticated:
            add_no_cache_headers(response)

        return response
