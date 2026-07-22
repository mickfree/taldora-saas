import secrets
import json
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from apps.subscriptions.services import get_user_usage_summary

from apps.scrapers.services import get_today_exchange_rate
from apps.users.models import APIToken
from apps.apis.models import ApiRequestLog
from apps.apis.filters import ApiRequestLogFilter

def get_or_create_api_token(user):
    """Gets the user's active API token or generates a new one if it doesn't exist."""
    token_obj, created = APIToken.objects.get_or_create(
        user=user,
        defaults={'token': f"taldora_sk_live_{secrets.token_hex(24)}"}
    )
    return token_obj.token

def regenerate_api_token(user):
    """Regenerates a new active API token for the user."""
    new_token = f"taldora_sk_live_{secrets.token_hex(24)}"
    token_obj, created = APIToken.objects.update_or_create(
        user=user,
        defaults={'token': new_token, 'is_active': True}
    )
    return token_obj.token

@login_required
@require_POST
def regenerate_token(request):
    """Regenerates the user's API Token and returns the partial HTML for HTMX updates."""
    new_token = regenerate_api_token(request.user)
    context = {'api_token': new_token}
    return render(request, 'dashboard/partials/_api_token_field.html', context)

@login_required
def refresh_monthly_usage(request):
    """Returns the updated monthly usage card partial for HTMX updates."""
    usage_summary = get_user_usage_summary(request.user)
    context = {'usage': usage_summary}
    return render(request, 'dashboard/partials/_monthly_usage_card.html', context)

@login_required
def recent_queries_table(request):
    """View dedicated to rendering the recent API queries table with filters and pagination."""
    initial_qs = ApiRequestLog.objects.filter(user=request.user).order_by('-created_at')
    api_filter = ApiRequestLogFilter(request.GET, queryset=initial_qs)
    qs = api_filter.qs

    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    formatted_items = []
    for log in page_obj:
        formatted_items.append({
            'id': f"req_{log.id:06d}",
            'service_code': log.service_code,
            'service': log.service_name,
            'query': log.query_param or '-',
            'status': log.status_code,
            'status_label': log.status_label,
            'latency': log.formatted_latency,
            'source': log.scraper_node,
            'timestamp': log.created_at.strftime("%d/%m %H:%M")
        })

    page_obj.object_list = formatted_items

    context = {
        'page_obj': page_obj,
        'api_filter': api_filter,
    }
    return render(request, 'dashboard/partials/_recent_queries_table.html', context)


@login_required
def home(request):
    usage_summary = get_user_usage_summary(request.user)
    exchange_rate = get_today_exchange_rate()
    api_token = get_or_create_api_token(request.user)
    api_filter = ApiRequestLogFilter(request.GET)

    # 1. Histórico de volumen diario (últimos 14 días vía Manager)
    today = timezone.now().date()
    start_date = today - timedelta(days=13)

    daily_logs = ApiRequestLog.objects.get_daily_stats(request.user, start_date)

    stats_map = {}
    for item in daily_logs:
        raw_d = item['day']
        if raw_d:
            if hasattr(raw_d, 'strftime'):
                key = raw_d.strftime("%Y-%m-%d")
            else:
                key = str(raw_d)[:10]
            stats_map[key] = {
                'success': item['success_count'],
                'error': item['error_count']
            }

    date_labels = []
    success_series = []
    error_series = []

    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        date_labels.append(day.strftime("%d/%m"))
        counts = stats_map.get(day.strftime("%Y-%m-%d"), {'success': 0, 'error': 0})
        success_series.append(counts['success'])
        error_series.append(counts['error'])

    # 2. Call from manager ApiRequestLogManager.get_service_distribution()
    service_counts = ApiRequestLog.objects.get_service_distribution(request.user)

    total_requests = sum(item['total'] for item in service_counts) or 1

    service_distribution = []
    donut_labels = []
    donut_series = []

    for item in service_counts:
        pct = round((item['total'] / total_requests) * 100, 1)
        service_distribution.append({
            'code': item['service_code'],
            'name': item['service_name'],
            'percentage': pct,
            'count': item['total']
        })
        donut_labels.append(item['service_name'])
        donut_series.append(item['total'])

    context = {
        'usage': usage_summary,
        'api_token': api_token,
        'exchange_rate': exchange_rate,
        'api_filter': api_filter,
        'chart_date_labels_json': json.dumps(date_labels),
        'chart_success_series_json': json.dumps(success_series),
        'chart_error_series_json': json.dumps(error_series),
        'service_distribution': service_distribution,
        'donut_labels_json': json.dumps(donut_labels),
        'donut_series_json': json.dumps(donut_series),
    }
    return render(request, 'dashboard/dashboard_list.html', context)

