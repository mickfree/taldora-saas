from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # django-allauth urls
    path('accounts/', include('allauth.urls')),
    
    # Core app urls
    path('', views.home, name='home'),
    path('htmx-demo-time/', views.htmx_demo_time, name='htmx_demo_time'),
]

# Incluir rutas de desarrollo solo si DEBUG está activado
if settings.DEBUG:
    # django_browser_reload urls
    urlpatterns.append(path("__reload__/", include("django_browser_reload.urls")))
    
    # django-debug-toolbar urls
    try:
        import debug_toolbar
        urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
    except ImportError:
        pass

