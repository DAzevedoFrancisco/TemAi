from django.db.models import Avg, Count

from .models import EstablishmentReview, ProductFavorite


def user_owns_establishment(user, establishment):
    return user.is_authenticated and establishment.owner_id == user.id


def can_client_engage_product(user, product):
    if not user.is_authenticated:
        return False
    return not user_owns_establishment(user, product.establishment)


def is_product_favorited(user, product):
    if not user.is_authenticated:
        return False
    return ProductFavorite.objects.filter(user=user, product=product).exists()


def toggle_product_favorite(user, product):
    favorite, created = ProductFavorite.objects.get_or_create(user=user, product=product)
    if not created:
        favorite.delete()
        return False
    return True


def get_user_favorite_products(user):
    return (
        ProductFavorite.objects
        .filter(user=user, product__is_active=True, product__establishment__is_active=True)
        .select_related('product__establishment', 'product__category')
    )


def get_establishment_review_stats(establishment):
    stats = (
        EstablishmentReview.objects
        .filter(establishment=establishment, status=EstablishmentReview.Status.APPROVED)
        .aggregate(avg_rating=Avg('rating'), total=Count('id'))
    )
    return {
        'avg_rating': stats['avg_rating'] or 0,
        'total': stats['total'] or 0,
    }


def get_approved_reviews(establishment, limit=None):
    queryset = (
        EstablishmentReview.objects
        .filter(establishment=establishment, status=EstablishmentReview.Status.APPROVED)
        .select_related('user')
    )
    if limit:
        return queryset[:limit]
    return queryset


def get_user_review(user, establishment):
    if not user.is_authenticated:
        return None
    return EstablishmentReview.objects.filter(user=user, establishment=establishment).first()
