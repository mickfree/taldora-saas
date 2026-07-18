document.addEventListener('alpine:init', () => {
    // Componente principal del Sidebar
    Alpine.data('sidebarComponent', () => ({
        collapsed: localStorage.getItem('sidebar-collapsed') === 'true',
        searchQuery: '',

        toggleCollapse() {
            this.collapsed = !this.collapsed;
            localStorage.setItem('sidebar-collapsed', this.collapsed);
        },

        expandAndFocus() {
            this.collapsed = false;
            localStorage.setItem('sidebar-collapsed', false);
            this.$nextTick(() => {
                if (this.$refs.searchInput) {
                    this.$refs.searchInput.focus();
                }
            });
        },

        clearSearch() {
            this.searchQuery = '';
            this.$nextTick(() => {
                if (this.$refs.searchInput) {
                    this.$refs.searchInput.focus();
                }
            });
        },

        shouldShowSubitem(subLabel) {
            if (!this.searchQuery) return true;
            return subLabel.toLowerCase().includes(this.searchQuery.toLowerCase());
        }
    }));

    // Componente para cada item del Sidebar (admite sub-ítems)
    Alpine.data('sidebarItemComponent', (label) => ({
        open: false,
        label: label,

        init() {
            // Observa cambios en searchQuery para auto-expandir el menú si un sub-ítem coincide
            this.$watch('searchQuery', value => {
                if (value) {
                    const query = value.toLowerCase();
                    let anySubMatches = false;
                    this.$el.querySelectorAll('[data-sub-label]').forEach(sub => {
                        const subLabel = sub.getAttribute('data-sub-label') || '';
                        if (subLabel.toLowerCase().includes(query)) {
                            anySubMatches = true;
                        }
                    });
                    if (anySubMatches) {
                        this.open = true;
                    }
                }
            });
        },

        matchesSearch() {
            if (!this.searchQuery) return true;
            const query = this.searchQuery.toLowerCase();
            if (this.label.toLowerCase().includes(query)) return true;

            // Verifica si algún sub-ítem coincide con la búsqueda
            const subItems = this.$el.querySelectorAll('[data-sub-label]');
            return Array.from(subItems).some(sub => {
                const subLabel = (sub.getAttribute('data-sub-label') || '').toLowerCase();
                return subLabel.includes(query);
            });
        }
    }));
});
