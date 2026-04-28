def test_register_get(client):
    r = client.get("/register")
    assert r.status_code == 200
    assert b"Create your account" in r.data


def test_register_success(client):
    r = client.post("/register", data={
        "name": "Alice", "email": "alice@example.com", "password": "secret99"
    })
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/login")
    with client.session_transaction() as sess:
        assert "user_id" in sess


def test_register_duplicate_email(client):
    r = client.post("/register", data={
        "name": "Bob", "email": "demo@spendly.com", "password": "secret99"
    })
    assert r.status_code == 200
    assert b"already exists" in r.data


def test_register_short_password(client):
    r = client.post("/register", data={
        "name": "Carol", "email": "carol@example.com", "password": "short"
    })
    assert r.status_code == 200
    assert b"8 characters" in r.data


def test_register_missing_fields(client):
    r = client.post("/register", data={"name": "", "email": "", "password": ""})
    assert r.status_code == 200
    assert b"required" in r.data


def test_register_email_normalized(client, app):
    client.post("/register", data={
        "name": "Dave", "email": "DAVE@EXAMPLE.COM", "password": "secret99"
    })
    from database.db import get_user_by_email
    with app.app_context():
        user = get_user_by_email("dave@example.com")
    assert user is not None


def test_register_password_hashed(client, app):
    client.post("/register", data={
        "name": "Eve", "email": "eve@example.com", "password": "secret99"
    })
    from database.db import get_user_by_email
    with app.app_context():
        user = get_user_by_email("eve@example.com")
    assert user["password"] != "secret99"
    assert user["password"].startswith(("pbkdf2:", "scrypt:"))
