import secrets
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from apps.subscriptions.services import get_user_usage_summary
from apps.scrapers.services import get_today_exchange_rate
from apps.users.models import APIToken

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
def home(request):
    usage_summary = get_user_usage_summary(request.user)
    exchange_rate = get_today_exchange_rate()
    api_token = get_or_create_api_token(request.user)
    context = {
        'usage': usage_summary,
        'api_token': api_token,
        'exchange_rate': exchange_rate,
    }
    return render(request, 'dashboard/dashboard_list.html', context)



