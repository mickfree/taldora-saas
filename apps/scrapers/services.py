from datetime import date
from django.utils import timezone
import json
import logging
from .models import ExchangeRate

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
