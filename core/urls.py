from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from core import views

from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # django-allauth urls
    path('accounts/', include('allauth.urls')),
    
    # User settings urls
    path('settings/', include('apps.users.urls')),
    
    # Subscriptions urls
    path('subscriptions/', include('apps.subscriptions.urls')),
    
    # API urls
    path('', include('apps.apis.urls')),
    
    # Core app urls
    path('', views.home, name='home'),
    path('settings/token/regenerate/', views.regenerate_token, name='regenerate_token'),
    path('dashboard/monthly-usage/', views.refresh_monthly_usage, name='refresh_monthly_usage'),
    path('dashboard/recent-queries/', views.recent_queries_table, name='recent_queries_table'),
]

# Incluir rutas de desarrollo solo si DEBUG está activado
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # django_browser_reload urls
    urlpatterns.append(path("__reload__/", include("django_browser_reload.urls")))
    
    # django-debug-toolbar urls
    try:
        import debug_toolbar
        urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
    except ImportError:
        pass

