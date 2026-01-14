from prometheus_client import Counter, generate_latest

HTTP_REQUESTS = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
WEBHOOK_REQUESTS = Counter('webhook_requests_total', 'Total webhook requests', ['result'])

def get_metrics():
    return generate_latest()
