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

def test_messages_list_empty(client):
    r = client.get('/messages')
    assert r.status_code == 200
    data = r.json()
    assert 'data' in data
    assert data['data'] == []
    assert data['total'] == 0

def test_messages_list_with_data(client, seed_data):
    r = client.get('/messages')
    assert r.status_code == 200
    data = r.json()
    assert len(data['data']) == 3
    assert data['total'] == 3
    assert data['limit'] == 50
    assert data['offset'] == 0

def test_messages_pagination(client, seed_data):
    r = client.get('/messages?limit=2&offset=1')
    assert r.status_code == 200
    data = r.json()
    assert len(data['data']) == 2
    assert data['total'] == 3
    assert data['limit'] == 2
    assert data['offset'] == 1

def test_messages_filter_from(client, seed_data):
    r = client.get('/messages?from=%2B123')  # URL encoded +
    assert r.status_code == 200
    data = r.json()
    assert len(data['data']) == 2  # m1 and m2
    assert all(msg['from'] == '+123' for msg in data['data'])

def test_messages_filter_since(client, seed_data):
    r = client.get('/messages?since=2025-01-02T00:00:00Z')
    assert r.status_code == 200
    data = r.json()
    assert len(data['data']) == 2  # m2 and m3
    assert all(msg['ts'] >= '2025-01-02T00:00:00Z' for msg in data['data'])

def test_messages_search_q(client, seed_data):
    r = client.get('/messages?q=hello')
    assert r.status_code == 200
    data = r.json()
    assert len(data['data']) == 1
    assert data['data'][0]['text'] == 'hello'

def test_messages_invalid_limit(client):
    r = client.get('/messages?limit=150')
    assert r.status_code == 200  # Defaults to 50
    data = r.json()
    assert data['limit'] == 50
