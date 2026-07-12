from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import UserRole
from .validators import MIN_VENDOR_AGE, user_meets_min_age

User = get_user_model()


def assign_cliente_role(user):
    user.add_role(UserRole.Role.CLIENTE)


def assign_vendedor_role(user):
    if not user_meets_min_age(user, MIN_VENDOR_AGE):
        raise ValidationError(
            f'Precisa de ter pelo menos {MIN_VENDOR_AGE} anos para se tornar vendedor.'
        )
    user.add_role(UserRole.Role.VENDEDOR)


def assign_admin_role(user):
    user.user_roles.all().delete()
    user.add_role(UserRole.Role.ADMINISTRADOR)


def register_user_with_default_role(*, email, password, name, date_of_birth, gender):
    with transaction.atomic():
        first_user = not User.objects.select_for_update().exists()
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            date_of_birth=date_of_birth,
            gender=gender,
        )
        if first_user:
            assign_admin_role(user)
        else:
            assign_cliente_role(user)
        return user


def promote_to_admin(user):
    assign_admin_role(user)


def demote_from_admin(user):
    user.user_roles.all().delete()
    assign_cliente_role(user)


def get_post_login_redirect_name(user):
    if user.is_administrador:
        return 'admin_panel:dashboard'
    return 'home'
