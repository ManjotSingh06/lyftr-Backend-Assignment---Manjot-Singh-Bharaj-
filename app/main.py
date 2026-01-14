from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from typing import Optional
import hmac
import hashlib
import json
from .config import settings
from .models import init_db, MessageIn
from .storage import insert_message, get_messages, get_stats
from .logging_utils import log_requests
from .metrics import HTTP_REQUESTS, WEBHOOK_REQUESTS, get_metrics
import structlog

app = FastAPI()
logger = structlog.get_logger()

# Middleware
@app.middleware("http")
async def add_logging_and_metrics(request: Request, call_next):
    response = await log_requests(request, call_next)
    HTTP_REQUESTS.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    return response

# @app.on_event("startup")
# async def startup():
#     await init_db()

@app.on_event("startup")
async def startup():
    await init_db()
    if not settings.webhook_secret or not settings.webhook_secret.strip():
        raise RuntimeError("WEBHOOK_SECRET must be set and non-empty")

@app.post("/webhook")
async def webhook(request: Request):
    if not settings.webhook_secret:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    body = await request.body()
    signature = request.headers.get("X-Signature")
    if not signature:
        WEBHOOK_REQUESTS.labels(result="invalid_signature").inc()
        raise HTTPException(status_code=401, detail="invalid signature")
    
    expected = hmac.new(settings.webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        WEBHOOK_REQUESTS.labels(result="invalid_signature").inc()
        raise HTTPException(status_code=401, detail="invalid signature")
    
    try:
        data = json.loads(body)
        msg = MessageIn(**data)
    except:
        WEBHOOK_REQUESTS.labels(result="validation_error").inc()
        raise HTTPException(status_code=422, detail="validation error")
    
    created = await insert_message(msg.message_id, msg.from_, msg.to, msg.ts, msg.text)
    result = "created" if created else "duplicate"
    WEBHOOK_REQUESTS.labels(result=result).inc()
    logger.info("webhook", message_id=msg.message_id, dup=not created, result=result)
    return {"status": "ok"}

@app.get("/messages")
async def messages(limit: int = 50, offset: int = 0, from_: Optional[str] = None, since: Optional[str] = None, q: Optional[str] = None):
    if limit < 1 or limit > 100:
        limit = 50
    msgs, total = await get_messages(limit, offset, from_, since, q)
    return {"data": msgs, "total": total, "limit": limit, "offset": offset}

@app.get("/stats")
async def stats():
    return await get_stats()

@app.get("/health/live")
async def live():
    return {"status": "ok"}

@app.get("/health/ready")
async def ready():
    if not settings.ready:
        raise HTTPException(status_code=503, detail="not ready")
    # Check DB
    try:
        await get_stats()
    except:
        raise HTTPException(status_code=503, detail="not ready")
    return {"status": "ok"}

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(get_metrics())
