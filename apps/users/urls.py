from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='settings_profile', permanent=False)),
    path('profile/', views.settings_profile, name='settings_profile'),
    path('profile/edit/', views.settings_profile_edit, name='settings_profile_edit'),
    path('profile/password/', views.settings_password_change, name='settings_password_change'),
]
