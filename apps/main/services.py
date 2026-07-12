from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.vendor.models import Establishment

from .jwt_utils import REFRESH_COOKIE, clear_jwt_cookies
from .models import UserRole
from .validators import MIN_VENDOR_AGE, user_meets_min_age

User = get_user_model()

DELETE_CONFIRMATION_TEXT = 'APAGAR'


def suspend_establishments_for_admin_role(user):
    now = timezone.now()
    for establishment in Establishment.objects.filter(owner=user, is_active=True):
        establishment.is_active = False
        establishment.suspended_for_admin_role = True
        establishment.updated_at = now
        establishment.save(update_fields=['is_active', 'suspended_for_admin_role', 'updated_at'])


def restore_establishments_after_admin_demote(user):
    now = timezone.now()
    for establishment in Establishment.objects.filter(owner=user, suspended_for_admin_role=True):
        establishment.is_active = True
        establishment.suspended_for_admin_role = False
        establishment.updated_at = now
        establishment.save(update_fields=['is_active', 'suspended_for_admin_role', 'updated_at'])


def assign_cliente_role(user):
    user.add_role(UserRole.Role.CLIENTE)


def assign_vendedor_role(user):
    if not user_meets_min_age(user, MIN_VENDOR_AGE):
        raise ValidationError(
            f'Precisa de ter pelo menos {MIN_VENDOR_AGE} anos para se tornar vendedor.'
        )
    user.add_role(UserRole.Role.VENDEDOR)


def assign_admin_role(user):
    suspend_establishments_for_admin_role(user)
    user.user_roles.all().delete()
    user.add_role(UserRole.Role.ADMINISTRADOR)


def has_system_admin():
    return UserRole.objects.filter(role=UserRole.Role.ADMINISTRADOR).exists()


def ensure_system_admin():
    if has_system_admin():
        return None

    oldest_user = User.objects.order_by('date_joined', 'pk').first()
    if oldest_user is None:
        return None

    assign_admin_role(oldest_user)
    return oldest_user


def register_user_with_default_role(*, email, password, name, date_of_birth, gender):
    with transaction.atomic():
        User.objects.select_for_update().exists()
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            date_of_birth=date_of_birth,
            gender=gender,
        )
        if not has_system_admin():
            oldest_user = User.objects.order_by('date_joined', 'pk').first()
            assign_admin_role(oldest_user)
            if user.pk != oldest_user.pk:
                assign_cliente_role(user)
        else:
            assign_cliente_role(user)
        user.refresh_from_db()
        return user


def promote_to_admin(user):
    assign_admin_role(user)


def demote_from_admin(user):
    user.user_roles.all().delete()
    assign_cliente_role(user)
    restore_establishments_after_admin_demote(user)


def get_post_login_redirect_name(user):
    if user.is_administrador:
        return 'admin_panel:dashboard'
    return 'home'


def administrator_count():
    return (
        User.objects
        .filter(user_roles__role=UserRole.Role.ADMINISTRADOR)
        .distinct()
        .count()
    )


def get_self_account_deletion_block_reason(user):
    if user.is_administrador:
        return (
            'Contas de administrador não podem ser eliminadas aqui. '
            'Peça a outro administrador para remover o seu acesso ou despromovê-lo.'
        )
    return None


def get_admin_account_deletion_block_reason(target, actor):
    if target.pk == actor.pk:
        return 'Não pode apagar a sua própria conta.'
    if target.is_administrador and administrator_count() <= 1:
        return 'Não pode apagar o último administrador do sistema.'
    return None


def get_account_deletion_summary(user):
    from apps.vendor.models import Product

    establishment_count = Establishment.objects.filter(owner=user).count()
    product_count = Product.objects.filter(establishment__owner=user).count()
    return {
        'establishment_count': establishment_count,
        'product_count': product_count,
        'favorite_count': user.product_favorites.count(),
        'review_count': user.establishment_reviews.count(),
        'has_vendor_content': establishment_count > 0,
        'has_activity': (
            establishment_count > 0
            or user.product_favorites.exists()
            or user.establishment_reviews.exists()
        ),
    }


def delete_user_account(user):
    with transaction.atomic():
        user.delete()


def complete_session_after_account_deletion(request, *, success_message):
    refresh_token = request.COOKIES.get(REFRESH_COOKIE)
    if refresh_token:
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            pass

    logout(request)
    response = redirect('auth')
    messages.success(request, success_message, extra_tags='general')
    return clear_jwt_cookies(response)
