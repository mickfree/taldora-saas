from django.contrib import admin
from .models import ApiRequestLog

@admin.register(ApiRequestLog)
class ApiRequestLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service_name', 'query_param', 'status_code', 'latency_ms', 'scraper_node', 'created_at')
    list_filter = ('service_code', 'status_code', 'scraper_node', 'created_at')
    search_fields = ('user__username', 'user__email', 'query_param', 'service_name')
    readonly_fields = ('created_at',)
