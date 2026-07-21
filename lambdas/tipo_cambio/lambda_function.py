import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

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

def get_bcrp_rate():
    """
    Queries the official BCRP API for the SBS USD exchange rates over the last 10 days.
    Returns the latest available rates, skipping days with non-available ('n.d.') data.
    """
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=10)
    
    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = end_dt.strftime("%Y-%m-%d")
    
    # Series: PD04639PD (SBS Compra), PD04640PD (SBS Venta)
    url = f"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04639PD-PD04640PD/json/{start_str}/{end_str}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    periods = data.get("periods", [])
    if not periods:
        raise ValueError("El API del BCRP no devolvió períodos de tiempo.")
    
    # Loop backwards through periods to find the latest valid day without 'n.d.' (no disponible)
    for period in reversed(periods):
        values = period.get("values", [])
        if len(values) >= 2 and values[0] != "n.d." and values[1] != "n.d.":
            val1 = float(values[0])
            val2 = float(values[1])
            # The Sell rate (Venta) is always higher than the Buy rate (Compra).
            # This ensures correctness regardless of how BCRP orders the series in the response.
            buy = min(val1, val2)
            sell = max(val1, val2)
            date_str = period.get("name", "") # e.g. "20.Jul.26"
            return buy, sell, f"BCRP ({date_str})"
            
    raise ValueError("No se encontraron registros con tipo de cambio numérico válido en los últimos 10 días en el BCRP.")

def lambda_handler(event, context):
    """
    AWS Lambda entry point.
    Attempts to scrape SBS, and falls back to BCRP API on failure.
    """
    source_used = None
    buy_rate = None
    sell_rate = None
    errors = []

    # 1. Try SBS Web Scraping
    try:
        buy_rate, sell_rate, source_used = get_sbs_rate()
    except Exception as e:
        errors.append(f"Error SBS Scraping: {str(e)}")
        
        # 2. Fallback to BCRP API
        try:
            buy_rate, sell_rate, source_used = get_bcrp_rate()
        except Exception as e2:
            errors.append(f"Error BCRP Fallback: {str(e2)}")

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
