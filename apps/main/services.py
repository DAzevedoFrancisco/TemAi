from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.vendor.models import Establishment

from .models import UserRole
from .validators import MIN_VENDOR_AGE, user_meets_min_age

User = get_user_model()


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
