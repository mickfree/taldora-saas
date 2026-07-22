import time
from django.http import JsonResponse
from apps.users.models import APIToken
from apps.subscriptions.services import can_make_request, increment_request_count
from apps.scrapers.services import get_today_exchange_rate
from .services import log_api_request

def api_tipo_cambio(request):
    """
    Public API endpoint to query today's USD exchange rate in PEN.
    Matches routing: api.decoleta.com/v1/tipo-cambio/ (served as /v1/tipo-cambio/)
    """
    start_time = time.time()
    
    # 1. Retrieve the token from headers or query parameters
    auth_header = request.headers.get('Authorization', '')
    token_str = None
    if auth_header.startswith('Bearer '):
        token_str = auth_header.split(' ')[1]
    elif auth_header:
        token_str = auth_header
        
    if not token_str:
        token_str = request.headers.get('X-API-Key')
        
    if not token_str:
        token_str = request.GET.get('api_key')
        
    if not token_str:
        return JsonResponse({
            "success": False,
            "error": "No se proporcionó un token de API. Envíe el token mediante la cabecera Authorization (Bearer), X-API-Key o el parámetro api_key."
        }, status=401)
        
    # 2. Authenticate the token
    token_obj = APIToken.objects.filter(token=token_str, is_active=True).select_related('user').first()
    if not token_obj:
        return JsonResponse({
            "success": False,
            "error": "Token de API inválido o inactivo."
        }, status=401)
        
    user = token_obj.user
    query_date = request.GET.get('fecha', 'Hoy')
    
    # 3. Check subscription limits
    if not can_make_request(user):
        log_api_request(
            user=user,
            service_code='tipo_cambio',
            service_name='Tipo de Cambio USD',
            query_param=query_date,
            status_code=429,
            start_time=start_time,
            scraper_node='AWS Lambda us-east-1'
        )
        return JsonResponse({
            "success": False,
            "error": "Límite de peticiones de tu plan excedido para el mes actual."
        }, status=429)
        
    # 4. Fetch exchange rate and track usage
    try:
        exchange_rate = get_today_exchange_rate()
        if not exchange_rate:
            log_api_request(
                user=user,
                service_code='tipo_cambio',
                service_name='Tipo de Cambio USD',
                query_param=query_date,
                status_code=503,
                start_time=start_time,
                scraper_node='AWS Lambda us-east-1'
            )
            return JsonResponse({
                "success": False,
                "error": "Tipo de cambio temporalmente no disponible."
            }, status=503)
            
        increment_request_count(user)
        log_api_request(
            user=user,
            service_code='tipo_cambio',
            service_name='Tipo de Cambio USD',
            query_param=query_date,
            status_code=200,
            start_time=start_time,
            scraper_node='AWS Lambda us-east-1'
        )
        
        return JsonResponse({
            "success": True,
            "compra": float(exchange_rate.buy_rate),
            "venta": float(exchange_rate.sell_rate),
            "fecha": exchange_rate.date.strftime("%Y-%m-%d"),
            "fuente": exchange_rate.source
        })
    except Exception as e:
        log_api_request(
            user=user,
            service_code='tipo_cambio',
            service_name='Tipo de Cambio USD',
            query_param=query_date,
            status_code=500,
            start_time=start_time,
            scraper_node='AWS Lambda us-east-1'
        )
        return JsonResponse({
            "success": False,
            "error": f"Error interno al obtener el tipo de cambio: {str(e)}"
        }, status=500)
