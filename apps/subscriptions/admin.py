from django.contrib import admin
from django.contrib import messages
from unfold.admin import ModelAdmin
from .models import Plan, Subscription, PaymentProof, MonthlyUsage, PaymentStatus
from .services import approve_payment_proof, reject_payment_proof


@admin.register(Plan)
class PlanAdmin(ModelAdmin):
    list_display = ('code', 'name', 'monthly_requests', 'price_monthly', 'price_annual', 'is_free', 'is_active', 'display_order')
    list_filter = ('is_active', 'is_free')
    search_fields = ('code', 'name')
    ordering = ('display_order', 'price_monthly')


@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = ('id', 'user', 'plan', 'billing_cycle', 'status', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'billing_cycle', 'plan')
    search_fields = ('user__username', 'user__email', 'plan__name')
    ordering = ('-created_at',)


@admin.register(PaymentProof)
class PaymentProofAdmin(ModelAdmin):
    list_display = ('id', 'user', 'plan', 'billing_cycle', 'amount', 'bank_name', 'reference_number', 'status', 'created_at')
    list_filter = ('status', 'billing_cycle', 'plan', 'bank_name')
    search_fields = ('user__username', 'user__email', 'reference_number', 'bank_name')
    ordering = ('-created_at',)
    actions = ['approve_selected_proofs', 'reject_selected_proofs']

    @admin.action(description="Aprobar comprobantes de pago seleccionados")
    def approve_selected_proofs(self, request, queryset):
        count = 0
        for proof in queryset:
            approve_payment_proof(proof, request.user)
            count += 1
        self.message_user(request, f"Se aprobaron {count} comprobantes y se activaron las suscripciones correspondientes.", messages.SUCCESS)

    @admin.action(description="Rechazar comprobantes de pago seleccionados")
    def reject_selected_proofs(self, request, queryset):
        count = 0
        for proof in queryset:
            reject_payment_proof(proof, request.user)
            count += 1
        self.message_user(request, f"Se rechazaron {count} comprobantes.", messages.WARNING)

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.status == PaymentStatus.APPROVED:
                approve_payment_proof(obj, request.user)
                return
            elif obj.status == PaymentStatus.REJECTED:
                reject_payment_proof(obj, request.user, obj.admin_notes)
                return
        elif not change and obj.status == PaymentStatus.APPROVED:
            approve_payment_proof(obj, request.user)
            return

        super().save_model(request, obj, form, change)


@admin.register(MonthlyUsage)
class MonthlyUsageAdmin(ModelAdmin):
    list_display = ('id', 'user', 'year_month', 'request_count', 'updated_at')
    list_filter = ('year_month',)
    search_fields = ('user__username', 'user__email')
    ordering = ('-year_month', '-updated_at')