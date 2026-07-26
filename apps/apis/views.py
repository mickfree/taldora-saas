import time
from django.http import JsonResponse
from apps.users.models import APIToken
from apps.subscriptions.services import can_make_request, increment_request_count
from apps.scrapers.services import get_today_exchange_rate, get_ruc_info
from .services import log_api_request

def _authenticate_token(request):
    """
    Extracts and authenticates API Token from Authorization header (Bearer), X-API-Key, or api_key query param.
    Returns (token_obj, error_json_response).
    """
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
        return None, JsonResponse({
            "success": False,
            "error": "No se proporcionó un token de API. Envíe el token mediante la cabecera Authorization (Bearer), X-API-Key o el parámetro api_key."
        }, status=401)
        
    token_obj = APIToken.objects.filter(token=token_str, is_active=True).select_related('user').first()
    if not token_obj:
        return None, JsonResponse({
            "success": False,
            "error": "Token de API inválido o inactivo."
        }, status=401)
        
    return token_obj, None

def api_tipo_cambio(request):
    """
    Public API endpoint to query today's USD exchange rate in PEN.
    Matches routing: api.taldora.com/v1/tipo-cambio/ (served as /v1/tipo-cambio/)
    """
    start_time = time.time()
    
    token_obj, err_resp = _authenticate_token(request)
    if err_resp:
        return err_resp
        
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


def api_ruc_sunat(request):
    """
    Public API endpoint to query RUC tax information from SUNAT.
    Matches routing: api.taldora.com/v1/ruc/?numero=...
    """
    start_time = time.time()
    
    token_obj, err_resp = _authenticate_token(request)
    if err_resp:
        return err_resp
        
    user = token_obj.user
    ruc_param = request.GET.get('numero') or request.GET.get('ruc') or ''
    ruc_param = ruc_param.strip()
    
    if not ruc_param:
        log_api_request(
            user=user,
            service_code='ruc_sunat',
            service_name='RUC SUNAT',
            query_param=ruc_param,
            status_code=400,
            start_time=start_time,
            scraper_node='AWS Lambda us-east-1'
        )
        return JsonResponse({
            "success": False,
            "error": "Debe proporcionar el parámetro 'numero' o 'ruc' con un número de RUC válido."
        }, status=400)
        
    # Check quota limits
    if not can_make_request(user):
        log_api_request(
            user=user,
            service_code='ruc_sunat',
            service_name='RUC SUNAT',
            query_param=ruc_param,
            status_code=429,
            start_time=start_time,
            scraper_node='AWS Lambda us-east-1'
        )
        return JsonResponse({
            "success": False,
            "error": "Límite de peticiones de tu plan excedido para el mes actual."
        }, status=429)
        
    try:
        result = get_ruc_info(ruc_param)
        if result.get("success"):
            increment_request_count(user)
            log_api_request(
                user=user,
                service_code='ruc_sunat',
                service_name='RUC SUNAT',
                query_param=ruc_param,
                status_code=200,
                start_time=start_time,
                scraper_node='AWS Lambda us-east-1'
            )
            return JsonResponse({
                "success": True,
                "data": result["data"]
            })
        else:
            log_api_request(
                user=user,
                service_code='ruc_sunat',
                service_name='RUC SUNAT',
                query_param=ruc_param,
                status_code=400,
                start_time=start_time,
                scraper_node='AWS Lambda us-east-1'
            )
            return JsonResponse({
                "success": False,
                "error": result.get("error", "RUC no encontrado o inválido.")
            }, status=400)
    except Exception as e:
        log_api_request(
            user=user,
            service_code='ruc_sunat',
            service_name='RUC SUNAT',
            query_param=ruc_param,
            status_code=500,
            start_time=start_time,
            scraper_node='AWS Lambda us-east-1'
        )
        return JsonResponse({
            "success": False,
            "error": f"Error interno al consultar el RUC: {str(e)}"
        }, status=500)

def api_sunarp_vehicular(request):
    """
    Public API endpoint to query vehicle registration data from SUNAT.
    Matches routing: api.taldora.com/v1/sunarp/?placa=...
    """
    start_time = time.time()
    
    token_obj, err_resp = _authenticate_token(request)
    if err_resp:
        return err_resp
        
    user = token_obj.user
    placa_param = request.GET.get('placa') or request.GET.get('numero') or ''
    placa_param = placa_param.strip()
    
    if not placa_param:
        log_api_request(
            user=user,
            service_code='sunarp_vehicular',
            service_name='Consulta Vehicular SUNARP',
            query_param=placa_param,
            status_code=400,
            start_time=start_time,
            scraper_node='AWS Lambda us-east-1'
        )
        return JsonResponse({
            "success": False,
            "error": "Debe proporcionar el parámetro 'placa' con una placa vehicular válida (ej. V7E313 o V7E-313)."
        }, status=400)
        
    # Check quota limits
    if not can_make_request(user):
        log_api_request(
            user=user,
            service_code='sunarp_vehicular',
            service_name='Consulta Vehicular SUNARP',
            query_param=placa_param,
            status_code=429,
            start_time=start_time,
            scraper_node='AWS Lambda us-east-1'
        )
        return JsonResponse({
            "success": False,
            "error": "Límite de peticiones de tu plan excedido para el mes actual."
        }, status=429)
        
    try:
        result = get_sunarp_info(placa_param)
        if result.get("success"):
            increment_request_count(user)
            log_api_request(
                user=user,
                service_code='sunarp_vehicular',
                service_name='Consulta Vehicular SUNARP',
                query_param=placa_param,
                status_code=200,
                start_time=start_time,
                scraper_node='AWS Lambda us-east-1'
            )
            return JsonResponse({
                "success": True,
                "data": result["data"]
            })
        else:
            log_api_request(
                user=user,
                service_code='sunarp_vehicular',
                service_name='Consulta Vehicular SUNARP',
                query_param=placa_param,
                status_code=400,
                start_time=start_time,
                scraper_node='AWS Lambda us-east-1'
            )
            return JsonResponse({
                "success": False,
                "error": result.get("error", "Registro vehicular SUNARP no encontrado o placa inválida.")
            }, status=400)
    except Exception as e:
        log_api_request(
            user=user,
            service_code='sunarp_vehicular',
            service_name='Consulta Vehicular SUNARP',
            query_param=placa_param,
            status_code=500,
            start_time=start_time,
            scraper_node='AWS Lambda us-east-1'
        )
        return JsonResponse({
            "success": False,
            "error": f"Error interno al consultar SUNARP: {str(e)}"
        }, status=500)



