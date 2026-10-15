"""RBAC no backend: admin, vendedor e aluno."""

import pytest

# (método, caminho) acessíveis só por admin.
ADMIN_ONLY = [
    ("GET", "/api/dashboard/summary"),
    ("GET", "/api/customer-analytics"),
    ("GET", "/api/marketing-analytics"),
    ("GET", "/api/lms-analytics"),
    ("GET", "/api/finance/summary"),
    ("GET", "/api/users"),
    ("GET", "/api/admin/lead-options"),
    ("GET", "/api/courses"),
    ("GET", "/api/enrollments"),
]

# Acessíveis por admin e vendedor.
ADMIN_AND_VENDEDOR = [
    ("GET", "/api/leads"),
    ("GET", "/api/followups"),
    ("GET", "/api/products"),
    ("GET", "/api/campaigns"),
    ("GET", "/api/sales"),
    ("GET", "/api/omnichannel/summary"),
    ("GET", "/api/automation/insights"),
]


@pytest.mark.parametrize("method,path", ADMIN_ONLY + ADMIN_AND_VENDEDOR)
def test_requires_authentication(client, method, path):
    assert client.request(method, path).status_code == 401


@pytest.mark.parametrize("method,path", ADMIN_ONLY + ADMIN_AND_VENDEDOR)
def test_admin_can_access_everything(client, admin_headers, method, path):
    response = client.request(method, path, headers=admin_headers)
    assert response.status_code == 200, f"{path}: {response.text}"


@pytest.mark.parametrize("method,path", ADMIN_ONLY)
def test_vendedor_is_blocked_from_admin_areas(client, make_user, method, path):
    headers, _ = make_user("vendedor", "vendedor@teste.local")
    assert client.request(method, path, headers=headers).status_code == 403


@pytest.mark.parametrize("method,path", ADMIN_AND_VENDEDOR)
def test_vendedor_can_use_crm_areas(client, make_user, method, path):
    headers, _ = make_user("vendedor", "vendedor@teste.local")
    assert client.request(method, path, headers=headers).status_code == 200


@pytest.mark.parametrize("method,path", ADMIN_ONLY + ADMIN_AND_VENDEDOR)
def test_aluno_is_blocked_from_every_staff_area(client, make_user, create_lead, method, path):
    lead = create_lead()
    headers, _ = make_user("aluno", "aluno@teste.local", lead_id=lead["id"])
    assert client.request(method, path, headers=headers).status_code == 403


def test_vendedor_cannot_create_admin_resources(client, make_user, course_setup):
    headers, _ = make_user("vendedor", "vendedor@teste.local")

    assert client.post(
        "/api/products", headers=headers, json={"nome": "X", "preco": 10}
    ).status_code == 403
    assert client.post(
        "/api/campaigns", headers=headers, json={"nome": "X", "canal": "Instagram"}
    ).status_code == 403
    assert client.post(
        "/api/courses", headers=headers, json={"product_id": course_setup["product_id"], "nome": "X"}
    ).status_code == 403
    assert client.post(
        f"/api/courses/{course_setup['course_id']}/contents",
        headers=headers,
        json={"titulo": "X", "tipo": "video", "ordem": 9},
    ).status_code == 403
    assert client.post(
        "/api/users",
        headers=headers,
        json={"nome": "X", "email": "x@x.com", "senha": "senha-12345", "role": "admin"},
    ).status_code == 403
    assert client.post(
        "/api/course-contents/upload", headers=headers, files={"file": ("a.pdf", b"%PDF-1.4")}
    ).status_code == 403


def test_vendedor_cannot_read_student_area_endpoints(client, make_user, course_setup):
    headers, _ = make_user("vendedor", "vendedor@teste.local")
    assert client.get("/api/my/enrollments", headers=headers).status_code == 403
    assert client.get("/api/enrollments/1", headers=headers).status_code == 403


def test_aluno_cannot_write_crm_or_sales(client, make_user, create_lead, course_setup):
    lead = create_lead()
    headers, _ = make_user("aluno", "aluno@teste.local", lead_id=lead["id"])

    assert client.post("/api/leads", headers=headers, json={"nome": "x"}).status_code == 403
    assert client.put(f"/api/leads/{lead['id']}", headers=headers, json={}).status_code == 403
    assert client.patch(
        f"/api/leads/{lead['id']}/status", headers=headers, json={"status": "Fechado"}
    ).status_code == 403
    assert client.post(
        "/api/sales",
        headers=headers,
        json={
            "lead_id": lead["id"],
            "product_id": course_setup["product_id"],
            "forma_pagamento": "Pix",
        },
    ).status_code == 403
    assert client.patch(
        "/api/sales/1/payment-status", headers=headers, json={"status_pagamento": "Pago"}
    ).status_code == 403


def test_public_ebook_endpoint_needs_no_auth_but_requires_consent(client):
    payload = {"nome": "Ana", "email": "ana@exemplo.com", "whatsapp": "(24) 99999-0000", "consentimento": True}
    assert client.post("/api/public/leads/ebook", json=payload).status_code == 201
    # E-mail repetido NÃO bloqueia o fluxo e NÃO cria outro Lead (2.1.0-rc.1).
    assert client.post("/api/public/leads/ebook", json=payload).status_code == 201
    no_consent = {"nome": "Bia", "email": "bia@exemplo.com", "whatsapp": "(24) 99999-0000", "consentimento": False}
    assert client.post("/api/public/leads/ebook", json=no_consent).status_code == 400
