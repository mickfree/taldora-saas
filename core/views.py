from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone

def home(request):
    """Renders the main landing page."""
    return render(request, 'index.html', {
        'server_time': timezone.now()
    })

def htmx_demo_time(request):
    """Returns a simple HTML snippet with current server time for HTMX demo."""
    current_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    return HttpResponse(
        f'<span class="font-mono text-primary-400 font-bold bg-primary-950/50 px-3 py-1.5 rounded-lg border border-primary-800/30 animate-pulse">'
        f'{current_time}'
        f'</span>'
    )
