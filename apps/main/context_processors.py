from apps.main.profile import get_active_profile
from apps.main.vendor_notifications import get_unread_review_count


def profile_context(request):
    return {
        'active_profile': get_active_profile(request),
        'vendor_unread_reviews': get_unread_review_count(request.user),
    }