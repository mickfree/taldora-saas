from django import forms
from .models import PaymentProof, Plan, BillingCycle


class PaymentProofForm(forms.ModelForm):
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True, is_free=False),
        label="Plan Deseado",
        empty_label="Selecciona un plan",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg dark:border-brandHover dark:bg-brandBg dark:text-white focus:ring-2 focus:ring-brandAccent focus:outline-none'
        })
    )
    billing_cycle = forms.ChoiceField(
        choices=BillingCycle.choices,
        label="Ciclo de Facturación",
        initial=BillingCycle.MONTHLY,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg dark:border-brandHover dark:bg-brandBg dark:text-white focus:ring-2 focus:ring-brandAccent focus:outline-none'
        })
    )
    bank_name = forms.CharField(
        max_length=100,
        label="Banco / Método de Pago",
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej. BCP, BBVA, Interbank, Yape, Plin',
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg dark:border-brandHover dark:bg-brandBg dark:text-white focus:ring-2 focus:ring-brandAccent focus:outline-none'
        })
    )
    reference_number = forms.CharField(
        max_length=100,
        label="N° de Operación / Referencia",
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej. 09482715 / N° de Comprobante',
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg dark:border-brandHover dark:bg-brandBg dark:text-white focus:ring-2 focus:ring-brandAccent focus:outline-none'
        })
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Monto Depositado (PEN)",
        widget=forms.NumberInput(attrs={
            'placeholder': '0.00',
            'step': '0.01',
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg dark:border-brandHover dark:bg-brandBg dark:text-white focus:ring-2 focus:ring-brandAccent focus:outline-none'
        })
    )
    proof_file = forms.FileField(
        required=False,
        label="Adjuntar Comprobante (Imagen o PDF)",
        widget=forms.FileInput(attrs={
            'accept': 'image/*,.pdf',
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg dark:border-brandHover dark:bg-brandBg dark:text-white focus:ring-2 focus:ring-brandAccent focus:outline-none'
        })
    )

    class Meta:
        model = PaymentProof
        fields = ['plan', 'billing_cycle', 'bank_name', 'reference_number', 'amount', 'proof_file']
