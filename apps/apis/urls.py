from django.urls import path
from . import views

urlpatterns = [
    path('v1/tipo-cambio/', views.api_tipo_cambio, name='api_tipo_cambio'),
]
