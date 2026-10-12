"""Fluxo CRM → Venda → Financeiro → LMS, com suspensão e restauração de acesso."""

from decimal import Decimal


def _sale(client, headers, lead_id, product_id, status="Pago", quantidade=1):
    response = client.post(
        "/api/sales",
        headers=headers,
        json={
            "lead_id": lead_id,
            "product_id": product_id,
            "quantidade": quantidade,
            "forma_pagamento": "Pix",
            "status_pagamento": status,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _student(client, make_user, lead_id, email="aluno@teste.local"):
    headers, _ = make_user("aluno", email, lead_id=lead_id)
    return headers


def _my_enrollments(client, headers):
    response = client.get("/api/my/enrollments", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_paid_sale_closes_lead_and_creates_enrollment(
    client, admin_headers, make_user, create_lead, course_setup
):
    lead = create_lead()
    sale = _sale(client, admin_headers, lead["id"], course_setup["product_id"], quantidade=2)

    assert Decimal(str(sale["valor_unitario"])) == Decimal("147")
    assert Decimal(str(sale["valor_total"])) == Decimal("294")
    assert client.get(f"/api/leads/{lead['id']}", headers=admin_headers).json()["status"] == "Fechado"

    student = _student(client, make_user, lead["id"])
    enrollments = _my_enrollments(client, student)
    assert len(enrollments) == 1
    assert enrollments[0]["status"] == "Acesso liberado"
    assert enrollments[0]["progresso"] == 0

    admin_view = client.get("/api/enrollments", headers=admin_headers).json()
    assert len(admin_view) == 1


def test_pending_sale_does_not_enroll_until_paid(
    client, admin_headers, make_user, create_lead, course_setup
):
    lead = create_lead()
    sale = _sale(client, admin_headers, lead["id"], course_setup["product_id"], status="Pendente")
    student = _student(client, make_user, lead["id"])
    assert _my_enrollments(client, student) == []
    assert client.get(f"/api/leads/{lead['id']}", headers=admin_headers).json()["status"] == "Lead"

    paid = client.patch(
        f"/api/sales/{sale['id']}/payment-status",
        headers=admin_headers,
        json={"status_pagamento": "Pago"},
    )
    assert paid.status_code == 200
    assert len(_my_enrollments(client, student)) == 1


def test_sale_without_course_does_not_create_enrollment(client, admin_headers, create_lead):
    product = client.post(
        "/api/products", headers=admin_headers, json={"nome": "Consultoria", "preco": 500}
    ).json()
    lead = create_lead()
    _sale(client, admin_headers, lead["id"], product["id"])
    assert client.get("/api/enrollments", headers=admin_headers).json() == []


def test_sale_validations(client, admin_headers, create_lead, course_setup):
    lead = create_lead()
    base = {
        "lead_id": lead["id"],
        "product_id": course_setup["product_id"],
        "forma_pagamento": "Pix",
    }
    assert client.post("/api/sales", headers=admin_headers, json={**base, "quantidade": 0}).status_code == 400
    assert client.post(
        "/api/sales", headers=admin_headers, json={**base, "status_pagamento": "Qualquer"}
    ).status_code == 400
    assert client.post("/api/sales", headers=admin_headers, json={**base, "lead_id": 99999}).status_code == 404
    assert client.post("/api/sales", headers=admin_headers, json={**base, "product_id": 99999}).status_code == 404
    assert client.patch(
        "/api/sales/99999/payment-status", headers=admin_headers, json={"status_pagamento": "Pago"}
    ).status_code == 404

    inactive = client.post(
        "/api/products", headers=admin_headers, json={"nome": "Inativo", "preco": 10, "ativo": False}
    ).json()
    assert client.post(
        "/api/sales", headers=admin_headers, json={**base, "product_id": inactive["id"]}
    ).status_code == 400


def test_refund_suspends_access_and_paid_again_restores_it(
    client, admin_headers, make_user, create_lead, course_setup
):
    lead = create_lead()
    sale = _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    student = _student(client, make_user, lead["id"])
    enrollment_id = _my_enrollments(client, student)[0]["id"]
    content_id = course_setup["content_ids"][0]

    assert client.get(f"/api/enrollments/{enrollment_id}", headers=student).status_code == 200

    refunded = client.patch(
        f"/api/sales/{sale['id']}/payment-status",
        headers=admin_headers,
        json={"status_pagamento": "Reembolsado"},
    )
    assert refunded.status_code == 200
    assert _my_enrollments(client, student)[0]["status"] == "Acesso suspenso"

    # Aluno perde o acesso a todo o conteúdo da matrícula.
    assert client.get(f"/api/enrollments/{enrollment_id}", headers=student).status_code == 403
    assert client.post(f"/api/enrollments/{enrollment_id}/access", headers=student).status_code == 403
    assert client.post(
        f"/api/enrollments/{enrollment_id}/contents/{content_id}/open", headers=student
    ).status_code == 403
    assert client.patch(
        f"/api/enrollments/{enrollment_id}/contents/{content_id}/progress",
        headers=student,
        json={"progresso": 100},
    ).status_code == 403

    restored = client.patch(
        f"/api/sales/{sale['id']}/payment-status",
        headers=admin_headers,
        json={"status_pagamento": "Pago"},
    )
    assert restored.status_code == 200
    assert _my_enrollments(client, student)[0]["status"] == "Acesso liberado"
    assert client.get(f"/api/enrollments/{enrollment_id}", headers=student).status_code == 200


def test_cancellation_also_suspends_access(
    client, admin_headers, make_user, create_lead, course_setup
):
    lead = create_lead()
    sale = _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    student = _student(client, make_user, lead["id"])
    client.patch(
        f"/api/sales/{sale['id']}/payment-status",
        headers=admin_headers,
        json={"status_pagamento": "Cancelado"},
    )
    assert _my_enrollments(client, student)[0]["status"] == "Acesso suspenso"


def test_admin_activity_does_not_reactivate_a_suspended_enrollment(
    client, admin_headers, make_user, create_lead, course_setup
):
    """Regressão: abrir conteúdo/atualizar progresso como admin reativava a matrícula."""
    lead = create_lead()
    sale = _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    student = _student(client, make_user, lead["id"])
    enrollment_id = _my_enrollments(client, student)[0]["id"]
    content_id = course_setup["content_ids"][0]

    client.patch(
        f"/api/sales/{sale['id']}/payment-status",
        headers=admin_headers,
        json={"status_pagamento": "Reembolsado"},
    )

    opened = client.post(
        f"/api/enrollments/{enrollment_id}/contents/{content_id}/open", headers=admin_headers
    )
    progressed = client.patch(
        f"/api/enrollments/{enrollment_id}/contents/{content_id}/progress",
        headers=admin_headers,
        json={"progresso": 100},
    )
    assert opened.status_code == 200
    assert progressed.status_code == 200
    assert _my_enrollments(client, student)[0]["status"] == "Acesso suspenso"
    assert client.get(f"/api/enrollments/{enrollment_id}", headers=student).status_code == 403


def test_student_progress_and_course_completion(
    client, admin_headers, make_user, create_lead, course_setup
):
    lead = create_lead()
    _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    student = _student(client, make_user, lead["id"])
    enrollment_id = _my_enrollments(client, student)[0]["id"]
    first, second = course_setup["content_ids"]

    assert client.post(f"/api/enrollments/{enrollment_id}/access", headers=student).json()[
        "status"
    ] == "Em andamento"
    assert client.post(
        f"/api/enrollments/{enrollment_id}/contents/{first}/open", headers=student
    ).status_code == 200

    half = client.patch(
        f"/api/enrollments/{enrollment_id}/contents/{first}/progress",
        headers=student,
        json={"progresso": 100},
    ).json()
    assert half["progresso_curso"] == 50
    assert half["status_curso"] == "Em andamento"

    done = client.patch(
        f"/api/enrollments/{enrollment_id}/contents/{second}/progress",
        headers=student,
        json={"progresso": 100},
    ).json()
    assert done["progresso_curso"] == 100
    assert done["status_curso"] == "Concluído"

    for invalid in (-1, 101):
        assert client.patch(
            f"/api/enrollments/{enrollment_id}/contents/{first}/progress",
            headers=student,
            json={"progresso": invalid},
        ).status_code == 400

    detail = client.get(f"/api/enrollments/{enrollment_id}", headers=student).json()
    assert detail["status"] == "Concluído"
    assert detail["concluido_em"] is not None


def test_content_from_another_course_is_rejected(
    client, admin_headers, make_user, create_lead, course_setup
):
    other_product = client.post(
        "/api/products", headers=admin_headers, json={"nome": "Outro", "preco": 50}
    ).json()
    other_course = client.post(
        "/api/courses", headers=admin_headers, json={"product_id": other_product["id"], "nome": "Outro curso"}
    ).json()
    foreign_content = client.post(
        f"/api/courses/{other_course['id']}/contents",
        headers=admin_headers,
        json={"titulo": "Alheio", "tipo": "material", "ordem": 1},
    ).json()

    lead = create_lead()
    _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    student = _student(client, make_user, lead["id"])
    enrollment_id = _my_enrollments(client, student)[0]["id"]

    response = client.post(
        f"/api/enrollments/{enrollment_id}/contents/{foreign_content['id']}/open", headers=student
    )
    assert response.status_code == 400


def test_finance_summary_reflects_payment_statuses(client, admin_headers, create_lead, course_setup):
    lead = create_lead()
    product_id = course_setup["product_id"]  # R$ 147
    _sale(client, admin_headers, lead["id"], product_id, status="Pago")  # 147
    _sale(client, admin_headers, lead["id"], product_id, status="Pago", quantidade=2)  # 294
    _sale(client, admin_headers, lead["id"], product_id, status="Pendente")  # 147
    _sale(client, admin_headers, lead["id"], product_id, status="Cancelado")  # 147
    refunded = _sale(client, admin_headers, lead["id"], product_id, status="Pago")  # 147 -> reembolsa
    client.patch(
        f"/api/sales/{refunded['id']}/payment-status",
        headers=admin_headers,
        json={"status_pagamento": "Reembolsado"},
    )

    summary = client.get("/api/finance/summary", headers=admin_headers).json()
    assert summary["receita_paga"] == 441
    assert summary["a_receber"] == 147
    assert summary["cancelado"] == 147
    assert summary["reembolsado"] == 147
    assert summary["saldo_liquido"] == 294
    assert summary["quantidades"] == {"Pago": 2, "Pendente": 1, "Cancelado": 1, "Reembolsado": 1}


def test_sales_list_and_pending_alert(client, admin_headers, create_lead, course_setup):
    lead = create_lead()
    _sale(client, admin_headers, lead["id"], course_setup["product_id"], status="Pendente")
    sales = client.get("/api/sales", headers=admin_headers).json()
    assert len(sales) == 1
    assert sales[0]["lead_nome"] == lead["nome"]
    alerts = client.get("/api/automation/insights", headers=admin_headers).json()["alerts"]
    assert any(alert["tipo"] == "financeiro" for alert in alerts)


def test_analytics_with_sales_and_enrollments(
    client, admin_headers, make_user, create_lead, course_setup
):
    lead = create_lead()
    _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    student = _student(client, make_user, lead["id"])
    enrollment_id = _my_enrollments(client, student)[0]["id"]
    client.post(f"/api/enrollments/{enrollment_id}/access", headers=student)

    for path in (
        "/api/dashboard/summary",
        "/api/customer-analytics",
        "/api/marketing-analytics",
        "/api/lms-analytics",
        "/api/finance/summary",
    ):
        response = client.get(path, headers=admin_headers)
        assert response.status_code == 200, f"{path}: {response.text}"


def test_course_rules(client, admin_headers, course_setup):
    # Um produto só pode ter um curso.
    duplicate = client.post(
        "/api/courses",
        headers=admin_headers,
        json={"product_id": course_setup["product_id"], "nome": "Duplicado"},
    )
    assert duplicate.status_code == 409
    assert client.post(
        "/api/courses", headers=admin_headers, json={"product_id": 99999, "nome": "X"}
    ).status_code == 404

    course_id = course_setup["course_id"]
    # Ordem ativa repetida e tipo inválido.
    assert client.post(
        f"/api/courses/{course_id}/contents",
        headers=admin_headers,
        json={"titulo": "Repetido", "tipo": "video", "ordem": 1},
    ).status_code == 409
    assert client.post(
        f"/api/courses/{course_id}/contents",
        headers=admin_headers,
        json={"titulo": "Tipo ruim", "tipo": "podcast", "ordem": 7},
    ).status_code == 400


def test_content_admin_create_edit_deactivate(client, admin_headers, course_setup):
    course_id = course_setup["course_id"]
    content_id = course_setup["content_ids"][0]

    edited = client.put(
        f"/api/course-contents/{content_id}",
        headers=admin_headers,
        json={
            "titulo": "Abertura revisada",
            "tipo": "apostila",
            "ordem": 1,
            "duracao_minutos": 10,
            "url_conteudo": "https://exemplo.com/material.pdf",
            "ativo": True,
        },
    )
    assert edited.status_code == 200
    assert edited.json()["titulo"] == "Abertura revisada"

    removed = client.delete(f"/api/course-contents/{content_id}", headers=admin_headers)
    assert removed.status_code == 200
    assert removed.json()["ativo"] is False

    listed = client.get(f"/api/courses/{course_id}/contents", headers=admin_headers).json()
    assert {item["id"]: item["ativo"] for item in listed}[content_id] is False

    # Reativar: a ordem 1 agora está livre.
    reactivated = client.put(
        f"/api/course-contents/{content_id}",
        headers=admin_headers,
        json={"titulo": "Abertura revisada", "tipo": "apostila", "ordem": 1, "ativo": True},
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["ativo"] is True
