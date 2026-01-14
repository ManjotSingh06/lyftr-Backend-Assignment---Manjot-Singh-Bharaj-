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

@pytest.fixture
def seed_data(client):
    # Seed some test messages
    messages = [
        {"message_id": "m1", "from": "+123", "to": "+456", "ts": "2025-01-01T00:00:00Z", "text": "hello"},
        {"message_id": "m2", "from": "+123", "to": "+456", "ts": "2025-01-02T00:00:00Z", "text": "world"},
        {"message_id": "m3", "from": "+789", "to": "+456", "ts": "2025-01-03T00:00:00Z", "text": "test"},
    ]
    for msg in messages:
        body = json.dumps(msg).encode()
        sig = sign(body)
        client.post("/webhook", content=body, headers={"X-Signature": sig})

def test_stats_empty(client):
    r = client.get('/stats')
    assert r.status_code == 200
    data = r.json()
    assert data['total_messages'] == 0
    assert data['senders_count'] == 0
    assert data['messages_per_sender'] == []
    assert data['first_message_ts'] is None
    assert data['last_message_ts'] is None

def test_stats_with_data(client, seed_data):
    r = client.get('/stats')
    assert r.status_code == 200
    data = r.json()
    assert data['total_messages'] == 3
    assert data['senders_count'] == 2
    assert len(data['messages_per_sender']) == 2
    # Top sender +123 with 2 messages
    assert data['messages_per_sender'][0]['from'] == '+123'
    assert data['messages_per_sender'][0]['count'] == 2
    # Next +789 with 1
    assert data['messages_per_sender'][1]['from'] == '+789'
    assert data['messages_per_sender'][1]['count'] == 1
    assert data['first_message_ts'] == '2025-01-01T00:00:00Z'
    assert data['last_message_ts'] == '2025-01-03T00:00:00Z'
