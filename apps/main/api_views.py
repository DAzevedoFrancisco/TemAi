from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import LoginForm, RegisterForm
from .jwt_utils import clear_jwt_cookies, get_tokens_for_user, set_jwt_cookies
from .services import assign_cliente_role, get_post_login_redirect_name

User = get_user_model()


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        form = RegisterForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            name=form.cleaned_data['name'],
            date_of_birth=form.cleaned_data['date_of_birth'],
            gender=form.cleaned_data['gender'],
        )
        assign_cliente_role(user)
        tokens = get_tokens_for_user(user)
        response = Response({
            'message': 'Conta criada com sucesso.',
            'user': {
                'name': user.name,
                'email': user.email,
                'date_of_birth': user.date_of_birth.isoformat(),
                'gender': user.gender,
                'roles': user.get_roles_display(),
            },
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
        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response(
                {'detail': 'Email ou senha inválidos.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

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
