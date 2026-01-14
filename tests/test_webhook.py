import pytest
from fastapi.testclient import TestClient
from app.main import app
import hmac
import hashlib
import json

SECRET = b"secret"

@pytest.fixture
def client():
    with TestClient(app) as tc:
        yield tc

def sign(payload: bytes):
    return hmac.new(SECRET, payload, hashlib.sha256).hexdigest()

def test_valid_webhook(client):
    data = {"message_id": "m1", "from": "+123", "to": "+456", "ts": "2025-01-01T00:00:00Z", "text": "hi"}
    body = json.dumps(data).encode()
    sig = sign(body)
    resp = client.post("/webhook", content=body, headers={"X-Signature": sig})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_invalid_signature(client):
    resp = client.post("/webhook", json={"message_id": "m1"}, headers={"X-Signature": "invalid"})
    assert resp.status_code == 401

def test_validation_error(client):
    data = {"invalid": "data"}
    body = json.dumps(data).encode()
    sig = sign(body)
    resp = client.post("/webhook", content=body, headers={"X-Signature": sig})
    assert resp.status_code == 422

def test_duplicate(client):
    data = {"message_id": "m2", "from": "+123", "to": "+456", "ts": "2025-01-01T00:00:00Z", "text": "hi"}
    body = json.dumps(data).encode()
    sig = sign(body)
    # First post
    resp1 = client.post("/webhook", content=body, headers={"X-Signature": sig})
    assert resp1.status_code == 200
    # Second post (duplicate)
    resp2 = client.post("/webhook", content=body, headers={"X-Signature": sig})
    assert resp2.status_code == 200  # Idempotent

def test_no_signature(client):
    resp = client.post("/webhook", json={"message_id": "m3"})
    assert resp.status_code == 401
