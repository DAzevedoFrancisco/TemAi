from urllib.parse import urlencode

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse

from apps.vendor.geo import fix_swapped_coordinates, is_within_beira
from apps.vendor.models import Category, Product


def public_products_queryset():
    return Product.objects.filter(
        is_active=True,
        establishment__is_active=True,
        category__is_active=True,
    ).select_related('establishment', 'category')


def normalize_establishment_coordinates(lat, lng):
    return fix_swapped_coordinates(lat, lng)


def get_establishment_coordinates(establishment):
    lat = float(establishment.latitude)
    lng = float(establishment.longitude)
    fixed_lat, fixed_lng = normalize_establishment_coordinates(lat, lng)
    if fixed_lat is None:
        return lat, lng
    return fixed_lat, fixed_lng


def search_products(query, category_slug=None):
    queryset = public_products_queryset()
    term = (query or '').strip()

    if not term:
        return queryset.none()

    queryset = queryset.filter(
        Q(name__icontains=term)
        | Q(description__icontains=term)
    )

    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)

    return queryset


def get_search_categories(query):
    term = (query or '').strip()
    if not term:
        return Category.objects.none()

    category_ids = search_products(term).values_list('category_id', flat=True).distinct()
    if not category_ids:
        return Category.objects.none()

    return Category.objects.filter(
        id__in=category_ids,
        is_active=True,
    ).order_by('name')


def build_search_map_markers(products, query='', category_slug=''):
    """Agrupa produtos por loja para o mapa dos resultados da pesquisa."""
    stores = {}
    for product in products:
        establishment = product.establishment
        store_id = establishment.pk
        if store_id not in stores:
            lat, lng = get_establishment_coordinates(establishment)
            stores[store_id] = {
                'id': store_id,
                'lat': lat,
                'lng': lng,
                'name': establishment.name,
                'address': establishment.address or '',
                'products': [],
            }

        detail_url = reverse('product_detail', kwargs={'pk': product.pk})
        params = {}
        if query:
            params['q'] = query
        if category_slug:
            params['categoria'] = category_slug
        if params:
            detail_url = f'{detail_url}?{urlencode(params)}'

        stores[store_id]['products'].append({
            'id': product.pk,
            'name': product.name,
            'url': detail_url,
            'available': product.is_available,
        })

    return list(stores.values())


def get_public_product(pk):
    return get_object_or_404(public_products_queryset(), pk=pk)


def establishment_is_within_beira(establishment):
    lat, lng = get_establishment_coordinates(establishment)
    return is_within_beira(lat, lng)
