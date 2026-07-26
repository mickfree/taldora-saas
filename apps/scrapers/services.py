from datetime import date
from django.utils import timezone
import json
import logging
from .models import ExchangeRate, RUCData

logger = logging.getLogger(__name__)

def get_today_exchange_rate():
    """
    Checks if today's exchange rate is cached in the database.
    If not, calls the local simulated Lambda to scrape it, caches it, and returns it.
    If everything fails, falls back to the most recent historical rate in the database.
    """
    today = timezone.localdate()
    
    # 1. Check if we already have it in the database
    rate = ExchangeRate.objects.filter(date=today).first()
    if rate:
        return rate
        
    # 2. Cache miss: invoke the simulated AWS Lambda locally
    try:
        from lambdas.tipo_cambio.lambda_function import lambda_handler
        
        response = lambda_handler(event={}, context=None)
        if response.get("statusCode") == 200:
            body = json.loads(response["body"])
            if body.get("success"):
                from decimal import Decimal
                buy_rate = Decimal(str(body["buy_rate"]))
                sell_rate = Decimal(str(body["sell_rate"]))
                source = body["source"]
                
                # Save to database to cache it
                rate, created = ExchangeRate.objects.update_or_create(
                    date=today,
                    defaults={
                        'buy_rate': buy_rate,
                        'sell_rate': sell_rate,
                        'source': source
                    }
                )
                logger.info(f"Tipo de cambio del día {today} guardado con éxito. Fuente: {source}")
                return rate
            else:
                logger.error(f"El scraper local falló: {body.get('errors')}")
        else:
            logger.error(f"La Lambda devolvió status {response.get('statusCode')}")
    except Exception as e:
        logger.exception(f"Error ejecutando la simulación local de Lambda: {e}")
        
    # 3. Fallback: Return the latest available rate from the database
    fallback_rate = ExchangeRate.objects.order_by('-date').first()
    if fallback_rate:
        logger.warning(f"Usando tipo de cambio antiguo como fallback: {fallback_rate.date}")
    else:
        logger.error("No se pudo obtener el tipo de cambio del día y la base de datos está vacía.")
        
    return fallback_rate


def get_ruc_info(ruc: str):
    """
    Looks up RUC in the database cache. If missing, invokes local simulated Lambda scraper.
    """
    clean_ruc = str(ruc).strip()
    
    # 1. Check DB cache first
    cached_ruc = RUCData.objects.filter(ruc=clean_ruc).first()
    if cached_ruc:
        return {
            "success": True,
            "data": {
                "ruc": cached_ruc.ruc,
                "razon_social": cached_ruc.razon_social,
                "estado": cached_ruc.estado,
                "condicion": cached_ruc.condicion,
                "direccion": cached_ruc.direccion,
                "departamento": cached_ruc.departamento,
                "provincia": cached_ruc.provincia,
                "distrito": cached_ruc.distrito,
                "ubigeo": cached_ruc.ubigeo,
                "es_agente_retencion": cached_ruc.es_agente_retencion
            }
        }
        
    # 2. Invoke local Lambda
    try:
        from lambdas.ruc_sunat.lambda_function import lambda_handler
        
        response = lambda_handler(event={"ruc": clean_ruc}, context=None)
        status_code = response.get("statusCode", 500)
        body = json.loads(response.get("body", "{}"))
        
        if status_code == 200 and body.get("success"):
            # Cache in DB
            ruc_obj, _ = RUCData.objects.update_or_create(
                ruc=clean_ruc,
                defaults={
                    'razon_social': body.get('razon_social', ''),
                    'estado': body.get('estado', 'ACTIVO'),
                    'condicion': body.get('condicion', 'HABIDO'),
                    'direccion': body.get('direccion', ''),
                    'departamento': body.get('departamento', ''),
                    'provincia': body.get('provincia', ''),
                    'distrito': body.get('distrito', ''),
                    'ubigeo': body.get('ubigeo', ''),
                    'es_agente_retencion': body.get('es_agente_retencion', False)
                }
            )
            return {
                "success": True,
                "data": {
                    "ruc": ruc_obj.ruc,
                    "razon_social": ruc_obj.razon_social,
                    "estado": ruc_obj.estado,
                    "condicion": ruc_obj.condicion,
                    "direccion": ruc_obj.direccion,
                    "departamento": ruc_obj.departamento,
                    "provincia": ruc_obj.provincia,
                    "distrito": ruc_obj.distrito,
                    "ubigeo": ruc_obj.ubigeo,
                    "es_agente_retencion": ruc_obj.es_agente_retencion
                }
            }
        else:
            return {
                "success": False,
                "error": body.get("error", "No se pudo encontrar información para el RUC especificado.")
            }
    except Exception as e:
        logger.exception(f"Error ejecutando simulación de Lambda RUC: {e}")
        return {
            "success": False,
            "error": f"Error interno procesando la consulta RUC: {str(e)}"
        }

