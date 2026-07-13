from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import LoginForm, RegisterForm
from .jwt_utils import clear_jwt_cookies, get_tokens_for_user, set_jwt_cookies
from .login_throttle import (
    clear_login_attempts,
    failed_login_error_message,
    is_login_locked,
    lockout_error_message,
    register_failed_login,
)
from .services import ensure_system_admin, get_post_login_redirect_name, register_user_with_default_role


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        form = RegisterForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        user = register_user_with_default_role(
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            name=form.cleaned_data['name'],
            date_of_birth=form.cleaned_data['date_of_birth'],
            gender=form.cleaned_data['gender'],
        )
        tokens = get_tokens_for_user(user)
        response = Response({
            'message': 'Conta criada com sucesso.',
            'user': {
                'name': user.name,
                'email': user.email,
                'date_of_birth': user.date_of_birth.isoformat(),
                'gender': user.gender,
                'roles': user.get_roles_display(),
                'is_administrador': user.is_administrador,
            },
            'redirect': get_post_login_redirect_name(user),
            'tokens': tokens,
        }, status=status.HTTP_201_CREATED)
        return set_jwt_cookies(response, tokens)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        form = LoginForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        email = form.cleaned_data['email'].lower()
        password = form.cleaned_data['password']

        if is_login_locked(email):
            return Response(
                {'detail': lockout_error_message(email)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        user = authenticate(request, username=email, password=password)

        if user is None:
            attempts, locked = register_failed_login(email)
            if locked:
                return Response(
                    {'detail': lockout_error_message(email)},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
            return Response(
                {'detail': failed_login_error_message(email, attempts)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        clear_login_attempts(email)
        ensure_system_admin()
        user.refresh_from_db()

        tokens = get_tokens_for_user(user)
        response = Response({
            'message': 'Login efetuado com sucesso.',
            'user': {
                'name': user.name,
                'email': user.email,
                'is_administrador': user.is_administrador,
            },
            'redirect': get_post_login_redirect_name(user),
            'tokens': tokens,
        })
        return set_jwt_cookies(response, tokens)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh')

        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass

        response = Response({'message': 'Logout efetuado com sucesso.'})
        return clear_jwt_cookies(response)


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'name': user.name,
            'email': user.email,
            'date_of_birth': user.date_of_birth.isoformat(),
            'roles': user.get_roles_display(),
            'is_vendedor': user.is_vendedor,
        })
