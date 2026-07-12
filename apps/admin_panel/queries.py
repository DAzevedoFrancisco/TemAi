from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from apps.main.models import UserRole
from apps.vendor.models import Establishment, Product

User = get_user_model()

USER_SORT_FIELDS = {
    'name': 'name',
    'date': 'date_joined',
    'email': 'email',
}

ESTABLISHMENT_SORT_FIELDS = {
    'name': 'name',
    'date': 'created_at',
    'owner': 'owner__name',
}

RECENT_DASHBOARD_LIMIT = 5


def get_dashboard_stats():
    users = User.objects.all()
    establishments = Establishment.objects.all()
    return {
        'users_total': users.count(),
        'users_active': users.filter(is_active=True).count(),
        'users_blocked': users.filter(is_active=False).count(),
        'clients_count': users.filter(user_roles__role=UserRole.Role.CLIENTE).distinct().count(),
        'vendors_count': users.filter(user_roles__role=UserRole.Role.VENDEDOR).distinct().count(),
        'admins_count': users.filter(
            user_roles__role=UserRole.Role.ADMINISTRADOR
        ).distinct().count(),
        'establishments_total': establishments.count(),
        'establishments_active': establishments.filter(is_active=True).count(),
        'establishments_blocked': establishments.filter(is_active=False).count(),
        'products_count': Product.objects.count(),
    }


def get_filtered_users(*, role='', gender='', status='', sort='date', order='desc'):
    queryset = User.objects.prefetch_related('user_roles').all()

    if role == UserRole.Role.CLIENTE:
        queryset = queryset.filter(user_roles__role=UserRole.Role.CLIENTE)
    elif role == UserRole.Role.VENDEDOR:
        queryset = queryset.filter(user_roles__role=UserRole.Role.VENDEDOR)
    elif role == UserRole.Role.ADMINISTRADOR:
        queryset = queryset.filter(user_roles__role=UserRole.Role.ADMINISTRADOR)

    if gender in User.Gender.values:
        queryset = queryset.filter(gender=gender)

    if status == 'active':
        queryset = queryset.filter(is_active=True)
    elif status == 'blocked':
        queryset = queryset.filter(is_active=False)

    sort_field = USER_SORT_FIELDS.get(sort, 'date_joined')
    if order == 'asc':
        queryset = queryset.order_by(sort_field)
    else:
        queryset = queryset.order_by(f'-{sort_field}')

    return queryset.distinct()


def get_filtered_establishments(*, status='', sort='date', order='desc', query=''):
    queryset = (
        Establishment.objects
        .select_related('owner')
        .annotate(products_count=Count('products'))
    )

    if status == 'active':
        queryset = queryset.filter(is_active=True)
    elif status == 'blocked':
        queryset = queryset.filter(is_active=False)

    if query:
        queryset = queryset.filter(
            Q(name__icontains=query)
            | Q(address__icontains=query)
            | Q(owner__name__icontains=query)
            | Q(owner__email__icontains=query)
        )

    sort_field = ESTABLISHMENT_SORT_FIELDS.get(sort, 'created_at')
    if order == 'asc':
        queryset = queryset.order_by(sort_field)
    else:
        queryset = queryset.order_by(f'-{sort_field}')

    return queryset


def get_recent_users(limit=RECENT_DASHBOARD_LIMIT):
    return get_filtered_users(sort='date', order='desc')[:limit]


def get_recent_establishments(limit=RECENT_DASHBOARD_LIMIT):
    return get_filtered_establishments(sort='date', order='desc')[:limit]


def get_system_admins():
    return (
        User.objects
        .filter(user_roles__role=UserRole.Role.ADMINISTRADOR)
        .prefetch_related('user_roles')
        .distinct()
        .order_by('name')
    )
