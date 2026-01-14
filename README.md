# Lyftr AI - Webhook Ingestion Service (MVP)

This is a minimal FastAPI service for ingesting WhatsApp-like messages, verifying HMAC signatures, storing messages in SQLite, and exposing listing, stats, health, and metrics.

## How to Run

```bash
make up
```

This will start the service on http://localhost:8000

## Example Curl Commands

### Ingest a message
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Signature: $(echo -n '{"message_id":"m1","from":"+919876543210","to":"+14155550100","ts":"2025-01-15T10:00:00Z","text":"Hello"}' | openssl dgst -sha256 -hmac "secret" -hex | cut -d' ' -f2)" \
  -d '{"message_id":"m1","from":"+919876543210","to":"+14155550100","ts":"2025-01-15T10:00:00Z","text":"Hello"}'
```

### List messages
```bash
curl "http://localhost:8000/messages?limit=10"
```

### Get stats
```bash
curl http://localhost:8000/stats
```

### Health checks
```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

### Metrics
```bash
curl http://localhost:8000/metrics
```

## Design Decisions

### HMAC Verification
- Uses raw request body for signature calculation to ensure integrity.
- Compares signatures using `hmac.compare_digest` to prevent timing attacks.
- Returns 401 for invalid/missing signatures.

### Pagination Logic
- Uses SQL LIMIT/OFFSET for efficient pagination.
- Orders by `ts ASC, message_id ASC` for deterministic results.
- Validates limit between 1-100.

### Stats Computation
- Uses SQL aggregates for efficient computation.
- Top 10 senders ordered by message count descending.
- Null timestamps when no messages exist.

## Tools Used
- VSCode + Copilot + ChatGPT for development.
- FastAPI for async web framework.
- SQLAlchemy with aiosqlite for async DB operations.
- Pydantic for configuration and validation.
- Structlog for structured JSON logging.
- Prometheus client for metrics.
- Docker Compose for containerization.

## Setup Used
VSCode + Copilot + occasional ChatGPT prompts for implementation.

## Implementation Details

### Message Validation
- `message_id`: Non-empty string
- `from`, `to`: E.164 format (starts with +, followed by digits only)
- `ts`: ISO-8601 UTC with Z suffix (e.g., 2025-01-15T10:00:00Z)
- `text`: Optional, max 4096 characters
- Invalid payloads return 422 with validation error details

### Idempotency
- SQLite PRIMARY KEY constraint on `message_id` prevents duplicates
- On duplicate message_id: returns 200 without inserting new row
- Graceful IntegrityError handling in application layer

### Logging & Metrics
- **Structured JSON logs**: One JSON line per request with ts, level, request_id, method, path, status, latency_ms
- **Webhook logs**: Include message_id, dup (boolean), result (created/duplicate/invalid_signature/validation_error)
- **Prometheus metrics**: 
  - `http_requests_total` with method, path, status labels
  - `webhook_requests_total` with result label
  - Request latency in milliseconds

### Health Checks
- `/health/live`: Always 200 when app is running
- `/health/ready`: 200 only if DB is reachable AND WEBHOOK_SECRET is set (non-empty)
