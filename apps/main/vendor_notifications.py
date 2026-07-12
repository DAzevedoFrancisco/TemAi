from django.utils import timezone

from .models import EstablishmentReview


def get_vendor_reviews_queryset(user):
    return (
        EstablishmentReview.objects
        .filter(
            establishment__owner=user,
            status=EstablishmentReview.Status.APPROVED,
        )
        .select_related('user', 'establishment', 'product', 'product__category')
    )


def get_unread_review_count(user):
    if not user.is_authenticated or not user.is_vendedor:
        return 0
    return get_vendor_reviews_queryset(user).filter(viewed_by_vendor_at__isnull=True).count()


def mark_vendor_reviews_read(user, establishment=None):
    queryset = get_vendor_reviews_queryset(user).filter(viewed_by_vendor_at__isnull=True)
    if establishment is not None:
        queryset = queryset.filter(establishment=establishment)
    queryset.update(viewed_by_vendor_at=timezone.now())


def mark_single_review_read(user, review_pk):
    review = get_vendor_reviews_queryset(user).filter(pk=review_pk, viewed_by_vendor_at__isnull=True).first()
    if review is None:
        return False
    review.viewed_by_vendor_at = timezone.now()
    review.save(update_fields=['viewed_by_vendor_at'])
    return True
