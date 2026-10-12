"""Ownership: o aluno só acessa a própria matrícula."""

from tests.conftest import new_lead_payload


def _enroll(client, admin_headers, lead_id, product_id):
    sale = client.post(
        "/api/sales",
        headers=admin_headers,
        json={
            "lead_id": lead_id,
            "product_id": product_id,
            "quantidade": 1,
            "forma_pagamento": "Pix",
            "status_pagamento": "Pago",
        },
    )
    assert sale.status_code == 201, sale.text


def _enrollment_id(client, headers):
    items = client.get("/api/my/enrollments", headers=headers).json()
    assert len(items) == 1
    return items[0]["id"]


def _two_students(client, admin_headers, make_user, create_lead, course_setup):
    lead_a = create_lead(nome="Aluno A", email="a@exemplo.com")
    lead_b = create_lead(nome="Aluno B", email="b@exemplo.com")
    headers_a, _ = make_user("aluno", "a@teste.local", lead_id=lead_a["id"])
    headers_b, _ = make_user("aluno", "b@teste.local", lead_id=lead_b["id"])
    _enroll(client, admin_headers, lead_a["id"], course_setup["product_id"])
    _enroll(client, admin_headers, lead_b["id"], course_setup["product_id"])
    return headers_a, headers_b


def test_student_lists_only_own_enrollments(
    client, admin_headers, make_user, create_lead, course_setup
):
    headers_a, headers_b = _two_students(client, admin_headers, make_user, create_lead, course_setup)
    mine_a = client.get("/api/my/enrollments", headers=headers_a).json()
    mine_b = client.get("/api/my/enrollments", headers=headers_b).json()
    assert len(mine_a) == 1 and len(mine_b) == 1
    assert mine_a[0]["id"] != mine_b[0]["id"]


def test_student_cannot_touch_someone_elses_enrollment(
    client, admin_headers, make_user, create_lead, course_setup
):
    headers_a, headers_b = _two_students(client, admin_headers, make_user, create_lead, course_setup)
    enrollment_a = _enrollment_id(client, headers_a)
    content_id = course_setup["content_ids"][0]

    # Aluno B tentando usar a matrícula do aluno A (trocando o ID na URL).
    assert client.get(f"/api/enrollments/{enrollment_a}", headers=headers_b).status_code == 403
    assert client.post(f"/api/enrollments/{enrollment_a}/access", headers=headers_b).status_code == 403
    assert client.post(
        f"/api/enrollments/{enrollment_a}/contents/{content_id}/open", headers=headers_b
    ).status_code == 403
    assert client.patch(
        f"/api/enrollments/{enrollment_a}/contents/{content_id}/progress",
        headers=headers_b,
        json={"progresso": 100},
    ).status_code == 403

    # O dono continua com acesso.
    assert client.get(f"/api/enrollments/{enrollment_a}", headers=headers_a).status_code == 200


def test_student_progress_does_not_leak_between_students(
    client, admin_headers, make_user, create_lead, course_setup
):
    headers_a, headers_b = _two_students(client, admin_headers, make_user, create_lead, course_setup)
    enrollment_a = _enrollment_id(client, headers_a)
    enrollment_b = _enrollment_id(client, headers_b)
    content_id = course_setup["content_ids"][0]

    update = client.patch(
        f"/api/enrollments/{enrollment_a}/contents/{content_id}/progress",
        headers=headers_a,
        json={"progresso": 50},
    )
    assert update.status_code == 200

    detail_b = client.get(f"/api/enrollments/{enrollment_b}", headers=headers_b).json()
    assert all(item["progresso"] == 0 for item in detail_b["conteudos"])


def test_nonexistent_enrollment_is_404_for_admin_and_403_or_404_for_student(
    client, admin_headers, make_user, create_lead
):
    lead = create_lead(**new_lead_payload(nome="Sem curso", email="sem@exemplo.com"))
    headers, _ = make_user("aluno", "sem@teste.local", lead_id=lead["id"])
    assert client.get("/api/enrollments/99999", headers=admin_headers).status_code == 404
    assert client.get("/api/enrollments/99999", headers=headers).status_code == 404
    assert client.get("/api/my/enrollments", headers=headers).json() == []


def test_student_without_lead_link_has_no_access(client, admin_headers, create_lead, course_setup):
    """Defesa em profundidade: aluno sem lead_id (dado legado) não acessa nada."""
    import main
    from database import SessionLocal
    from models import User

    lead = create_lead()
    _enroll(client, admin_headers, lead["id"], course_setup["product_id"])

    with SessionLocal() as db:
        db.add(
            User(
                nome="Aluno órfão",
                email="orfao@teste.local",
                senha_hash=main.PASSWORD_HASHER.hash("senha-12345"),
                role="aluno",
                lead_id=None,
                ativo=True,
            )
        )
        db.commit()

    from tests.conftest import login

    headers = login(client, "orfao@teste.local", "senha-12345")
    assert client.get("/api/my/enrollments", headers=headers).status_code == 403
