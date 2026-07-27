import django_filters
from django.db.models import Q
from django.contrib.auth import get_user_model
from apps.scrapers.models import ExchangeRate, RUCData
from .models import PaymentProof, PaymentStatus

User = get_user_model()

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


STATUS_USER_CHOICES = (
    ('active', 'Activo'),
    ('inactive', 'Inactivo'),
)

ROLE_USER_CHOICES = (
    ('staff', 'Administrador / Staff'),
    ('customer', 'Cliente / Usuario'),
)

class UserFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', label='Buscar')
    status = django_filters.ChoiceFilter(choices=STATUS_USER_CHOICES, method='filter_status', label='Estado')
    role = django_filters.ChoiceFilter(choices=ROLE_USER_CHOICES, method='filter_role', label='Rol')

    class Meta:
        model = User
        fields = ['search', 'status', 'role']

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        val = value.strip()
        return queryset.filter(
            Q(username__icontains=val) |
            Q(email__icontains=val) |
            Q(first_name__icontains=val) |
            Q(last_name__icontains=val)
        )

    def filter_status(self, queryset, name, value):
        if value == 'active':
            return queryset.filter(is_active=True)
        elif value == 'inactive':
            return queryset.filter(is_active=False)
        return queryset

    def filter_role(self, queryset, name, value):
        if value == 'staff':
            return queryset.filter(Q(is_staff=True) | Q(is_superuser=True))
        elif value == 'customer':
            return queryset.filter(is_staff=False, is_superuser=False)
        return queryset


class ExchangeRateFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', label='Buscar')

    class Meta:
        model = ExchangeRate
        fields = ['search']

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        val = value.strip()
        return queryset.filter(
            Q(source__icontains=val) |
            Q(date__icontains=val)
        )


class RUCDataFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', label='Buscar')
    estado = django_filters.CharFilter(field_name='estado', lookup_expr='icontains', label='Estado')

    class Meta:
        model = RUCData
        fields = ['search', 'estado']

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        val = value.strip()
        return queryset.filter(
            Q(ruc__icontains=val) |
            Q(razon_social__icontains=val) |
            Q(direccion__icontains=val) |
            Q(departamento__icontains=val) |
            Q(provincia__icontains=val) |
            Q(distrito__icontains=val)
        )