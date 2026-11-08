import re
from datetime import timedelta

from app.db.base import utcnow
from app.models import AuthToken, User
from tests.conftest import PASSWORD, auth

NEW = {"email": "New.User@test.dev", "full_name": "New User", "password": "Passw0rd1"}


def signup(client, **overrides):
    return client.post("/api/v1/auth/signup", json={**NEW, **overrides})


def login(client, email, password=PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def token_from(email) -> str:
    return re.search(r"token=([\w-]+)", email.html).group(1)


# ---------- signup + email verification ----------


def test_signup_sends_verification_and_blocks_login_until_verified(client, world, outbox):
    res = signup(client)
    assert res.status_code == 201 and "access_token" not in res.json()
    assert len(outbox.sent) == 1 and outbox.sent[0].to == "new.user@test.dev"
    assert "/verify-email?token=" in outbox.sent[0].html
    blocked = login(client, "new.user@test.dev")
    assert blocked.status_code == 403 and "verify" in blocked.json()["detail"].lower()
    assert client.post("/api/v1/auth/verify-email", json={"token": token_from(outbox.sent[0])}).status_code == 200
    assert login(client, "new.user@test.dev").status_code == 200


def test_signup_is_always_a_developer_and_rejects_duplicates_and_weak_passwords(client, world, db):
    assert signup(client, role="ADMIN").status_code == 201
    assert db.query(User).filter_by(email="new.user@test.dev").one().role.value == "DEVELOPER"
    assert signup(client, email="admin@test.dev").status_code == 409
    assert signup(client, email="b@test.dev", password="onlyletters").status_code == 422


def test_wrong_password_never_reveals_verification_state(client, world):
    signup(client)
    assert login(client, "new.user@test.dev", "WrongPass1").status_code == 401


def test_verification_token_is_single_use_and_expires(client, world, outbox, db):
    signup(client)
    token = token_from(outbox.sent[0])
    assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 200
    assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 400  # already used
    assert client.post("/api/v1/auth/verify-email", json={"token": "x" * 40}).status_code == 400  # unknown
    signup(client, email="late@test.dev")
    record = db.query(AuthToken).order_by(AuthToken.id.desc()).first()
    record.expires_at = utcnow() - timedelta(minutes=1)
    db.commit()
    assert client.post("/api/v1/auth/verify-email", json={"token": token_from(outbox.sent[-1])}).status_code == 400


def test_resend_verification_replaces_the_old_link(client, world, outbox):
    signup(client)
    old = token_from(outbox.sent[0])
    assert client.post("/api/v1/auth/resend-verification", json={"email": "new.user@test.dev"}).status_code == 202
    assert len(outbox.sent) == 2
    assert client.post("/api/v1/auth/verify-email", json={"token": old}).status_code == 400
    assert client.post("/api/v1/auth/verify-email", json={"token": token_from(outbox.sent[1])}).status_code == 200
    # unknown / already verified addresses look identical and send nothing
    sent = len(outbox.sent)
    assert client.post("/api/v1/auth/resend-verification", json={"email": "nobody@test.dev"}).status_code == 202
    assert client.post("/api/v1/auth/resend-verification", json={"email": "admin@test.dev"}).status_code == 202
    assert len(outbox.sent) == sent


def test_admin_created_users_are_verified(client, world):
    body = {"email": "made@test.dev", "full_name": "Made By Admin", "password": "Passw0rd1", "role": "DEVELOPER"}
    assert client.post("/api/v1/users", json=body, headers=auth(world.admin)).status_code == 201
    assert login(client, "made@test.dev", "Passw0rd1").status_code == 200


# ---------- forgot / reset password ----------


def test_forgot_password_does_not_reveal_which_emails_exist(client, world, outbox):
    known = client.post("/api/v1/auth/forgot-password", json={"email": "dev1@test.dev"})
    unknown = client.post("/api/v1/auth/forgot-password", json={"email": "ghost@test.dev"})
    assert known.status_code == unknown.status_code == 202 and known.json() == unknown.json()
    assert [m.to for m in outbox.sent] == ["dev1@test.dev"]  # only the real account got mail
    assert "did not request" in outbox.sent[0].html  # security warning is in the email


def test_reset_password_full_flow_and_session_invalidation(client, world, outbox, db):
    old_session = login(client, "dev1@test.dev").json()
    client.post("/api/v1/auth/forgot-password", json={"email": "dev1@test.dev"})
    token = token_from(outbox.sent[0])
    stored = db.query(AuthToken).one()
    assert stored.token_hash != token and len(stored.token_hash) == 64  # only a hash is stored
    res = client.post("/api/v1/auth/reset-password", json={"token": token, "password": "BrandNew123"})
    assert res.status_code == 200
    assert login(client, "dev1@test.dev").status_code == 401  # old password is dead
    assert login(client, "dev1@test.dev", "BrandNew123").status_code == 200
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": old_session["refresh_token"]}).status_code == 401


def test_reset_token_is_single_use_expires_and_rejects_garbage(client, world, outbox, db):
    client.post("/api/v1/auth/forgot-password", json={"email": "dev1@test.dev"})
    token = token_from(outbox.sent[0])
    assert client.post("/api/v1/auth/reset-password", json={"token": token, "password": "BrandNew123"}).status_code == 200
    assert client.post("/api/v1/auth/reset-password", json={"token": token, "password": "Another1234"}).status_code == 400
    assert client.post("/api/v1/auth/reset-password", json={"token": "z" * 40, "password": "BrandNew123"}).status_code == 400
    client.post("/api/v1/auth/forgot-password", json={"email": "dev2@test.dev"})
    db.query(AuthToken).filter_by(used_at=None).one().expires_at = utcnow() - timedelta(seconds=1)
    db.commit()
    assert client.post("/api/v1/auth/reset-password", json={"token": token_from(outbox.sent[1]), "password": "BrandNew123"}).status_code == 400


def test_reset_rejects_weak_password_and_newer_link_replaces_older(client, world, outbox):
    client.post("/api/v1/auth/forgot-password", json={"email": "dev1@test.dev"})
    client.post("/api/v1/auth/forgot-password", json={"email": "dev1@test.dev"})
    first, second = token_from(outbox.sent[0]), token_from(outbox.sent[1])
    assert client.post("/api/v1/auth/reset-password", json={"token": second, "password": "onlyletters"}).status_code == 422
    assert client.post("/api/v1/auth/reset-password", json={"token": first, "password": "BrandNew123"}).status_code == 400
    assert client.post("/api/v1/auth/reset-password", json={"token": second, "password": "BrandNew123"}).status_code == 200


def test_inactive_and_removed_users_get_no_reset_email(client, world, outbox, db):
    world.dev2.is_active = False
    db.commit()
    client.post("/api/v1/auth/forgot-password", json={"email": "dev2@test.dev"})
    assert outbox.sent == []


def test_reset_also_verifies_an_unverified_account(client, world, outbox):
    signup(client)
    client.post("/api/v1/auth/forgot-password", json={"email": "new.user@test.dev"})
    token = token_from(outbox.sent[-1])
    client.post("/api/v1/auth/reset-password", json={"token": token, "password": "BrandNew123"})
    assert login(client, "new.user@test.dev", "BrandNew123").status_code == 200


def test_email_endpoints_validate_input(client, world):
    assert client.post("/api/v1/auth/forgot-password", json={"email": "not-an-email"}).status_code == 422
    assert client.post("/api/v1/auth/verify-email", json={"token": "short"}).status_code == 422
    assert client.post("/api/v1/auth/reset-password", json={"token": "short", "password": "BrandNew123"}).status_code == 422
