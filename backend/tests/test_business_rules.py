"""Regressão das regras N1–N4 (decisões de negócio da auditoria 2.0.1).

N1  Venda paga não faz o funil regredir (Pós-venda não volta para Fechado).
N2  Nova compra válida do mesmo curso restaura matrícula suspensa.
N3  Cancelar/reembolsar uma venda não suspende se há outra venda Paga do curso.
N4  A restauração preserva o estado acadêmico (Concluído / Em andamento).
"""

from tests.test_sales_lms_flow import _my_enrollments, _sale, _student


def _set_status(client, headers, lead_id, status):
    response = client.patch(
        f"/api/leads/{lead_id}/status", headers=headers, json={"status": status}
    )
    assert response.status_code == 200, response.text


def _lead_status(client, headers, lead_id):
    return client.get(f"/api/leads/{lead_id}", headers=headers).json()["status"]


def _set_payment(client, headers, sale_id, status):
    response = client.patch(
        f"/api/sales/{sale_id}/payment-status",
        headers=headers,
        json={"status_pagamento": status},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _enrollment(client, student):
    items = _my_enrollments(client, student)
    assert len(items) == 1
    return items[0]


def _progress(client, headers, enrollment_id, content_id, value):
    response = client.patch(
        f"/api/enrollments/{enrollment_id}/contents/{content_id}/progress",
        headers=headers,
        json={"progresso": value},
    )
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------------------
# N1 — o funil não regride
# ---------------------------------------------------------------------------


def test_n1_new_paid_sale_keeps_lead_in_pos_venda(
    client, admin_headers, create_lead, course_setup
):
    lead = create_lead()
    _set_status(client, admin_headers, lead["id"], "Pós-venda")
    _sale(client, admin_headers, lead["id"], course_setup["product_id"], status="Pago")
    assert _lead_status(client, admin_headers, lead["id"]) == "Pós-venda"


def test_n1_payment_status_change_to_paid_keeps_pos_venda(
    client, admin_headers, create_lead, course_setup
):
    lead = create_lead()
    sale = _sale(client, admin_headers, lead["id"], course_setup["product_id"], status="Pendente")
    _set_status(client, admin_headers, lead["id"], "Pós-venda")
    _set_payment(client, admin_headers, sale["id"], "Pago")
    assert _lead_status(client, admin_headers, lead["id"]) == "Pós-venda"


def test_n1_other_stages_still_become_fechado(
    client, admin_headers, create_lead, course_setup
):
    """Controle: o comportamento atual para as demais etapas não muda."""
    for index, stage in enumerate(("Lead", "Proposta", "Negociação", "Perdido")):
        lead = create_lead(nome=f"Lead {index}", email=f"n1-{index}@exemplo.com")
        _set_status(client, admin_headers, lead["id"], stage)
        _sale(client, admin_headers, lead["id"], course_setup["product_id"], status="Pago")
        assert _lead_status(client, admin_headers, lead["id"]) == "Fechado", stage


# ---------------------------------------------------------------------------
# N2 — nova compra após suspensão
# ---------------------------------------------------------------------------


def test_n2_new_paid_sale_restores_suspended_enrollment(
    client, admin_headers, make_user, create_lead, course_setup
):
    lead = create_lead()
    first = _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    student = _student(client, make_user, lead["id"])
    enrollment_id = _enrollment(client, student)["id"]

    _set_payment(client, admin_headers, first["id"], "Reembolsado")
    assert _enrollment(client, student)["status"] == "Acesso suspenso"
    assert client.get(f"/api/enrollments/{enrollment_id}", headers=student).status_code == 403

    _sale(client, admin_headers, lead["id"], course_setup["product_id"], status="Pago")

    assert _enrollment(client, student)["status"] == "Acesso liberado"
    assert client.get(f"/api/enrollments/{enrollment_id}", headers=student).status_code == 200
    # Continua sendo UMA matrícula (não duplica).
    assert len(client.get("/api/enrollments", headers=admin_headers).json()) == 1


def test_n2_new_pending_sale_does_not_restore(
    client, admin_headers, make_user, create_lead, course_setup
):
    lead = create_lead()
    first = _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    student = _student(client, make_user, lead["id"])
    _set_payment(client, admin_headers, first["id"], "Cancelado")

    _sale(client, admin_headers, lead["id"], course_setup["product_id"], status="Pendente")
    assert _enrollment(client, student)["status"] == "Acesso suspenso"


# ---------------------------------------------------------------------------
# N3 — várias vendas do mesmo curso
# ---------------------------------------------------------------------------


def test_n3_refund_keeps_access_when_another_paid_sale_exists(
    client, admin_headers, make_user, create_lead, course_setup
):
    lead = create_lead()
    product_id = course_setup["product_id"]
    first = _sale(client, admin_headers, lead["id"], product_id)
    second = _sale(client, admin_headers, lead["id"], product_id)
    student = _student(client, make_user, lead["id"])
    enrollment_id = _enrollment(client, student)["id"]

    _set_payment(client, admin_headers, first["id"], "Reembolsado")
    assert _enrollment(client, student)["status"] == "Acesso liberado"
    assert client.get(f"/api/enrollments/{enrollment_id}", headers=student).status_code == 200

    # Perdendo também a última venda paga, o acesso é suspenso.
    _set_payment(client, admin_headers, second["id"], "Cancelado")
    assert _enrollment(client, student)["status"] == "Acesso suspenso"
    assert client.get(f"/api/enrollments/{enrollment_id}", headers=student).status_code == 403


def test_n3_only_paid_sales_of_same_lead_and_course_count(
    client, admin_headers, make_user, create_lead, course_setup
):
    lead = create_lead()
    other_lead = create_lead(nome="Outro", email="outro@exemplo.com")
    product_id = course_setup["product_id"]
    other_product = client.post(
        "/api/products", headers=admin_headers, json={"nome": "Consultoria", "preco": 900}
    ).json()

    paid = _sale(client, admin_headers, lead["id"], product_id)
    student = _student(client, make_user, lead["id"])

    # Nenhuma destas dá direito à matrícula deste Lead neste curso.
    _sale(client, admin_headers, lead["id"], product_id, status="Pendente")
    _sale(client, admin_headers, lead["id"], other_product["id"], status="Pago")
    _sale(client, admin_headers, other_lead["id"], product_id, status="Pago")

    _set_payment(client, admin_headers, paid["id"], "Reembolsado")
    assert _enrollment(client, student)["status"] == "Acesso suspenso"


# ---------------------------------------------------------------------------
# N4 — a restauração preserva o estado acadêmico
# ---------------------------------------------------------------------------


def test_n4_restore_keeps_em_andamento_and_progress(
    client, admin_headers, make_user, create_lead, course_setup
):
    lead = create_lead()
    sale = _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    student = _student(client, make_user, lead["id"])
    enrollment_id = _enrollment(client, student)["id"]
    first_content = course_setup["content_ids"][0]

    _progress(client, student, enrollment_id, first_content, 100)
    assert _enrollment(client, student)["status"] == "Em andamento"

    _set_payment(client, admin_headers, sale["id"], "Reembolsado")
    assert _enrollment(client, student)["status"] == "Acesso suspenso"

    _set_payment(client, admin_headers, sale["id"], "Pago")
    restored = _enrollment(client, student)
    assert restored["status"] == "Em andamento"
    assert restored["progresso"] == 50

    detail = client.get(f"/api/enrollments/{enrollment_id}", headers=student).json()
    by_id = {item["id"]: item["progresso"] for item in detail["conteudos"]}
    assert by_id[first_content] == 100


def test_n4_restore_keeps_concluido(
    client, admin_headers, make_user, create_lead, course_setup
):
    lead = create_lead()
    sale = _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    student = _student(client, make_user, lead["id"])
    enrollment_id = _enrollment(client, student)["id"]
    for content_id in course_setup["content_ids"]:
        _progress(client, student, enrollment_id, content_id, 100)
    assert _enrollment(client, student)["status"] == "Concluído"
    concluded_at = client.get(
        f"/api/enrollments/{enrollment_id}", headers=student
    ).json()["concluido_em"]
    assert concluded_at is not None

    _set_payment(client, admin_headers, sale["id"], "Cancelado")
    assert _enrollment(client, student)["status"] == "Acesso suspenso"

    _set_payment(client, admin_headers, sale["id"], "Pago")
    detail = client.get(f"/api/enrollments/{enrollment_id}", headers=student).json()
    assert detail["status"] == "Concluído"
    assert detail["concluido_em"] == concluded_at
    assert detail["progresso"] == 100


def test_n4_restore_without_prior_access_is_acesso_liberado(
    client, admin_headers, make_user, create_lead, course_setup
):
    lead = create_lead()
    sale = _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    student = _student(client, make_user, lead["id"])

    _set_payment(client, admin_headers, sale["id"], "Reembolsado")
    _set_payment(client, admin_headers, sale["id"], "Pago")
    assert _enrollment(client, student)["status"] == "Acesso liberado"


def test_n4_restore_via_new_sale_also_keeps_academic_state(
    client, admin_headers, make_user, create_lead, course_setup
):
    lead = create_lead()
    sale = _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    student = _student(client, make_user, lead["id"])
    enrollment_id = _enrollment(client, student)["id"]
    for content_id in course_setup["content_ids"]:
        _progress(client, student, enrollment_id, content_id, 100)

    _set_payment(client, admin_headers, sale["id"], "Reembolsado")
    _sale(client, admin_headers, lead["id"], course_setup["product_id"], status="Pago")
    assert _enrollment(client, student)["status"] == "Concluído"
