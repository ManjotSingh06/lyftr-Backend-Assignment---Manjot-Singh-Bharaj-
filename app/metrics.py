from prometheus_client import Counter,Histogram, generate_latest

HTTP_REQUESTS = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
WEBHOOK_REQUESTS = Counter('webhook_requests_total', 'Total webhook requests', ['result'])
REQUEST_LATENCY = Histogram(
    'request_latency_ms',
    'Request latency in milliseconds',
    ['endpoint'],
    buckets=[100, 500, 1000, 5000, 10000]
)
def get_metrics():
    return generate_latest()