def get_sunarp_info(placa: str):
    """
    Looks up vehicle SUNARP registration in DB cache. If missing, invokes local SUNARP Lambda.
    """
    import re
    clean_placa = re.sub(r'[^A-Za-z0-9]', '', str(placa)).upper()
    
    # 1. Check DB cache first
    cached = SUNARPData.objects.filter(placa=clean_placa).first()
    if cached:
        return {
            "success": True,
            "data": {
                "placa": cached.placa,
                "numero_serie": cached.numero_serie,
                "numero_vin": cached.numero_vin,
                "numero_motor": cached.numero_motor,
                "color": cached.color,
                "marca": cached.marca,
                "modelo": cached.modelo,
                "placa_vigente": cached.placa_vigente,
                "placa_anterior": cached.placa_anterior,
                "estado": cached.estado,
                "anotaciones": cached.anotaciones,
                "sede": cached.sede,
                "anio_modelo": cached.anio_modelo,
                "propietarios": cached.propietarios
            }
        }
        
    # 2. Invoke local Lambda
    try:
        from lambdas.sunarp_vehicular.lambda_function import lambda_handler
        
        response = lambda_handler(event={"placa": clean_placa}, context=None)
        status_code = response.get("statusCode", 500)
        body = json.loads(response.get("body", "{}"))
        
        if status_code == 200 and body.get("success"):
            sunarp_obj, _ = SUNARPData.objects.update_or_create(
                placa=body.get('placa', clean_placa),
                defaults={
                    'numero_serie': body.get('numero_serie', '-'),
                    'numero_vin': body.get('numero_vin', '-'),
                    'numero_motor': body.get('numero_motor', '-'),
                    'color': body.get('color', '-'),
                    'marca': body.get('marca', '-'),
                    'modelo': body.get('modelo', '-'),
                    'placa_vigente': body.get('placa_vigente', clean_placa),
                    'placa_anterior': body.get('placa_anterior', 'NINGUNA'),
                    'estado': body.get('estado', 'EN CIRCULACION'),
                    'anotaciones': body.get('anotaciones', 'NINGUNA'),
                    'sede': body.get('sede', '-'),
                    'anio_modelo': str(body.get('anio_modelo', '-')),
                    'propietarios': body.get('propietarios', '-')
                }
            )
            return {
                "success": True,
                "data": {
                    "placa": sunarp_obj.placa,
                    "numero_serie": sunarp_obj.numero_serie,
                    "numero_vin": sunarp_obj.numero_vin,
                    "numero_motor": sunarp_obj.numero_motor,
                    "color": sunarp_obj.color,
                    "marca": sunarp_obj.marca,
                    "modelo": sunarp_obj.modelo,
                    "placa_vigente": sunarp_obj.placa_vigente,
                    "placa_anterior": sunarp_obj.placa_anterior,
                    "estado": sunarp_obj.estado,
                    "anotaciones": sunarp_obj.anotaciones,
                    "sede": sunarp_obj.sede,
                    "anio_modelo": sunarp_obj.anio_modelo,
                    "propietarios": sunarp_obj.propietarios
                }
            }
        else:
            return {
                "success": False,
                "error": body.get("error", "No se encontró registro SUNARP para la placa especificada.")
            }
    except Exception as e:
        logger.exception(f"Error ejecutando simulación de Lambda SUNARP Vehicular: {e}")
        return {
            "success": False,
            "error": f"Error interno procesando la consulta SUNARP: {str(e)}"
        }



