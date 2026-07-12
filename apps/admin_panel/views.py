from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.main.models import UserRole
from apps.main.services import (
    delete_user_account,
    demote_from_admin,
    get_admin_account_deletion_block_reason,
    promote_to_admin,
)
from apps.main.search import get_establishment_coordinates
from apps.vendor.models import Establishment

from .decorators import administrador_required
from .forms import PromoteAdminForm
from .queries import (
    get_dashboard_stats,
    get_filtered_establishments,
    get_filtered_users,
    get_recent_establishments,
    get_recent_users,
    get_system_admins,
)

User = get_user_model()


def _active_admin_count():
    return (
        User.objects
        .filter(is_active=True, user_roles__role=UserRole.Role.ADMINISTRADOR)
        .distinct()
        .count()
    )


def _admin_role_count():
    return (
        User.objects
        .filter(user_roles__role=UserRole.Role.ADMINISTRADOR)
        .distinct()
        .count()
    )


@administrador_required
def dashboard(request):
    stats = get_dashboard_stats()
    recent_users = get_recent_users()
    recent_establishments = get_recent_establishments()
    return render(request, 'admin_panel/dashboard.html', {
        **stats,
        'recent_users': recent_users,
        'recent_establishments': recent_establishments,
    })


@administrador_required
def admin_users(request):
    system_admins = get_system_admins()
    return render(request, 'admin_panel/admin_users.html', {
        'promote_form': PromoteAdminForm(),
        'system_admins': system_admins,
        'admins_total': system_admins.count(),
        'admins_active_count': system_admins.filter(is_active=True).count(),
        'admins_blocked_count': system_admins.filter(is_active=False).count(),
    })


def _handle_promote_admin(request, email):
    target = User.objects.filter(email__iexact=email).first()
    if target is None:
        messages.error(
            request,
            'Não existe nenhuma conta com esse email. O utilizador deve registar-se primeiro.',
            extra_tags='admin',
        )
        return redirect('admin_panel:admin_users')

    if target.has_role(UserRole.Role.ADMINISTRADOR):
        messages.info(request, f'"{target.email}" já é administrador do sistema.', extra_tags='admin')
        return redirect('admin_panel:admin_users')

    promote_to_admin(target)
    messages.success(
        request,
        f'"{target.name}" ({target.email}) foi promovido a administrador. Os outros perfis foram removidos.',
        extra_tags='admin',
    )
    return redirect('admin_panel:admin_users')


@administrador_required
@require_POST
def promote_admin(request):
    form = PromoteAdminForm(request.POST)
    if not form.is_valid():
        for error in form.errors.get('email', ['Email inválido.']):
            messages.error(request, error, extra_tags='admin')
        return redirect(request.POST.get('next') or 'admin_panel:admin_users')

    return _handle_promote_admin(request, form.cleaned_data['email'])


@administrador_required
@require_POST
def demote_admin(request, pk):
    target = get_object_or_404(User, pk=pk)

    if target.pk == request.user.pk:
        messages.error(request, 'Não pode despromover a sua própria conta.', extra_tags='admin')
        return redirect('admin_panel:admin_users')

    if not target.has_role(UserRole.Role.ADMINISTRADOR):
        messages.info(request, f'"{target.email}" já não é administrador.', extra_tags='admin')
        return redirect('admin_panel:admin_users')

    if _active_admin_count() <= 1:
        messages.error(
            request,
            'Não pode despromover o último administrador ativo do sistema.',
            extra_tags='admin',
        )
        return redirect('admin_panel:admin_users')

    demote_from_admin(target)
    messages.success(
        request,
        f'"{target.name}" ({target.email}) foi despromovido e voltou a ser cliente.',
        extra_tags='admin',
    )
    return redirect(request.POST.get('next') or 'admin_panel:admin_users')


