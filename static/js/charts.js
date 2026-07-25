document.addEventListener('DOMContentLoaded', function () {
    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#94a3b8' : '#64748b';
    const borderColor = isDark ? '#334155' : '#e2e8f0';

    const dates = window.chartData?.dates || [];
    const successData = window.chartData?.successData || [];
    const errorData = window.chartData?.errorData || [];

// area chart     
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
        zoom: {
            enabled: false
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
        axisTicks: { show: false }
    },
    yaxis: {
        labels: { style: { colors: textColor, fontSize: '11px' } }
    },
    grid: {
        borderColor: borderColor,
        strokeDashArray: 4
    },
    tooltip: { theme: isDark ? 'dark' : 'light' },
    legend: { show: false }
};

const areaChart = new ApexCharts(document.querySelector("#usageHistoryChart"), areaOptions);
areaChart.render();

// donut chart
const donutLabels = window.chartData?.donutLabels || [];
const donutSeries = window.chartData?.donutSeries || [];

const donutOptions = {
    series: donutSeries.length > 0 ? donutSeries : [1],
    labels: donutLabels.length > 0 ? donutLabels : ['Sin uso'],
    chart: {
        type: 'donut',
        height: 240,
        background: 'transparent'
    },
    colors: ['#6366f1', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'],
    legend: { show: false },
    dataLabels: { enabled: false },
    stroke: { show: false },
    tooltip: { theme: isDark ? 'dark' : 'light' }
};

const donutChart = new ApexCharts(document.querySelector("#servicesDonutChart"), donutOptions);
donutChart.render();
});