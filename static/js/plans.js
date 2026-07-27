document.addEventListener('alpine:init', () => {
    Alpine.data('plansComponent', (config = {}) => ({
        billingCycle: config.billingCycle || 'MONTHLY',
        showDepositModal: config.showDepositModal || false,
        selectedPlanId: config.selectedPlanId || '',
        amount: config.amount || '',
        plans: config.plans || {},

        init() {
            if (!this.amount) {
                this.updateAmount();
            }
            this.$watch('selectedPlanId', () => this.updateAmount());
            this.$watch('billingCycle', () => this.updateAmount());
        },

        updateAmount() {
            const plan = this.plans[this.selectedPlanId];
            if (plan) {
                const val = this.billingCycle === 'MONTHLY' ? plan.monthly : plan.annual;
                this.amount = String(val).replace(',', '.');
            } else {
                this.amount = '';
            }
        }
    }));
});
