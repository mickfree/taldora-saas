from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from unfold.admin import ModelAdmin
from .models import Plan, Subscription, PaymentProof, MonthlyUsage, PaymentStatus
from .services import approve_payment_proof, reject_payment_proof


@admin.register(Plan)
class PlanAdmin(ModelAdmin):
    list_display = ('name', 'code', 'monthly_requests_formatted', 'price_monthly', 'price_annual', 'effective_monthly', 'is_free', 'is_active', 'display_order')
    list_filter = ('is_free', 'is_active')
    search_fields = ('name', 'code')
    ordering = ('display_order', 'price_monthly')

    def monthly_requests_formatted(self, obj):
        return f"{obj.monthly_requests:,}"
    monthly_requests_formatted.short_description = "Peticiones/Mes"

    def effective_monthly(self, obj):
        return f"PEN {obj.effective_monthly_annual_price}/mes"
    effective_monthly.short_description = "Equivalente Anual"


@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = ('user', 'plan', 'billing_cycle', 'status', 'start_date', 'end_date', 'is_valid_badge')
    list_filter = ('status', 'billing_cycle', 'plan')
    search_fields = ('user__username', 'user__email', 'plan__name')
    raw_id_fields = ('user',)
    ordering = ('-created_at',)

    def is_valid_badge(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: green; font-weight: bold;">✔ Válida</span>')
        return format_html('<span style="color: red; font-weight: bold;">✘ Inactiva</span>')
    is_valid_badge.short_description = "Estado de Validez"


@admin.register(PaymentProof)
class PaymentProofAdmin(ModelAdmin):
    list_display = (
        'id', 'user', 'plan', 'billing_cycle', 'amount', 'bank_name',
        'reference_number', 'status_badge', 'proof_preview', 'created_at'
    )
    list_filter = ('status', 'billing_cycle', 'bank_name', 'plan')
    search_fields = ('user__username', 'user__email', 'reference_number', 'bank_name')
    readonly_fields = ('created_at', 'reviewed_at', 'reviewed_by')
    actions = ['approve_selected_proofs', 'reject_selected_proofs']
    ordering = ('-created_at',)

    def status_badge(self, obj):
        colors = {
            PaymentStatus.PENDING: '#d97706',
            PaymentStatus.APPROVED: '#059669',
            PaymentStatus.REJECTED: '#dc2626'
        }
        color = colors.get(obj.status, '#4b5563')
        return format_html(
            f'<span style="background-color: {color}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: 600;">{obj.get_status_display()}</span>'
        )
    status_badge.short_description = "Estado"

    def proof_preview(self, obj):
        if obj.proof_file:
            return format_html(
                f'<a href="{obj.proof_file.url}" target="_blank" style="color: #2563eb; text-decoration: underline;">Ver Adjunto</a>'
            )
        return "Sin archivo"
    proof_preview.short_description = "Comprobante"

    @admin.action(description="✔ Aprobar comprobantes seleccionados (Activa suscripción)")
    def approve_selected_proofs(self, request, queryset):
        approved_count = 0
        for proof in queryset.filter(status=PaymentStatus.PENDING):
            approve_payment_proof(proof, request.user)
            approved_count += 1
        self.message_user(
            request,
            f"Se aprobaron {approved_count} comprobantes y se actualizaron las suscripciones correspondientes.",
            messages.SUCCESS
        )

    @admin.action(description="✘ Rechazar comprobantes seleccionados")
    def reject_selected_proofs(self, request, queryset):
        rejected_count = 0
        for proof in queryset.filter(status=PaymentStatus.PENDING):
            reject_payment_proof(proof, request.user, admin_notes="Rechazado manualmente desde el panel de administración.")
            rejected_count += 1
        self.message_user(
            request,
            f"Se rechazaron {rejected_count} comprobantes.",
            messages.WARNING
        )


@admin.register(MonthlyUsage)
class MonthlyUsageAdmin(ModelAdmin):
    list_display = ('user', 'year_month', 'request_count', 'updated_at')
    list_filter = ('year_month',)
    search_fields = ('user__username', 'user__email', 'year_month')
    ordering = ('-year_month', '-request_count')
