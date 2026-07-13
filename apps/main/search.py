import math

from django.db.models import Q
from django.shortcuts import get_object_or_404

from apps.vendor.geo import fix_swapped_coordinates, is_within_beira
from apps.vendor.models import Category, Product

DISTANCE_FILTER_OPTIONS = (
    (None, 'Todas'),
    (2, '2 km'),
    (5, '5 km'),
    (10, '10 km'),
    (25, '25 km'),
)


def public_products_queryset():
    return Product.objects.filter(
        is_active=True,
        establishment__is_active=True,
        category__is_active=True,
    ).select_related('establishment', 'category')


def parse_coordinate(value):
    if value in (None, ''):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_user_coordinates(lat, lng):
    """
    Corrige lat/lng trocados para a localização do utilizador.
    Aceita qualquer ponto válido no globo (ex.: Chota, Chimoio, etc.).
    """
    return fix_swapped_coordinates(lat, lng)


def normalize_establishment_coordinates(lat, lng):
    """
    Corrige lat/lng trocados para o estabelecimento.
    Mantém o ponto mesmo fora da Beira para não distorcer distâncias antigas.
    """
    return fix_swapped_coordinates(lat, lng)


def parse_search_coordinates(lat_value, lng_value):
    return normalize_user_coordinates(
        parse_coordinate(lat_value),
        parse_coordinate(lng_value),
    )


def parse_authenticated_user_coordinates(request):
    if not request.user.is_authenticated:
        return None, None
    return parse_search_coordinates(
        request.GET.get('lat'),
        request.GET.get('lng'),
    )


def parse_authenticated_distance_km(request):
    if not request.user.is_authenticated:
        return None
    return parse_distance_km(request.GET.get('distancia'))


def parse_distance_km(value):
    if value in (None, ''):
        return None
    try:
        distance = int(value)
    except (TypeError, ValueError):
        return None
    if distance <= 0:
        return None
    return distance


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def get_establishment_coordinates(establishment):
    lat = float(establishment.latitude)
    lng = float(establishment.longitude)
    fixed_lat, fixed_lng = normalize_establishment_coordinates(lat, lng)
    if fixed_lat is None:
        return lat, lng
    return fixed_lat, fixed_lng


def calculate_distance_km(user_lat, user_lng, establishment):
    user_lat, user_lng = normalize_user_coordinates(user_lat, user_lng)
    if user_lat is None or user_lng is None:
        return None

    establishment_lat, establishment_lng = get_establishment_coordinates(establishment)
    return haversine_km(user_lat, user_lng, establishment_lat, establishment_lng)


def search_products(query, category_slug=None):
    queryset = public_products_queryset()
    term = (query or '').strip()

    if not term:
        return queryset.none()

    queryset = queryset.filter(
        Q(name__icontains=term)
        | Q(description__icontains=term)
        | Q(category__name__icontains=term)
    )

    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)

    return queryset


def apply_distance_filter(products, user_lat=None, user_lng=None, max_distance_km=None):
    user_lat, user_lng = normalize_user_coordinates(user_lat, user_lng)
    if user_lat is None or user_lng is None:
        return [(product, None) for product in products]

    results = []
    for product in products:
        distance_km = calculate_distance_km(
            user_lat,
            user_lng,
            product.establishment,
        )

        if max_distance_km is None or distance_km <= max_distance_km:
            results.append((product, distance_km))

    results.sort(key=lambda item: item[1] if item[1] is not None else float('inf'))
    return results


def search_products_with_distance(
    query,
    category_slug=None,
    user_lat=None,
    user_lng=None,
    max_distance_km=None,
):
    queryset = search_products(query, category_slug=category_slug)
    return apply_distance_filter(
        queryset,
        user_lat=user_lat,
        user_lng=user_lng,
        max_distance_km=max_distance_km,
    )


def get_search_categories(query, user_lat=None, user_lng=None, max_distance_km=None):
    term = (query or '').strip()
    if not term:
        return Category.objects.none()

    product_pairs = search_products_with_distance(
        term,
        user_lat=user_lat,
        user_lng=user_lng,
        max_distance_km=max_distance_km,
    )
    category_ids = {product.category_id for product, _ in product_pairs}
    if not category_ids:
        return Category.objects.none()

    return Category.objects.filter(
        id__in=category_ids,
        is_active=True,
    ).order_by('name')


def get_public_product(pk):
    return get_object_or_404(public_products_queryset(), pk=pk)


def establishment_is_within_beira(establishment):
    lat, lng = get_establishment_coordinates(establishment)
    return is_within_beira(lat, lng)
