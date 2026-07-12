from apps.main.profile import (
    can_use_client_catalog,
    get_active_profile,
    get_client_nav_home_url,
)
from apps.main.vendor_notifications import get_unread_review_count


def profile_context(request):
    return {
        'active_profile': get_active_profile(request),
        'can_use_client_catalog': can_use_client_catalog(request),
        'client_nav_home_url': get_client_nav_home_url(request),
        'vendor_unread_reviews': get_unread_review_count(request.user),
    }