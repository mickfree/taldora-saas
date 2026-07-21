from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Plan, PaymentProof, PaymentStatus
from .services import get_user_usage_summary, get_active_subscription
from .forms import PaymentProofForm
from django.core.paginator import Paginator
from .filters import PaymentProofFilter
from apps.subscriptions.choices import PaymentStatus, BillingCycle

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

    if request.headers.get('HX-Request'):
        return render(
            request,
            "subscriptions/partials/_history_payment_table.html",
            context,
        )
    return render(request, 'subscriptions/history_payment_list.html', context)
