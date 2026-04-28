def test_login_get(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert b"Sign in" in r.data


def test_login_success(client):
    r = client.post("/login", data={
        "email": "demo@spendly.com", "password": "password123"
    })
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/profile")
    with client.session_transaction() as sess:
        assert "user_id" in sess


def test_login_wrong_password(client):
    r = client.post("/login", data={
        "email": "demo@spendly.com", "password": "wrongpassword"
    })
    assert r.status_code == 200
    assert b"Invalid email or password" in r.data


def test_login_unknown_email(client):
    r = client.post("/login", data={
        "email": "nobody@example.com", "password": "password123"
    })
    assert r.status_code == 200
    assert b"Invalid email or password" in r.data


def test_login_empty_fields(client):
    r = client.post("/login", data={"email": "", "password": ""})
    assert r.status_code == 200
    assert b"required" in r.data


def test_login_no_enumeration(client):
    r_wrong_pass = client.post("/login", data={
        "email": "demo@spendly.com", "password": "wrongpassword"
    })
    r_unknown = client.post("/login", data={
        "email": "nobody@example.com", "password": "password123"
    })
    assert b"Invalid email or password" in r_wrong_pass.data
    assert b"Invalid email or password" in r_unknown.data


def test_logout_clears_session(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
    r = client.get("/logout")
    assert r.status_code == 302
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_logout_redirects_to_landing(client):
    r = client.get("/logout")
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/")
