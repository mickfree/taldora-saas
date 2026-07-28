window.renderedAreaChart = null;
window.renderedDonutChart = null;

function initDashboardCharts(force = false) {
    const usageElem = document.querySelector("#usageHistoryChart");
    const donutElem = document.querySelector("#servicesDonutChart");

    if (!usageElem && !donutElem) return;

    const areaAlreadyRendered = usageElem && usageElem.querySelector('.apexcharts-canvas');
    const donutAlreadyRendered = donutElem && donutElem.querySelector('.apexcharts-canvas');

    // Si ya están renderizados en el DOM y no es forzado, no hacer nada
    if (!force && (usageElem ? areaAlreadyRendered : true) && (donutElem ? donutAlreadyRendered : true)) {
        return;
    }

    // Esperar a que los contenedores tengan dimensiones estables en el DOM
    if (usageElem && usageElem.offsetWidth === 0) {
        setTimeout(function () { initDashboardCharts(force); }, 50);
        return;
    }

    // Usar requestAnimationFrame para garantizar que el motor de renderizado del navegador haya terminado la disposición (layout)
    requestAnimationFrame(function () {
        executeChartRender(usageElem, donutElem, force, areaAlreadyRendered, donutAlreadyRendered);
    });
}

function executeChartRender(usageElem, donutElem, force, areaAlreadyRendered, donutAlreadyRendered) {
    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#94a3b8' : '#64748b';
    const borderColor = isDark ? '#334155' : '#e2e8f0';

    const dates = window.chartData?.dates || [];
    const successData = window.chartData?.successData || [];
    const errorData = window.chartData?.errorData || [];

    // 1. Gráfico de Área (Consumo Diario)
    if (usageElem && (force || !areaAlreadyRendered)) {
        if (window.renderedAreaChart) {
            try { window.renderedAreaChart.destroy(); } catch (e) { }
            window.renderedAreaChart = null;
        }
        usageElem.innerHTML = '';
        const areaOptions = {
            series: [{
                name: 'Exitosas (200)',
                data: successData
            }, {
                name: 'Fallidas / Errores',
                data: errorData
            }],
            chart: {
                type: 'area',
                height: 280,
                toolbar: { show: false },
                background: 'transparent',
                zoom: { enabled: false },
                redrawOnParentResize: true,
                redrawOnWindowResize: true,
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 600
                }
            },
            colors: ['#6366f1', '#f43f5e'],
            dataLabels: { enabled: false },
            stroke: { curve: 'smooth', width: 2 },
            fill: {
                type: 'gradient',
                gradient: {
                    shadeIntensity: 1,
                    opacityFrom: 0.45,
                    opacityTo: 0.05,
                    stops: [0, 90, 100]
                }
            },
            xaxis: {
                categories: dates,
                labels: { style: { colors: textColor, fontSize: '11px' } },
                axisBorder: { show: false },
                axisTicks: { show: false },
                tooltip: { enabled: false }
            },
            yaxis: {
                min: 0,
                forceNiceScale: true,
                labels: { style: { colors: textColor, fontSize: '11px' } }
            },
            grid: {
                borderColor: borderColor,
                strokeDashArray: 4,
                padding: {
                    left: 15,
                    right: 15,
                    top: 10,
                    bottom: 0
                }
            },
            tooltip: { theme: isDark ? 'dark' : 'light' },
            legend: { show: false }
        };

        window.renderedAreaChart = new ApexCharts(usageElem, areaOptions);
        window.renderedAreaChart.render();
    }

    // 2. Gráfico de Donut (Distribución por servicio)
    if (donutElem && (force || !donutAlreadyRendered)) {
        if (window.renderedDonutChart) {
            try { window.renderedDonutChart.destroy(); } catch (e) { }
            window.renderedDonutChart = null;
        }
        donutElem.innerHTML = '';
        const donutLabels = window.chartData?.donutLabels || [];
        const donutSeries = window.chartData?.donutSeries || [];

        const donutOptions = {
            series: donutSeries.length > 0 ? donutSeries : [1],
            labels: donutLabels.length > 0 ? donutLabels : ['Sin uso'],
            chart: {
                type: 'donut',
                height: 240,
                background: 'transparent',
                redrawOnParentResize: true,
                redrawOnWindowResize: true,
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 600
                }
            },
            colors: ['#6366f1', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'],
            legend: { show: false },
            dataLabels: { enabled: false },
            stroke: { show: false },
            tooltip: { theme: isDark ? 'dark' : 'light' }
        };

        window.renderedDonutChart = new ApexCharts(donutElem, donutOptions);
        window.renderedDonutChart.render();
    }
}

window.initDashboardCharts = initDashboardCharts;

// Carga inicial standard
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { initDashboardCharts(true); });
} else {
    initDashboardCharts(true);
}

// Re-inicialización tras navegación asíncrona con HTMX (hx-boost / swap)
document.addEventListener('htmx:afterSettle', function () {
    initDashboardCharts(false);
});

// Al restaurar desde el historial del navegador
document.addEventListener('htmx:historyRestore', function () {
    initDashboardCharts(true);
});