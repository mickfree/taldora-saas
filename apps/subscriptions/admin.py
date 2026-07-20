from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from unfold.admin import ModelAdmin
from .models import Plan, Subscription, PaymentProof, MonthlyUsage, PaymentStatus
from .services import approve_payment_proof, reject_payment_proof


@admin.register(Plan)
class PlanAdmin(ModelAdmin):
    ...

@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    ...

@admin.register(PaymentProof)
class PaymentProofAdmin(ModelAdmin):
    ...

@admin.register(MonthlyUsage)
class MonthlyUsageAdmin(ModelAdmin):
    ...