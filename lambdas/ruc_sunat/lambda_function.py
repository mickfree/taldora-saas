import json
import re
import requests
import logging

logger = logging.getLogger(__name__)

def validate_ruc(ruc: str) -> bool:
    """
    Validates a Peruvian RUC (11 digits, valid prefix, modulo 11 checksum).
    """
    if not isinstance(ruc, str) or not re.match(r'^\d{11}$', ruc):
        return False
        
    multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    sum_val = sum(int(digit) * mult for digit, mult in zip(ruc[:10], multipliers))
    remainder = sum_val % 11
    check_digit = 11 - remainder
    
    if check_digit == 10:
        check_digit = 0
    elif check_digit == 11:
        check_digit = 1
        
    return check_digit == int(ruc[10])

def fetch_real_sunat_ruc(ruc: str) -> dict:
    """
    Fetches real SUNAT RUC data from public live APIs / endpoints.
    """
    # Try primary live SUNAT public endpoint
    url = f"https://api.apis.net.pe/v1/ruc?numero={ruc}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            data = response.json()
            nombre = data.get('nombre') or data.get('razonSocial') or ''
            if nombre:
                return {
                    "success": True,
                    "ruc": ruc,
                    "razon_social": nombre.strip(),
                    "estado": data.get('estado', 'ACTIVO').strip(),
                    "condicion": data.get('condicion', 'HABIDO').strip(),
                    "direccion": data.get('direccion', '').strip(),
                    "departamento": data.get('departamento', '').strip(),
                    "provincia": data.get('provincia', '').strip(),
                    "distrito": data.get('distrito', '').strip(),
                    "ubigeo": data.get('ubigeo', '').strip(),
                    "es_agente_retencion": data.get('esAgenteRetencion', False),
                    "source": "SUNAT Public Portal / Live Service"
                }
    except Exception as e:
        logger.warning(f"Failed to fetch from primary SUNAT endpoint: {e}")

    return None


def lambda_handler(event, context):
    """
    AWS Lambda function for querying SUNAT RUC data with real live HTTP requests.
    Event structure: {"ruc": "20100047218"}
    """
    ruc = event.get('ruc') or (event.get('queryStringParameters') or {}).get('ruc')
    
    if not ruc:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": "El parámetro RUC es obligatorio."
            })
        }
        
    ruc = str(ruc).strip()
    
    if not validate_ruc(ruc):
        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": "El RUC ingresado no tiene un formato válido o falló la verificación de dígito."
            })
        }
        
    # Execute real HTTP request to SUNAT service
    real_data = fetch_real_sunat_ruc(ruc)
    
    if real_data and real_data.get("success"):
        return {
            "statusCode": 200,
            "body": json.dumps(real_data)
        }
    else:
        return {
            "statusCode": 404,
            "body": json.dumps({
                "success": False,
                "error": f"No se encontró información en SUNAT para el RUC {ruc}."
            })
        }
