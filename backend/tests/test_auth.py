from tests.conftest import PASSWORD, auth


def login(client, email, password=PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_login_success_and_me(client, world):
    res = login(client, "admin@test.dev")
    assert res.status_code == 200
    tokens = res.json()
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["role"] == "ADMIN"
    assert "hashed_password" not in me.json()


def test_login_wrong_password_is_401(client, world):
    assert login(client, "admin@test.dev", "WrongPass1").status_code == 401


def test_login_unknown_user_gives_same_error(client, world):
    res = login(client, "nobody@test.dev")
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


def test_protected_route_needs_token(client, world):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/projects", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_refresh_rotates_and_old_token_is_rejected(client, world):
    first = login(client, "m1@test.dev").json()
    second = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert second.status_code == 200
    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert reuse.status_code == 401
    # Reuse detection revokes the whole session, so the newer token no longer works either.
    again = client.post("/api/v1/auth/refresh", json={"refresh_token": second.json()["refresh_token"]})
    assert again.status_code == 401


def test_logout_revokes_refresh_token(client, world):
    tokens = login(client, "m1@test.dev").json()
    assert client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 204
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_deactivated_user_token_stops_working(client, world, db):
    headers = auth(world.dev1)
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    world.dev1.is_active = False
    db.commit()
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def signup(client, **overrides):
    body = {"email": "New.User@test.dev", "full_name": "New User", "password": "Passw0rd1", **overrides}
    return client.post("/api/v1/auth/signup", json=body)


def test_signup_creates_developer_and_returns_tokens(client, world):
    res = signup(client)
    assert res.status_code == 201
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {res.json()['access_token']}"})
    assert me.json()["role"] == "DEVELOPER"
    assert me.json()["email"] == "new.user@test.dev"
    assert login(client, "new.user@test.dev").status_code == 200


def test_signup_cannot_choose_role(client, world):
    res = signup(client, role="ADMIN")
    assert res.status_code == 201
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {res.json()['access_token']}"})
    assert me.json()["role"] == "DEVELOPER"


def test_signup_duplicate_email_is_409(client, world):
    assert signup(client, email="admin@test.dev").status_code == 409


def test_signup_rejects_weak_password(client, world):
    assert signup(client, password="onlyletters").status_code == 422
    assert signup(client, password="Sh0rt").status_code == 422
