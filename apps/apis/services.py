import time
from .models import ApiRequestLog

def log_api_request(user, service_code, service_name, query_param='', status_code=200, start_time=None, latency_ms=None, scraper_node='AWS Lambda us-east-1'):
    """
    Helper function to record an API request into the ApiRequestLog model.
    """
    if latency_ms is None and start_time is not None:
        latency_ms = int((time.time() - start_time) * 1000)
    elif latency_ms is None:
        latency_ms = 0

    return ApiRequestLog.objects.create(
        user=user,
        service_code=service_code,
        service_name=service_name,
        query_param=query_param,
        status_code=status_code,
        latency_ms=latency_ms,
        scraper_node=scraper_node
    )
