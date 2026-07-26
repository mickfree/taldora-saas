from django.urls import path
from . import views

urlpatterns = [
    path('v1/tipo-cambio/', views.api_tipo_cambio, name='api_tipo_cambio'),
    path('v1/ruc/', views.api_ruc_sunat, name='api_ruc_sunat'),
]



