from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import api_views, views
from .views_profile import (
    account_settings,
    switch_profile,
)
from .views_engagement import (
    favorites_list,
    submit_establishment_review,
    toggle_product_favorite,
)

urlpatterns = [
    path('', views.home, name='home'),
    path('pesquisa/', views.search_results, name='search_results'),
    path('api/pesquisa/sugestoes/', views.search_suggestions, name='search_suggestions'),
    path('produtos/<int:pk>/', views.product_detail, name='product_detail'),
    path('produtos/<int:pk>/favorito/', toggle_product_favorite, name='product_favorite_toggle'),
    path('favoritos/', favorites_list, name='favorites'),
    path('estabelecimentos/<int:pk>/comentario/', submit_establishment_review, name='establishment_review_submit'),
    path('termos/', views.terms_view, name='terms'),
    path('privacidade/', views.privacy_view, name='privacy'),
    path('auth/', views.auth_view, name='auth'),
    path('conta/', account_settings, name='account_settings'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/alterar/', switch_profile, name='switch_profile'),
    path('api/auth/register/', api_views.RegisterAPIView.as_view(), name='api_register'),
    path('api/auth/login/', api_views.LoginAPIView.as_view(), name='api_login'),
    path('api/auth/logout/', api_views.LogoutAPIView.as_view(), name='api_logout'),
    path('api/auth/me/', api_views.MeAPIView.as_view(), name='api_me'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
]
