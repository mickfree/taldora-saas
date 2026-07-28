import json
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from .models import Plan, PaymentProof, PaymentStatus, Subscription, SubscriptionStatus
from apps.apis.models import ApiRequestLog
from .services import get_user_usage_summary, get_active_subscription, approve_payment_proof, reject_payment_proof
from .forms import PaymentProofForm
from django.core.paginator import Paginator
from .filters import PaymentProofFilter, UserFilter, ExchangeRateFilter, RUCDataFilter
from apps.subscriptions.choices import PaymentStatus, BillingCycle
from apps.scrapers.models import ExchangeRate, RUCData

User = get_user_model()

@login_required
def plan_list(request):
    plans = Plan.objects.filter(is_active=True).order_by('display_order', 'price_monthly')
    usage_summary = get_user_usage_summary(request.user)
    
    # Pre-selección de plan si viene por GET
    selected_plan_code = request.GET.get('plan')
    initial_data = {}
    if selected_plan_code:
        plan_obj = Plan.objects.filter(code=selected_plan_code, is_active=True).first()
        if plan_obj:
            initial_data['plan'] = plan_obj.id

    form = PaymentProofForm(initial=initial_data)
    
    context = {
        'plans': plans,
        'usage': usage_summary,
        'form': form,
    }
    return render(request, 'subscriptions/plans.html', context)


@login_required
def submit_payment_proof(request):
    plans = Plan.objects.filter(is_active=True).order_by('display_order', 'price_monthly')
    usage_summary = get_user_usage_summary(request.user)
    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES)
        if form.is_valid():
            proof = form.save(commit=False)
            proof.user = request.user
            proof.status = PaymentStatus.PENDING
            proof.save()
            messages.success(
                request,
                '¡Comprobante de depósito enviado con éxito! Un administrador revisará tu pago a la brevedad para activar tu plan.'
            )
            context = {
                'plans': plans,
                'usage': usage_summary,
                'form': form,
            }
            if request.headers.get('HX-Request') == 'true':
                return render(request, 'subscriptions/partials/_plans_table.html', context)
        else:
            messages.error(request, 'Por favor, verifica los datos e intenta de nuevo.')
            context = {
                'plans': plans,
                'usage': usage_summary,
                'form': form,
            }
    return render(request, 'subscriptions/plans.html', context)


@login_required
def history_payment_list(request):
    initial_qs = PaymentProof.objects.filter(user=request.user).select_related('plan').order_by('-created_at')
    payment_proof_filter = PaymentProofFilter(request.GET, queryset=initial_qs)
    payment_proofs = payment_proof_filter.qs

    # pagination
    page_number = request.GET.get('page')
    paginator = Paginator(payment_proofs, 25)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'payment_proofs': page_obj,
        'payment_proof_filter': payment_proof_filter,
    }

    if request.headers.get('HX-Request') and not request.headers.get('HX-Boosted'):
        return render(
            request,
            "subscriptions/partials/_history_payment_table.html",
            context,
        )
    return render(request, 'subscriptions/history_payment_list.html', context)


@staff_member_required
def admin_payment_list(request):
    initial_qs = PaymentProof.objects.all().select_related('user', 'plan', 'reviewed_by').order_by('-created_at')
    payment_proof_filter = PaymentProofFilter(request.GET, queryset=initial_qs)
    payment_proofs = payment_proof_filter.qs

    page_number = request.GET.get('page')
    paginator = Paginator(payment_proofs, 25)
    page_obj = paginator.get_page(page_number)

    context = {
        'payment_proofs': page_obj,
        'payment_proof_filter': payment_proof_filter,
    }

    if request.headers.get('HX-Request') and not request.headers.get('HX-Boosted'):
        return render(
            request,
            "subscriptions/partials/_admin_payment_table.html",
            context,
        )
    return render(request, 'subscriptions/admin_payment_list.html', context)


@staff_member_required
@require_POST
def admin_approve_payment(request, pk):
    proof = get_object_or_404(PaymentProof, pk=pk)
    approve_payment_proof(proof, admin_user=request.user)
    messages.success(request, f"Comprobante #{proof.id} de {proof.user.username} aprobado exitosamente. Suscripción activada.")

    return _render_admin_payment_table_response(request)


@staff_member_required
@require_POST
def admin_reject_payment(request, pk):
    proof = get_object_or_404(PaymentProof, pk=pk)
    admin_notes = request.POST.get('admin_notes', '').strip()
    reject_payment_proof(proof, admin_user=request.user, admin_notes=admin_notes)
    messages.warning(request, f"Comprobante #{proof.id} de {proof.user.username} ha sido rechazado.")

    return _render_admin_payment_table_response(request)


