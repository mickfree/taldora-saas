from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import ExchangeRate

@admin.register(ExchangeRate)
class ExchangeRateAdmin(ModelAdmin):
    list_display = ('date', 'buy_rate', 'sell_rate', 'source', 'updated_at')
    list_filter = ('source',)
    search_fields = ('date',)
    ordering = ('-date',)
