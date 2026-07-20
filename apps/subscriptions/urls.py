from django.urls import path
from . import views

urlpatterns = [
    path('', views.plan_list, name='plan_list'),
    path('submit-proof/', views.submit_payment_proof, name='submit_payment_proof'),
    path('history_payment_list/', views.history_payment_list, name='history_payment_list'),
]