@administrador_required
def user_list(request):
    role = request.GET.get('role', '')
    gender = request.GET.get('gender', '')
    status = request.GET.get('status', '')
    sort = request.GET.get('sort', 'date')
    order = request.GET.get('order', 'desc')

    users = get_filtered_users(
        role=role,
        gender=gender,
        status=status,
        sort=sort,
        order=order,
    )

    return render(request, 'admin_panel/user_list.html', {
        'users': users,
        'users_total': users.count(),
        'users_active_count': users.filter(is_active=True).count(),
        'users_blocked_count': users.filter(is_active=False).count(),
        'users_admins_count': users.filter(
            user_roles__role=UserRole.Role.ADMINISTRADOR
        ).distinct().count(),
        'filters': {
            'role': role,
            'gender': gender,
            'status': status,
            'sort': sort,
            'order': order,
        },
        'role_choices': UserRole.Role.choices,
        'gender_choices': User.Gender.choices,
    })


@administrador_required
@require_POST
def user_toggle_active(request, pk):
    target = get_object_or_404(User, pk=pk)

    if target.pk == request.user.pk:
        messages.error(request, 'Não pode bloquear a sua própria conta.', extra_tags='admin')
        return redirect('admin_panel:user_list')

    target.is_active = not target.is_active
    target.save(update_fields=['is_active'])

    if target.is_active:
        messages.success(request, f'Utilizador "{target.name}" foi desbloqueado.', extra_tags='admin')
    else:
        messages.info(request, f'Utilizador "{target.name}" foi bloqueado.', extra_tags='admin')

    return redirect(request.POST.get('next') or 'admin_panel:user_list')


@administrador_required
@require_POST
def user_delete(request, pk):
    target = get_object_or_404(User, pk=pk)

    block_reason = get_admin_account_deletion_block_reason(target, request.user)
    if block_reason:
        messages.error(request, block_reason, extra_tags='admin')
        return redirect(request.POST.get('next') or 'admin_panel:user_list')

    name = target.name
    delete_user_account(target)
    messages.success(request, f'Utilizador "{name}" foi apagado.', extra_tags='admin')
    return redirect(request.POST.get('next') or 'admin_panel:user_list')


@administrador_required
def establishment_list(request):
    status = request.GET.get('status', '')
    sort = request.GET.get('sort', 'date')
    order = request.GET.get('order', 'desc')
    query = request.GET.get('q', '').strip()

    establishments = get_filtered_establishments(
        status=status,
        sort=sort,
        order=order,
        query=query,
    )
    products_total = sum(item.products_count for item in establishments)

    return render(request, 'admin_panel/establishment_list.html', {
        'establishments': establishments,
        'establishments_total': establishments.count(),
        'establishments_active_count': establishments.filter(is_active=True).count(),
        'establishments_blocked_count': establishments.filter(is_active=False).count(),
        'products_total': products_total,
        'filters': {
            'status': status,
            'sort': sort,
            'order': order,
            'q': query,
        },
    })


@administrador_required
def establishment_detail(request, pk):
    establishment = get_object_or_404(
        Establishment.objects.select_related('owner').annotate(products_count=Count('products')),
        pk=pk,
    )
    establishment_lat, establishment_lng = get_establishment_coordinates(establishment)
    return render(request, 'admin_panel/establishment_detail.html', {
        'establishment': establishment,
        'establishment_lat': establishment_lat,
        'establishment_lng': establishment_lng,
    })


@administrador_required
@require_POST
def establishment_toggle_active(request, pk):
    establishment = get_object_or_404(Establishment, pk=pk)
    establishment.is_active = not establishment.is_active
    establishment.save(update_fields=['is_active', 'updated_at'])

    if establishment.is_active:
        messages.success(
            request,
            f'Estabelecimento "{establishment.name}" foi desbloqueado.',
            extra_tags='admin',
        )
    else:
        messages.info(
            request,
            f'Estabelecimento "{establishment.name}" foi bloqueado.',
            extra_tags='admin',
        )

    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('admin_panel:establishment_list')


@administrador_required
@require_POST
def establishment_delete(request, pk):
    establishment = get_object_or_404(Establishment, pk=pk)
    name = establishment.name
    establishment.delete()
    messages.success(request, f'Estabelecimento "{name}" foi apagado.', extra_tags='admin')

    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('admin_panel:establishment_list')
