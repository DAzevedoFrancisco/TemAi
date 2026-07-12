from django.urls import path

from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('administradores/', views.admin_users, name='admin_users'),
    path('administradores/promover/', views.promote_admin, name='promote_admin'),
    path('administradores/<int:pk>/despromover/', views.demote_admin, name='demote_admin'),
    path('utilizadores/', views.user_list, name='user_list'),
    path('utilizadores/<int:pk>/estado/', views.user_toggle_active, name='user_toggle_active'),
    path('utilizadores/<int:pk>/apagar/', views.user_delete, name='user_delete'),
    path('estabelecimentos/', views.establishment_list, name='establishment_list'),
    path('estabelecimentos/<int:pk>/', views.establishment_detail, name='establishment_detail'),
    path('estabelecimentos/<int:pk>/estado/', views.establishment_toggle_active, name='establishment_toggle_active'),
    path('estabelecimentos/<int:pk>/apagar/', views.establishment_delete, name='establishment_delete'),
]
