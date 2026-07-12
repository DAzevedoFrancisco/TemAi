from decimal import Decimal

BEIRA_CENTER_LAT = Decimal('-19.843600')
BEIRA_CENTER_LNG = Decimal('34.838900')

BEIRA_BOUNDS = {
    'lat_min': Decimal('-19.902000'),
    'lat_max': Decimal('-19.768000'),
    'lng_min': Decimal('34.802000'),
    'lng_max': Decimal('34.928000'),
}


def _to_decimal(value):
    return Decimal(str(value))


def is_within_beira(latitude, longitude):
    lat = _to_decimal(latitude)
    lng = _to_decimal(longitude)
    return (
        BEIRA_BOUNDS['lat_min'] <= lat <= BEIRA_BOUNDS['lat_max']
        and BEIRA_BOUNDS['lng_min'] <= lng <= BEIRA_BOUNDS['lng_max']
    )


def _is_mozambique_latitude(value):
    return -27 <= value <= -10


def _is_mozambique_longitude(value):
    return 30 <= value <= 42


def fix_swapped_coordinates(latitude, longitude):
    """
    Corrige lat/lng trocados (comum em APIs e formulários).
    Retorna (None, None) quando os valores não são coordenadas válidas.
    """
    if latitude is None or longitude is None:
        return None, None

    try:
        lat = float(latitude)
        lng = float(longitude)
    except (TypeError, ValueError):
        return None, None

    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None, None

    if _is_mozambique_longitude(lat) and _is_mozambique_latitude(lng):
        lat, lng = lng, lat
    elif abs(lat) > abs(lng) and abs(lat) >= 30 and abs(lng) <= 27:
        lat, lng = lng, lat

    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None, None

    return lat, lng
