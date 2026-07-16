from django.urls import path

from . import views
from apps.main.views_engagement import establishment_reviews, moderate_review, review_delete

app_name = 'vendor'

urlpatterns = [
    path('tornar-vendedor/', views.become_seller, name='become_seller'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('comentarios/', views.review_inbox, name='review_inbox'),
    path('comentarios/marcar-lidos/', views.mark_reviews_read, name='mark_reviews_read'),
    path('comentarios/<int:pk>/marcar-lido/', views.mark_review_read, name='mark_review_read'),
    path('estabelecimentos/', views.establishment_list, name='establishment_list'),
    path('estabelecimentos/novo/', views.establishment_create, name='establishment_create'),
    path('estabelecimentos/<int:pk>/editar/', views.establishment_edit, name='establishment_edit'),
    path('estabelecimentos/<int:pk>/eliminar/', views.establishment_delete, name='establishment_delete'),
    path('estabelecimentos/<int:pk>/produtos/', views.product_list, name='product_list'),
    path('estabelecimentos/<int:est_pk>/produtos/novo/', views.product_create, name='product_create'),
    path('produtos/<int:pk>/editar/', views.product_edit, name='product_edit'),
    path('produtos/<int:pk>/disponibilidade/', views.product_toggle_availability, name='product_toggle_availability'),
    path('produtos/<int:pk>/eliminar/', views.product_delete, name='product_delete'),
    path('estabelecimentos/<int:pk>/comentarios/', establishment_reviews, name='establishment_reviews'),
    path('comentarios/<int:pk>/moderar/', moderate_review, name='moderate_review'),
    path('comentarios/<int:pk>/eliminar/', review_delete, name='review_delete'),
]
