import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def get_sunat_rate():
    """
    Queries the SUNAT exchange rate API (apis.net.pe).
    Returns buy rate, sell rate, and source string.
    """
    url = "https://api.apis.net.pe/v1/tipo-cambio-sunat"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers, timeout=8)
    response.raise_for_status()
    
    data = response.json()
    buy = float(data["compra"])
    sell = float(data["venta"])
    date_str = data.get("fecha", "")
    source = f"SUNAT ({date_str})" if date_str else "SUNAT"
    return buy, sell, source

def get_sbs_rate():
    """
    Scrapes the SBS website for the USD exchange rate (compra/venta).
    Note: Under standard conditions, this may be blocked by Incapsula/Cloudflare.
    """
    url = "https://www.sbs.gob.pe/app/pp/SISTIP_PORTAL/Paginas/Publicacion/TipoCambioPromedio.aspx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    dollar_row = None
    # Iterate through all rows looking for the row containing US Dollars ("Dólar")
    for tr in soup.find_all('tr'):
        cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
        if len(cells) >= 3:
            if "Dólar" in cells[0] or "Dolar" in cells[0]:
                dollar_row = cells
                break
                
    if not dollar_row:
        raise ValueError("No se encontró la fila del Dólar en la página de la SBS.")
    
    # Extract and parse rates
    buy = float(dollar_row[1].replace(',', ''))
    sell = float(dollar_row[2].replace(',', ''))
    return buy, sell, "SBS"


def lambda_handler(event, context):
    """
    AWS Lambda entry point.
    Attempts to fetch SUNAT API (1st), then falls back to SBS Web Scraping (2nd).
    """
    source_used = None
    buy_rate = None
    sell_rate = None
    errors = []
    
    # 1. Try SUNAT API (Primary)
    try:
        buy_rate, sell_rate, source_used = get_sunat_rate()
    except Exception as e1:
        errors.append(f"Error SUNAT API: {str(e1)}")
        
        # 2. Fallback to SBS Web Scraping
        try:
            buy_rate, sell_rate, source_used = get_sbs_rate()
        except Exception as e2:
            errors.append(f"Error SBS Scraping: {str(e2)}")

    if buy_rate is not None and sell_rate is not None:
        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "buy_rate": buy_rate,
                "sell_rate": sell_rate,
                "source": source_used,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "warnings": errors
            })
        }
    else:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "errors": errors
            })
        }
