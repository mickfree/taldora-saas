import django_filters
from django.db.models import Q
from .models import ApiRequestLog

SERVICE_CHOICES = (
    ('sunat_ruc', 'SUNAT RUC'),
    ('reniec_dni', 'RENIEC DNI'),
    ('sunarp_placa', 'SUNARP Placa'),
    ('tipo_cambio', 'Tipo de Cambio'),
)

STATUS_CHOICES = (
    ('200', '200 OK (Exitosas)'),
    ('error', 'Errores / 404'),
)

class ApiRequestLogFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', label='Búsqueda')
    status = django_filters.ChoiceFilter(choices=STATUS_CHOICES, method='filter_status', label='Estado')
    service = django_filters.ChoiceFilter(choices=SERVICE_CHOICES, field_name='service_code', lookup_expr='exact', label='Servicio')

    class Meta:
        model = ApiRequestLog
        fields = ['search', 'status', 'service']

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        val_clean = str(value).strip()
        val_id = val_clean.lower().replace('req_', '')
        if val_id.isdigit():
            return queryset.filter(
                Q(query_param__icontains=val_clean) |
                Q(service_name__icontains=val_clean) |
                Q(service_code__icontains=val_clean) |
                Q(scraper_node__icontains=val_clean) |
                Q(id=int(val_id))
            )
        return queryset.filter(
            Q(query_param__icontains=val_clean) |
            Q(service_name__icontains=val_clean) |
            Q(service_code__icontains=val_clean) |
            Q(scraper_node__icontains=val_clean)
        )

    def filter_status(self, queryset, name, value):
        if not value or value == 'all':
            return queryset
        if value == '200':
            return queryset.filter(status_code=200)
        elif value == 'error':
            return queryset.exclude(status_code=200)
        elif value.isdigit():
            return queryset.filter(status_code=int(value))
        return queryset
