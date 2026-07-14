from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, logout
from django.shortcuts import redirect, render
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import LoginForm, RegisterForm
from .jwt_utils import REFRESH_COOKIE, clear_jwt_cookies, get_tokens_for_user, set_jwt_cookies
from .profile import Profile, can_use_client_catalog, get_client_catalog_redirect_name, set_active_profile
from .search import (
    build_search_map_markers,
    get_establishment_coordinates,
    get_public_product,
    get_search_categories,
    search_products,
)
from .engagement import (
    can_client_engage_product,
    get_approved_reviews,
    get_establishment_review_stats,
    get_user_review,
    is_product_favorited,
)
from .forms import EstablishmentReviewForm
from .login_throttle import (
    clear_login_attempts,
    failed_login_error_message,
    is_login_locked,
    lockout_error_message,
    register_failed_login,
)
from .services import ensure_system_admin, get_post_login_redirect_name, register_user_with_default_role
from .validators import can_become_seller

User = get_user_model()


def home(request):
    return render(request, 'main/home.html', {
        'can_become_seller': (
            can_become_seller(request.user)
            if request.user.is_authenticated
            else False
        ),
    })


def search_results(request):
    if request.user.is_authenticated and not can_use_client_catalog(request):
        return redirect(get_client_catalog_redirect_name(request))

    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('categoria', '').strip()
    products = list(search_products(query, category_slug=category_slug or None))
    map_markers = []
    if request.user.is_authenticated:
        map_markers = build_search_map_markers(
            products,
            query=query,
            category_slug=category_slug,
        )

    return render(request, 'main/search_results.html', {
        'query': query,
        'active_category': category_slug,
        'categories': get_search_categories(query),
        'products': products,
        'results_count': len(products),
        'map_markers': map_markers,
        'show_search_map': request.user.is_authenticated and bool(map_markers),
    })


def product_detail(request, pk):
    product = get_public_product(pk)
    establishment = product.establishment
    back_query = request.GET.get('q', '').strip()
    back_category = request.GET.get('categoria', '').strip()
    establishment_lat, establishment_lng = get_establishment_coordinates(establishment)

    review_stats = get_establishment_review_stats(establishment)
    user_review = get_user_review(request.user, establishment)
    review_form = EstablishmentReviewForm(
        initial={
            'rating': str(user_review.rating) if user_review and user_review.rating else '',
            'comment': user_review.comment if user_review else '',
        }
    )

    show_product_map = (
        request.user.is_authenticated
        and establishment_lat is not None
        and establishment_lng is not None
    )

    return render(request, 'main/product_detail.html', {
        'product': product,
        'establishment': establishment,
        'establishment_lat': establishment_lat,
        'establishment_lng': establishment_lng,
        'show_product_map': show_product_map,
        'product_map_point': {
            'lat': establishment_lat,
            'lng': establishment_lng,
            'name': establishment.name,
        } if show_product_map else None,
        'back_query': back_query,
        'back_category': back_category,
        'is_favorited': is_product_favorited(request.user, product),
        'review_stats': review_stats,
        'reviews': get_approved_reviews(establishment, limit=8),
        'user_review': user_review,
        'review_form': review_form,
        'can_review': can_client_engage_product(request.user, product) and can_use_client_catalog(request),
        'can_favorite': can_client_engage_product(request.user, product) and can_use_client_catalog(request),
    })


def terms_view(request):
    return render(request, 'main/terms.html')


def privacy_view(request):
    return render(request, 'main/privacy.html')


def auth_view(request):
    if request.user.is_authenticated:
        return redirect(get_post_login_redirect_name(request.user))

    login_form = LoginForm()
    register_form = RegisterForm()
    active_panel = request.GET.get('mode', 'login')

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'login':
            login_form = LoginForm(request.POST)
            active_panel = 'login'

            if login_form.is_valid():
                email = login_form.cleaned_data['email'].lower()
                password = login_form.cleaned_data['password']

                if is_login_locked(email):
                    login_form.add_error(None, lockout_error_message(email))
                else:
                    user = authenticate(request, username=email, password=password)

                    if user is not None:
                        clear_login_attempts(email)
                        ensure_system_admin()
                        user.refresh_from_db()
                        if not user.is_administrador:
                            set_active_profile(request, Profile.CLIENTE)
                        tokens = get_tokens_for_user(user)
                        response = redirect(get_post_login_redirect_name(user))
                        return set_jwt_cookies(response, tokens)

                    attempts, _locked = register_failed_login(email)
                    login_form.add_error(None, failed_login_error_message(email, attempts))

        elif form_type == 'register':
            register_form = RegisterForm(request.POST)
            active_panel = 'register'

            if register_form.is_valid():
                user = register_user_with_default_role(
                    email=register_form.cleaned_data['email'],
                    password=register_form.cleaned_data['password'],
                    name=register_form.cleaned_data['name'],
                    date_of_birth=register_form.cleaned_data['date_of_birth'],
                    gender=register_form.cleaned_data['gender'],
                )
                if not user.is_administrador:
                    set_active_profile(request, Profile.CLIENTE)
                tokens = get_tokens_for_user(user)
                if user.is_administrador:
                    messages.success(
                        request,
                        'Conta criada com sucesso. Tem acesso de administrador ao sistema.',
                        extra_tags='general',
                    )
                else:
                    messages.success(request, 'Conta criada com sucesso!', extra_tags='general')
                response = redirect(get_post_login_redirect_name(user))
                return set_jwt_cookies(response, tokens)

    return render(request, 'main/auth.html', {
        'login_form': login_form,
        'register_form': register_form,
        'active_panel': active_panel,
    })


def logout_view(request):
    refresh_token = request.COOKIES.get(REFRESH_COOKIE)
    if refresh_token:
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            pass

    logout(request)
    response = redirect('auth')
    messages.info(request, 'Sessão terminada. Inicie sessão novamente para continuar.', extra_tags='general')
    return clear_jwt_cookies(response)
