from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

ACCESS_COOKIE = 'access_token'
REFRESH_COOKIE = 'refresh_token'


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def set_jwt_cookies(response, tokens):
    access_lifetime = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
    refresh_lifetime = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']

    response.set_cookie(
        ACCESS_COOKIE,
        tokens['access'],
        max_age=int(access_lifetime.total_seconds()),
        httponly=True,
        samesite='Lax',
        secure=not settings.DEBUG,
    )
    response.set_cookie(
        REFRESH_COOKIE,
        tokens['refresh'],
        max_age=int(refresh_lifetime.total_seconds()),
        httponly=True,
        samesite='Lax',
        secure=not settings.DEBUG,
    )
    return response


def add_no_cache_headers(response):
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def clear_jwt_cookies(response):
    response.delete_cookie(ACCESS_COOKIE, path='/')
    response.delete_cookie(REFRESH_COOKIE, path='/')
    return add_no_cache_headers(response)
