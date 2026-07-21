from django.urls import path
from . import views

urlpatterns = [
    path('', views.plan_list, name='plan_list'),
    path('submit-proof/', views.submit_payment_proof, name='submit_payment_proof'),
    path('history_payment_list/', views.history_payment_list, name='history_payment_list'),
    path('admin/payments/', views.admin_payment_list, name='admin_payment_list'),
    path('admin/payments/<int:pk>/approve/', views.admin_approve_payment, name='admin_approve_payment'),
    path('admin/payments/<int:pk>/reject/', views.admin_reject_payment, name='admin_reject_payment'),
]
