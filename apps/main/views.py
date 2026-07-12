from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, logout
from django.shortcuts import redirect, render
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import LoginForm, RegisterForm
from .jwt_utils import REFRESH_COOKIE, clear_jwt_cookies, get_tokens_for_user, set_jwt_cookies
from .profile import Profile, set_active_profile
from .search import (
    DISTANCE_FILTER_OPTIONS,
    calculate_distance_km,
    get_establishment_coordinates,
    get_public_product,
    get_search_categories,
    parse_distance_km,
    parse_search_coordinates,
    search_products_with_distance,
)
from .engagement import (
    can_client_engage_product,
    get_approved_reviews,
    get_establishment_review_stats,
    get_user_review,
    is_product_favorited,
)
from .forms import EstablishmentReviewForm
from .services import assign_cliente_role, get_post_login_redirect_name
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
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('categoria', '').strip()
    user_lat, user_lng = parse_search_coordinates(
        request.GET.get('lat'),
        request.GET.get('lng'),
    )
    max_distance_km = parse_distance_km(request.GET.get('distancia'))
    raw_has_coordinates = bool(request.GET.get('lat') and request.GET.get('lng'))

    product_pairs = search_products_with_distance(
        query,
        category_slug=category_slug or None,
        user_lat=user_lat,
        user_lng=user_lng,
        max_distance_km=max_distance_km,
    )

    for product, distance_km in product_pairs:
        product.distance_km = distance_km

    products = [product for product, _ in product_pairs]

    return render(request, 'main/search_results.html', {
        'query': query,
        'active_category': category_slug,
        'active_distance': str(max_distance_km) if max_distance_km else '',
        'categories': get_search_categories(
            query,
            user_lat=user_lat,
            user_lng=user_lng,
            max_distance_km=max_distance_km,
        ),
        'products': products,
        'results_count': len(products),
        'user_lat': user_lat,
        'user_lng': user_lng,
        'has_location': user_lat is not None and user_lng is not None,
        'location_invalid': raw_has_coordinates and user_lat is None,
        'distance_options': DISTANCE_FILTER_OPTIONS,
    })


def product_detail(request, pk):
    product = get_public_product(pk)
    establishment = product.establishment
    back_query = request.GET.get('q', '').strip()
    back_category = request.GET.get('categoria', '').strip()
    user_lat, user_lng = parse_search_coordinates(
        request.GET.get('lat'),
        request.GET.get('lng'),
    )
    distance_km = None
    if user_lat is not None and user_lng is not None:
        distance_km = calculate_distance_km(user_lat, user_lng, establishment)

    establishment_lat, establishment_lng = get_establishment_coordinates(establishment)

    review_stats = get_establishment_review_stats(establishment)
    user_review = get_user_review(request.user, establishment)
    review_form = EstablishmentReviewForm(
        initial={
            'rating': str(user_review.rating) if user_review and user_review.rating else '',
            'comment': user_review.comment if user_review else '',
        }
    )

    return render(request, 'main/product_detail.html', {
        'product': product,
        'establishment': establishment,
        'establishment_lat': establishment_lat,
        'establishment_lng': establishment_lng,
        'back_query': back_query,
        'back_category': back_category,
        'user_lat': user_lat,
        'user_lng': user_lng,
        'has_location': user_lat is not None and user_lng is not None,
        'distance_km': distance_km,
        'is_favorited': is_product_favorited(request.user, product),
        'review_stats': review_stats,
        'reviews': get_approved_reviews(establishment, limit=8),
        'user_review': user_review,
        'review_form': review_form,
        'can_review': can_client_engage_product(request.user, product),
        'can_favorite': can_client_engage_product(request.user, product),
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
                user = authenticate(request, username=email, password=password)

                if user is not None:
                    if not user.is_administrador:
                        set_active_profile(request, Profile.CLIENTE)
                    tokens = get_tokens_for_user(user)
                    response = redirect(get_post_login_redirect_name(user))
                    return set_jwt_cookies(response, tokens)

                login_form.add_error(None, 'Email ou senha inválidos.')

        elif form_type == 'register':
            register_form = RegisterForm(request.POST)
            active_panel = 'register'

            if register_form.is_valid():
                user = User.objects.create_user(
                    email=register_form.cleaned_data['email'],
                    password=register_form.cleaned_data['password'],
                    name=register_form.cleaned_data['name'],
                    date_of_birth=register_form.cleaned_data['date_of_birth'],
                    gender=register_form.cleaned_data['gender'],
                )
                assign_cliente_role(user)
                set_active_profile(request, Profile.CLIENTE)
                tokens = get_tokens_for_user(user)
                messages.success(request, 'Conta criada com sucesso!', extra_tags='general')
                response = redirect('home')
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
