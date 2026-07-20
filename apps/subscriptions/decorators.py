from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from .services import can_make_request, increment_request_count


def subscription_quota_required(amount=1, auto_increment=True):
    """
    Decorador para proteger vistas que consumen peticiones del plan del usuario.
    - Si el usuario no tiene cuota suficiente:
      - Si es petición HTMX/JSON: retorna un error 429 Too Many Requests con mensaje en JSON.
      - Si es petición estándar: envía mensaje de error y redirige a la página de planes.
    - Si auto_increment es True, incrementa el contador al procesar la vista exitosamente.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')

            if not can_make_request(request.user, amount=amount):
                err_msg = "Has alcanzado el límite mensual de peticiones de tu plan. Por favor, renueva o mejora tu suscripción."
                
                if request.headers.get('HX-Request') or request.content_type == 'application/json':
                    return JsonResponse({'error': err_msg}, status=429)

                messages.error(request, err_msg)
                return redirect('subscriptions:plan_list')

            response = view_func(request, *args, **kwargs)

            # Si la vista respondió exitosamente (código 2xx), incrementamos el uso
            if auto_increment and 200 <= response.status_code < 300:
                increment_request_count(request.user, amount=amount)

            return response
        return _wrapped_view
    return decorator
