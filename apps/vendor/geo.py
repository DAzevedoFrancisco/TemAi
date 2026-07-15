from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

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


def haversine_km(lat1, lng1, lat2, lng2):
    """Distância aproximada em km entre dois pontos (fórmula de Haversine)."""
    try:
        lat1_f = float(lat1)
        lng1_f = float(lng1)
        lat2_f = float(lat2)
        lng2_f = float(lng2)
    except (TypeError, ValueError):
        return None

    earth_radius_km = 6371.0
    d_lat = radians(lat2_f - lat1_f)
    d_lng = radians(lng2_f - lng1_f)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1_f)) * cos(radians(lat2_f)) * sin(d_lng / 2) ** 2
    )
    return earth_radius_km * 2 * asin(sqrt(a))


def format_distance_km(distance_km):
    if distance_km is None:
        return None
    if distance_km < 1:
        return f'{int(round(distance_km * 1000))} m'
    if distance_km < 10:
        return f'{distance_km:.1f} km'
    return f'{int(round(distance_km))} km'


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