def _render_admin_payment_table_response(request):
    initial_qs = PaymentProof.objects.all().select_related('user', 'plan', 'reviewed_by').order_by('-created_at')
    payment_proof_filter = PaymentProofFilter(request.GET, queryset=initial_qs)
    payment_proofs = payment_proof_filter.qs

    page_number = request.GET.get('page')
    paginator = Paginator(payment_proofs, 25)
    page_obj = paginator.get_page(page_number)

    context = {
        'payment_proofs': page_obj,
        'payment_proof_filter': payment_proof_filter,
    }

    if request.headers.get('HX-Request'):
        return render(request, "subscriptions/partials/_admin_payment_table.html", context)
    return redirect('admin_payment_list')


@staff_member_required
def user_autocomplete(request):
    q = request.GET.get('q', '').strip()
    users = []
    if q:
        users = User.objects.filter(
            Q(username__icontains=q) | Q(email__icontains=q)
        ).only('id', 'username', 'email')[:10]

    return render(
        request,
        'subscriptions/partials/_user_autocomplete_results.html',
        {'users': users, 'query': q}
    )


@staff_member_required
def admin_user_list(request):
    initial_qs = User.objects.all().annotate(
        total_api_requests=Count('api_request_logs')
    ).prefetch_related('subscriptions__plan').order_by('-date_joined')
    user_filter = UserFilter(request.GET, queryset=initial_qs)
    users_qs = user_filter.qs

    page_number = request.GET.get('page')
    paginator = Paginator(users_qs, 20)
    page_obj = paginator.get_page(page_number)

    # Dashboard Metrics
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_requests': ApiRequestLog.objects.count(),
        'active_subscriptions': Subscription.objects.filter(status=SubscriptionStatus.ACTIVE).count(),
    }

    # Chart Analytics (Global for Admin)
    today = timezone.localdate()
    start_date = today - timedelta(days=13)
    daily_logs = ApiRequestLog.objects.get_daily_stats(user=None, start_date=start_date)

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

    # Service distribution
    service_counts = ApiRequestLog.objects.get_service_distribution(user=None)
    total_requests_all = sum(item['total'] for item in service_counts) or 1

    service_distribution = []
    donut_labels = []
    donut_series = []

    for item in service_counts:
        pct = round((item['total'] / total_requests_all) * 100, 1)
        service_distribution.append({
            'code': item['service_code'],
            'name': item['service_name'],
            'percentage': pct,
            'count': item['total']
        })
        donut_labels.append(f"{item['service_name']} ({pct}%)")
        donut_series.append(item['total'])

    context = {
        'users_page': page_obj,
        'user_filter': user_filter,
        'stats': stats,
        'chart_date_labels_json': json.dumps(date_labels),
        'chart_success_series_json': json.dumps(success_series),
        'chart_error_series_json': json.dumps(error_series),
        'service_distribution': service_distribution,
        'donut_labels_json': json.dumps(donut_labels),
        'donut_series_json': json.dumps(donut_series),
    }

    if request.headers.get('HX-Request') and not request.headers.get('HX-Boosted'):
        return render(
            request,
            "subscriptions/partials/_admin_user_table.html",
            context,
        )
    return render(request, 'subscriptions/admin_user_list.html', context)


@staff_member_required
def admin_exchange_rate_list(request):
    initial_qs = ExchangeRate.objects.all().order_by('-date')
    rate_filter = ExchangeRateFilter(request.GET, queryset=initial_qs)
    rates_qs = rate_filter.qs

    page_number = request.GET.get('page')
    paginator = Paginator(rates_qs, 20)
    page_obj = paginator.get_page(page_number)

    context = {
        'rates_page': page_obj,
        'rate_filter': rate_filter,
    }

    if request.headers.get('HX-Request') and not request.headers.get('HX-Boosted'):
        return render(
            request,
            "subscriptions/partials/_admin_exchange_rate_table.html",
            context,
        )
    return render(request, 'subscriptions/admin_exchange_rate_list.html', context)


@staff_member_required
def admin_ruc_query_list(request):
    initial_qs = RUCData.objects.all().order_by('-updated_at')
    ruc_filter = RUCDataFilter(request.GET, queryset=initial_qs)
    rucs_qs = ruc_filter.qs

    page_number = request.GET.get('page')
    paginator = Paginator(rucs_qs, 20)
    page_obj = paginator.get_page(page_number)

    context = {
        'rucs_page': page_obj,
        'ruc_filter': ruc_filter,
    }

    if request.headers.get('HX-Request') and not request.headers.get('HX-Boosted'):
        return render(
            request,
            "subscriptions/partials/_admin_ruc_query_table.html",
            context,
        )
    return render(request, 'subscriptions/admin_ruc_query_list.html', context)



