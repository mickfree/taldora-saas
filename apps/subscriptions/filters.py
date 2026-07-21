import django_filters
from django.db.models import Q
from .models import PaymentProof, PaymentStatus

class PaymentProofFilter(django_filters.FilterSet):

    search = django_filters.CharFilter(method='filter_search', label='Buscar')
    user_id = django_filters.NumberFilter(field_name='user__id', label='ID de Cliente')

    class Meta:
        model = PaymentProof
        fields = ['search', 'status', 'billing_cycle', 'user_id']

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(user__username__icontains=value) |
            Q(user__email__icontains=value) |
            Q(bank_name__icontains=value) |
            Q(reference_number__icontains=value) |
            Q(plan__name__icontains=value) |
            Q(admin_notes__icontains=value)
        )