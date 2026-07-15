from urllib.parse import urlencode

import logging

from django.db import transaction

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.main.profile import Profile, set_active_profile
from apps.main.services import assign_vendedor_role
from apps.main.validators import MIN_VENDOR_AGE, calculate_age, can_become_seller
from django.views.decorators.http import require_POST

from apps.main.vendor_notifications import (
    get_unread_review_count,
    get_vendor_reviews_queryset,
    mark_single_review_read,
    mark_vendor_reviews_read,
)

from .decorators import login_required_view, vendedor_required
from .forms import EstablishmentForm, ProductForm
from .models import Establishment, Product

logger = logging.getLogger(__name__)


def _save_product_from_form(form, establishment):
    product = form.save(commit=False)
    product.establishment = establishment
    with transaction.atomic():
        product.save()
    return product


def _product_image_save_error_message():
    from django.conf import settings

    if settings.USE_CLOUDINARY:
        return (
            'Não foi possível enviar a imagem do produto. '
            'Confirme as credenciais Cloudinary no servidor ou contacte o suporte.'
        )
    return 'Não foi possível guardar a imagem do produto. Tente novamente com outro ficheiro.'


def _handle_product_form_submission(request, *, form, establishment, success_message, redirect_url):
    if request.method != 'POST' or not form.is_valid():
        return None

    try:
        if establishment is not None:
            _save_product_from_form(form, establishment)
        else:
            with transaction.atomic():
                form.save()
    except Exception:
        logger.exception('Failed to save product for establishment %s', getattr(establishment, 'pk', None))
        messages.error(
            request,
            _product_image_save_error_message(),
            extra_tags='vendor',
        )
        return None

    messages.success(request, success_message, extra_tags='vendor')
    return redirect(redirect_url)


@login_required_view
def become_seller(request):
    if request.user.is_vendedor:
        set_active_profile(request, Profile.VENDEDOR)
        if request.user.establishments.exists():
            return redirect('vendor:dashboard')
        return redirect('vendor:establishment_create')

    eligible = can_become_seller(request.user)
    user_age = calculate_age(request.user.date_of_birth)

    if request.method == 'POST':
        if not eligible:
            messages.error(
                request,
                f'Precisa de ter pelo menos {MIN_VENDOR_AGE} anos para se tornar vendedor.',
                extra_tags='vendor',
            )
            return redirect('vendor:become_seller')

        from apps.main.search import parse_user_coordinates
        from apps.vendor.geo import is_within_beira

        user_lat, user_lng = parse_user_coordinates(
            request.POST.get('lat'),
            request.POST.get('lng'),
        )
        if user_lat is None or user_lng is None:
            messages.error(
                request,
                'É obrigatório autorizar a localização GPS para se tornar vendedor.',
                extra_tags='vendor',
            )
            return redirect('vendor:become_seller')

        if not is_within_beira(user_lat, user_lng):
            messages.error(
                request,
                'A sua localização está fora da cidade da Beira. Só pode tornar-se vendedor na Beira.',
                extra_tags='vendor',
            )
            return redirect('vendor:become_seller')

        assign_vendedor_role(request.user)
        messages.success(request, 'Perfil de vendedor atribuído com sucesso!', extra_tags='vendor')
        set_active_profile(request, Profile.VENDEDOR)

        if request.user.establishments.exists():
            return redirect('vendor:dashboard')
        return redirect('vendor:establishment_create')

    return render(request, 'main/become_seller.html', {
        'eligible': eligible,
        'min_vendor_age': MIN_VENDOR_AGE,
        'user_age': user_age,
    })


@vendedor_required
def dashboard(request):
    establishments = request.user.establishments.prefetch_related('products')
    products_qs = Product.objects.filter(establishment__owner=request.user)
    products_count = products_qs.count()
    categories_count = products_qs.values('category').distinct().count()

    return render(request, 'vendor/dashboard.html', {
        'establishments': establishments,
        'establishments_count': establishments.count(),
        'products_count': products_count,
        'categories_count': categories_count,
    })


@vendedor_required
def review_inbox(request):
    reviews = get_vendor_reviews_queryset(request.user)
    return render(request, 'vendor/review_inbox.html', {
        'reviews': reviews,
        'unread_reviews_count': get_unread_review_count(request.user),
    })


@vendedor_required
@require_POST
def mark_reviews_read(request):
    mark_vendor_reviews_read(request.user)
    messages.success(request, 'Todos os comentários foram marcados como lidos.', extra_tags='vendor')
    return redirect('vendor:review_inbox')


@vendedor_required
@require_POST
def mark_review_read(request, pk):
    if mark_single_review_read(request.user, pk):
        messages.success(request, 'Comentário marcado como lido.', extra_tags='vendor')
    else:
        messages.info(request, 'Comentário já estava marcado como lido.', extra_tags='vendor')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('vendor:review_inbox')


