"""Autenticação: bootstrap, login, JWT e contas inativas."""

from datetime import datetime, timedelta, timezone

import jwt

import main
from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD, login


def test_bootstrap_admin_only_works_once(client):
    payload = {"nome": "Admin", "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}
    first = client.post("/api/auth/bootstrap-admin", json=payload)
    assert first.status_code == 201
    assert first.json()["role"] == "admin"

    second = client.post(
        "/api/auth/bootstrap-admin",
        json={"nome": "Outro", "email": "outro@teste.local", "senha": "outra-senha-123"},
    )
    assert second.status_code == 409


def test_bootstrap_rejects_short_password(client):
    response = client.post(
        "/api/auth/bootstrap-admin",
        json={"nome": "Admin", "email": ADMIN_EMAIL, "senha": "curta"},
    )
    assert response.status_code == 400


def test_login_returns_token_user_and_expiry(client, admin_headers):
    response = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == main.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert body["user"]["role"] == "admin"
    assert "senha_hash" not in str(body)


def test_login_is_case_insensitive_on_email(client, admin_headers):
    response = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL.upper(), "senha": ADMIN_PASSWORD}
    )
    assert response.status_code == 200


def test_wrong_password_and_unknown_email_look_the_same(client, admin_headers):
    wrong_password = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "senha": "senha-errada-123"}
    )
    unknown_email = client.post(
        "/api/auth/login", json={"email": "ninguem@teste.local", "senha": "qualquer-123"}
    )
    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_me_requires_token_and_returns_current_user(client, admin_headers):
    assert client.get("/api/auth/me").status_code == 401
    me = client.get("/api/auth/me", headers=admin_headers)
    assert me.status_code == 200
    assert me.json()["email"] == ADMIN_EMAIL


def test_invalid_and_tampered_tokens_are_rejected(client, admin_headers):
    garbage = {"Authorization": "Bearer isto-nao-e-um-jwt"}
    assert client.get("/api/auth/me", headers=garbage).status_code == 401

    forged = jwt.encode(
        {"sub": "1", "role": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "outra-chave-qualquer-que-nao-e-a-do-servidor",
        algorithm="HS256",
    )
    assert (
        client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code
        == 401
    )


def test_expired_token_is_rejected(client, admin_headers):
    me = client.get("/api/auth/me", headers=admin_headers).json()
    expired = jwt.encode(
        {
            "sub": str(me["id"]),
            "role": "admin",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        main.JWT_SECRET_KEY,
        algorithm=main.JWT_ALGORITHM,
    )
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_token_role_claim_does_not_grant_privileges(client, admin_headers, make_user):
    """O perfil vem do banco, não do claim `role` do token."""
    vendedor_headers, vendedor = make_user("vendedor", "vendedor@teste.local")
    token = jwt.encode(
        {
            "sub": str(vendedor["id"]),
            "role": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        main.JWT_SECRET_KEY,
        algorithm=main.JWT_ALGORITHM,
    )
    response = client.get(
        "/api/users", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_deactivated_user_cannot_login_or_use_existing_token(client, admin_headers, make_user):
    headers, user = make_user("vendedor", "vendedor@teste.local")
    assert client.get("/api/leads", headers=headers).status_code == 200

    update = client.put(
        f"/api/users/{user['id']}",
        headers=admin_headers,
        json={
            "nome": user["nome"],
            "email": user["email"],
            "role": "vendedor",
            "lead_id": None,
            "ativo": False,
        },
    )
    assert update.status_code == 200

    assert client.get("/api/leads", headers=headers).status_code == 401
    blocked = client.post(
        "/api/auth/login", json={"email": "vendedor@teste.local", "senha": "senha-12345"}
    )
    assert blocked.status_code == 403


def test_admin_cannot_demote_or_deactivate_self(client, admin_headers):
    me = client.get("/api/auth/me", headers=admin_headers).json()
    base = {"nome": me["nome"], "email": me["email"], "lead_id": None}

    demote = client.put(
        f"/api/users/{me['id']}", headers=admin_headers, json={**base, "role": "vendedor", "ativo": True}
    )
    deactivate = client.put(
        f"/api/users/{me['id']}", headers=admin_headers, json={**base, "role": "admin", "ativo": False}
    )
    assert demote.status_code == 400
    assert deactivate.status_code == 400


def test_new_user_validations(client, admin_headers, create_lead):
    def create(**overrides):
        payload = {
            "nome": "Fulano",
            "email": "fulano@teste.local",
            "senha": "senha-12345",
            "role": "vendedor",
            "lead_id": None,
            "ativo": True,
        }
        payload.update(overrides)
        return client.post("/api/users", headers=admin_headers, json=payload)

    assert create(senha="curta").status_code == 400
    assert create(role="superuser").status_code == 400
    assert create(role="aluno", lead_id=None).status_code == 400
    assert create(role="aluno", lead_id=99999).status_code == 404

    lead = create_lead()
    assert create(role="aluno", lead_id=lead["id"]).status_code == 201
    # Mesmo Lead não pode ter duas contas, e e-mail não pode repetir.
    assert (
        create(role="aluno", lead_id=lead["id"], email="outro@teste.local").status_code == 409
    )
    assert create(email="fulano@teste.local").status_code == 409


def test_login_helper_roundtrip(client, admin_headers):
    assert login(client, ADMIN_EMAIL, ADMIN_PASSWORD)["Authorization"].startswith("Bearer ")
