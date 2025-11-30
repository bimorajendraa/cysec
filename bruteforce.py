# test_2fa.py
import pytest
from app import app, pending2fa_store, USERS
from datetime import datetime, timedelta
import secrets

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Ensure clean store before each test
        pending2fa_store.clear()
        yield client

def test_login_sets_pending2fa_and_code_sent(client, monkeypatch):
    # Intercept send_email_mock to capture the code
    sent = {}
    def fake_send_email(email, subject, body):
        sent['email'] = email
        sent['body'] = body
    monkeypatch.setattr('app.send_email_mock', fake_send_email)

    # perform login (username/password valid)
    rv = client.post('/login', data={'username': 'wiener', 'password': 'peter'}, follow_redirects=False)
    assert rv.status_code in (302, 303)  # redirect to /login2

    # session cookie is set; obtain session_sid from client cookie jar
    # Flask test_client stores cookies; we can call /login2 (GET) to ensure pending exists
    rv2 = client.get('/login2')
    assert b'Enter 2FA Code for user' in rv2.data
    # ensure server stored pending2fa for this session
    sid = client.cookie_jar._cookies['localhost.local']['/']['session'].value
    # we cannot access session id internals easily, but pending2fa_store should have one entry
    assert len(pending2fa_store) == 1
    pending = list(pending2fa_store.values())[0]
    assert pending['username'] == 'wiener'
    assert 'code' in pending
    assert pending['expires_at'] > datetime.utcnow()

def test_client_cannot_override_target_with_verify_param(client):
    # login as wiener to create pending2fa tied to session
    client.post('/login', data={'username': 'wiener', 'password': 'peter'}, follow_redirects=True)
    # capture the pending code from store
    pending = list(pending2fa_store.values())[0]
    code_for_wiener = pending['code']

    # Now craft a POST to /login2 but include a bogus 'verify=carlos' parameter
    # Our server should ignore any such client parameter and verify only against session's pending user (wiener)
    rv = client.post('/login2?verify=carlos', data={'mfa_code': code_for_wiener}, follow_redirects=True)
    # login should succeed and redirect to /account
    assert b'Account page' in rv.data
    assert b'Welcome, wiener' in rv.data

    # Ensure session user is wiener, not carlos
    # (We can call /account again to ensure the session user remains wiener)
    rv2 = client.get('/account')
    assert b'Welcome, wiener' in rv2.data
    assert b'carlos' not in rv2.data

def test_bruteforce_protection_limits_attempts(client):
    client.post('/login', data={'username': 'wiener', 'password': 'peter'}, follow_redirects=True)
    pending = list(pending2fa_store.values())[0]
    bad_code = '000000'
    # try 6 times (limit in app is 5)
    for i in range(5):
        rv = client.post('/login2', data={'mfa_code': bad_code})
        # after each failed attempt, should respond with 401 or show invalid
        assert rv.status_code in (401, 200)
    # 6th attempt -> should get 429 or "Too many attempts"
    rv = client.post('/login2', data={'mfa_code': bad_code})
    assert b'Too many attempts' in rv.data or rv.status_code == 429