@vendedor_required
def establishment_list(request):
    establishments = request.user.establishments.prefetch_related('products')
    products_count = Product.objects.filter(establishment__owner=request.user).count()
    return render(request, 'vendor/establishment_list.html', {
        'establishments': establishments,
        'products_count': products_count,
    })


@vendedor_required
def establishment_create(request):
    form = EstablishmentForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        establishment = form.save(commit=False)
        establishment.owner = request.user
        establishment.save()
        messages.success(request, 'Estabelecimento cadastrado com sucesso!', extra_tags='vendor')
        return redirect('vendor:dashboard')

    return render(request, 'vendor/establishment_form.html', {
        'form': form,
        'title': 'Cadastrar estabelecimento',
        'is_edit': False,
    })


@vendedor_required
def establishment_edit(request, pk):
    establishment = get_object_or_404(Establishment, pk=pk, owner=request.user)
    form = EstablishmentForm(request.POST or None, instance=establishment)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Estabelecimento atualizado com sucesso!', extra_tags='vendor')
        return redirect('vendor:establishment_list')

    return render(request, 'vendor/establishment_form.html', {
        'form': form,
        'title': 'Editar estabelecimento',
        'is_edit': True,
        'establishment': establishment,
    })


@vendedor_required
def product_list(request, pk):
    establishment = get_object_or_404(Establishment, pk=pk, owner=request.user)
    all_products = establishment.products.select_related('category')
    products_count = all_products.count()
    available_count = all_products.filter(is_available=True).count()
    categories_count = all_products.values('category').distinct().count()

    query = request.GET.get('q', '').strip()
    availability = request.GET.get('disponibilidade', '').strip()

    products = all_products
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

    if availability == 'disponivel':
        products = products.filter(is_available=True)
    elif availability == 'indisponivel':
        products = products.filter(is_available=False)

    return render(request, 'vendor/product_list.html', {
        'establishment': establishment,
        'products': products,
        'products_count': products_count,
        'filtered_count': products.count(),
        'available_count': available_count,
        'categories_count': categories_count,
        'query': query,
        'active_availability': availability,
    })


@vendedor_required
def product_create(request, est_pk):
    establishment = get_object_or_404(Establishment, pk=est_pk, owner=request.user)
    form = ProductForm(request.POST or None, request.FILES or None)

    response = _handle_product_form_submission(
        request,
        form=form,
        establishment=establishment,
        success_message='Produto cadastrado com sucesso!',
        redirect_url=reverse('vendor:product_list', kwargs={'pk': establishment.pk}),
    )
    if response is not None:
        return response

    return render(request, 'vendor/product_form.html', {
        'form': form,
        'establishment': establishment,
        'title': 'Novo produto',
        'is_edit': False,
    })


@vendedor_required
def product_edit(request, pk):
    product = get_object_or_404(
        Product,
        pk=pk,
        establishment__owner=request.user,
    )
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)

    response = _handle_product_form_submission(
        request,
        form=form,
        establishment=None,
        success_message='Produto atualizado com sucesso!',
        redirect_url=reverse('vendor:product_list', kwargs={'pk': product.establishment.pk}),
    )
    if response is not None:
        return response

    return render(request, 'vendor/product_form.html', {
        'form': form,
        'establishment': product.establishment,
        'title': 'Editar produto',
        'is_edit': True,
        'product': product,
    })


@vendedor_required
def product_toggle_availability(request, pk):
    product = get_object_or_404(
        Product,
        pk=pk,
        establishment__owner=request.user,
    )

    if request.method == 'POST':
        product.is_available = not product.is_available
        product.save(update_fields=['is_available', 'updated_at'])
        status = 'disponível' if product.is_available else 'indisponível'
        messages.success(request, f'Produto marcado como {status}.', extra_tags='vendor')

    redirect_params = {}
    query = request.POST.get('q', '').strip()
    availability = request.POST.get('disponibilidade', '').strip()
    if query:
        redirect_params['q'] = query
    if availability in ('disponivel', 'indisponivel'):
        redirect_params['disponibilidade'] = availability

    list_url = reverse('vendor:product_list', kwargs={'pk': product.establishment.pk})
    if redirect_params:
        list_url = f'{list_url}?{urlencode(redirect_params)}'

    return redirect(list_url)


@vendedor_required
def product_delete(request, pk):
    product = get_object_or_404(
        Product,
        pk=pk,
        establishment__owner=request.user,
    )
    establishment_pk = product.establishment.pk

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Produto eliminado com sucesso!', extra_tags='vendor')
        return redirect('vendor:product_list', pk=establishment_pk)

    return render(request, 'vendor/product_confirm_delete.html', {
        'product': product,
        'establishment': product.establishment,
    })
