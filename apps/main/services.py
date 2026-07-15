from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.vendor.models import Establishment

from .models import UserRole
from .validators import MIN_VENDOR_AGE, user_meets_min_age

User = get_user_model()


def suspend_establishments_for_admin_role(user):
    """Legado: já não é usado na promoção. Mantido para limpeza de dados antigos."""
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
    """Adiciona o perfil administrador sem remover cliente/vendedor."""
    user.add_role(UserRole.Role.ADMINISTRADOR)
    if not user.is_cliente and not user.is_vendedor:
        assign_cliente_role(user)


def has_system_admin():
    return UserRole.objects.filter(role=UserRole.Role.ADMINISTRADOR).exists()


def ensure_system_admin():
    from django.conf import settings

    if not getattr(settings, 'AUTO_PROMOTE_FIRST_USER', False):
        return None

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
        assign_cliente_role(user)
        ensure_system_admin()
        user.refresh_from_db()
        return user


def promote_to_admin(user):
    assign_admin_role(user)


def _clear_user_role_cache(user):
    if hasattr(user, '_role_values_cache'):
        del user._role_values_cache


def demote_from_admin(user):
    user.user_roles.filter(role=UserRole.Role.ADMINISTRADOR).delete()
    _clear_user_role_cache(user)
    if not user.is_cliente and not user.is_vendedor:
        assign_cliente_role(user)
    restore_establishments_after_admin_demote(user)


def get_post_login_redirect_name(user):
    """Todos entram como cliente; o painel admin é acesso opcional."""
    return 'home'


def administrator_count():
    return (
        User.objects
        .filter(user_roles__role=UserRole.Role.ADMINISTRADOR)
        .distinct()
        .count()
    )


def active_administrator_count():
    return (
        User.objects
        .filter(is_active=True, user_roles__role=UserRole.Role.ADMINISTRADOR)
        .distinct()
        .count()
    )


def get_admin_account_deletion_block_reason(target, actor):
    if target.pk == actor.pk:
        return 'Não pode apagar a sua própria conta.'
    if target.is_administrador and administrator_count() <= 1:
        return 'Não pode apagar o último administrador do sistema.'
    return None


def get_admin_account_deactivate_block_reason(target, actor):
    if target.pk == actor.pk:
        return 'Não pode bloquear a sua própria conta.'
    if (
        target.is_administrador
        and target.is_active
        and active_administrator_count() <= 1
    ):
        return 'Não pode bloquear o último administrador ativo do sistema.'
    return None


def get_self_account_deletion_block_reason(user):
    if user.is_administrador and administrator_count() <= 1:
        return 'Não pode eliminar a conta: é o último administrador do sistema.'
    return None


def delete_user_account(user):
    with transaction.atomic():
        user.delete()
