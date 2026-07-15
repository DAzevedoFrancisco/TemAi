"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.db import connection
from django.http import HttpResponse
from django.urls import path, include


def health_check(_request):
    try:
        connection.ensure_connection()
    except Exception:
        return HttpResponse('db unavailable', status=503, content_type='text/plain')
    return HttpResponse('ok', content_type='text/plain')


urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('gestao/', include('apps.admin_panel.urls')),
    path('vendedor/', include('apps.vendor.urls')),
    path('', include('apps.main.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
