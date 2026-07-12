from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.main.profile import Profile, get_active_profile
from apps.vendor.decorators import login_required_view, vendedor_required
from apps.vendor.models import Establishment

from .engagement import (
    can_client_engage_product,
    get_approved_reviews,
    get_establishment_review_stats,
    get_user_favorite_products,
    get_user_review,
    is_product_favorited,
    toggle_product_favorite as apply_product_favorite_toggle,
    user_owns_establishment,
)
from .forms import EstablishmentReviewForm
from .models import EstablishmentReview
from .vendor_notifications import get_unread_review_count, get_vendor_reviews_queryset, mark_vendor_reviews_read


def _product_detail_redirect(product, request):
    params = request.GET.urlencode()
    url = reverse('product_detail', kwargs={'pk': product.pk})
    if params:
        url = f'{url}?{params}'
    return redirect(url)


@login_required_view
def favorites_list(request):
    if get_active_profile(request) == Profile.VENDEDOR:
        return redirect('vendor:dashboard')

    favorites = get_user_favorite_products(request.user)
    return render(request, 'main/favorites.html', {
        'favorites': favorites,
    })


@login_required_view
@require_POST
def toggle_product_favorite(request, pk):
    product = get_public_product(pk)

    if not can_client_engage_product(request.user, product):
        messages.error(request, 'Não pode favoritar produtos do seu próprio estabelecimento.', extra_tags='product')
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        if next_url:
            return redirect(next_url)
        return _product_detail_redirect(product, request)

    added = apply_product_favorite_toggle(request.user, product)
    if added:
        messages.success(request, f'"{product.name}" foi adicionado aos favoritos.', extra_tags='product')
    else:
        messages.info(request, f'"{product.name}" foi removido dos favoritos.', extra_tags='product')

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return _product_detail_redirect(product, request)


@login_required_view
@require_POST
def submit_establishment_review(request, pk):
    establishment = get_object_or_404(
        Establishment,
        pk=pk,
        is_active=True,
    )
    product_pk = request.POST.get('product_pk')
    product = get_public_product(product_pk) if product_pk else None

    if user_owns_establishment(request.user, establishment):
        messages.error(request, 'Não pode comentar o seu próprio estabelecimento.', extra_tags='product')
        if product:
            return _product_detail_redirect(product, request)
        return redirect('home')

    form = EstablishmentReviewForm(request.POST)
    if not form.is_valid():
        for error in form.errors.get('__all__', []):
            messages.error(request, error, extra_tags='product')
        for field, errors in form.errors.items():
            if field == '__all__':
                continue
            for error in errors:
                messages.error(request, error, extra_tags='product')
        if product:
            return _product_detail_redirect(product, request)
        return redirect('home')

    rating = form.cleaned_data.get('rating')
    comment = form.cleaned_data.get('comment', '')

    existing_review = EstablishmentReview.objects.filter(
        user=request.user,
        establishment=establishment,
    ).first()

    if existing_review:
        if rating is not None:
            existing_review.rating = rating
        if comment:
            existing_review.comment = comment
        existing_review.product = product
        existing_review.status = EstablishmentReview.Status.APPROVED
        existing_review.viewed_by_vendor_at = None
        existing_review.save()
        created = False
    else:
        EstablishmentReview.objects.create(
            user=request.user,
            establishment=establishment,
            rating=rating,
            comment=comment,
            status=EstablishmentReview.Status.APPROVED,
            product=product,
        )
        created = True

    if created:
        messages.success(request, 'Avaliação publicada com sucesso.', extra_tags='product')
    else:
        messages.success(request, 'Avaliação atualizada com sucesso.', extra_tags='product')

    if product:
        return _product_detail_redirect(product, request)
    return redirect('home')


@vendedor_required
def establishment_reviews(request, pk):
    establishment = get_object_or_404(Establishment, pk=pk, owner=request.user)
    reviews = (
        get_vendor_reviews_queryset(request.user)
        .filter(establishment=establishment)
    )
    unread_count = reviews.filter(viewed_by_vendor_at__isnull=True).count()
    return render(request, 'vendor/establishment_reviews.html', {
        'establishment': establishment,
        'reviews': reviews,
        'unread_reviews_count': unread_count,
    })


@vendedor_required
@require_POST
def moderate_review(request, pk):
    review = get_object_or_404(
        EstablishmentReview,
        pk=pk,
        establishment__owner=request.user,
    )
    action = request.POST.get('action')
    establishment_pk = review.establishment_id

    if action == 'approve':
        review.status = EstablishmentReview.Status.APPROVED
        review.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Comentário aprovado e visível na plataforma.', extra_tags='vendor')
    elif action == 'reject':
        review.status = EstablishmentReview.Status.REJECTED
        review.save(update_fields=['status', 'updated_at'])
        messages.info(request, 'Comentário rejeitado e ocultado.', extra_tags='vendor')
    else:
        messages.error(request, 'Ação inválida.', extra_tags='vendor')

    return redirect('vendor:establishment_reviews', pk=establishment_pk)
