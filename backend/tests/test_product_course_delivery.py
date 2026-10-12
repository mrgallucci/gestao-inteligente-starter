"""2.1.0-rc.1 — Produto → Curso → Matrícula: visibilidade e entrega."""


def _product(client, headers, nome="E-book Pago", preco=47, ativo=True):
    response = client.post(
        "/api/products", headers=headers, json={"nome": nome, "preco": preco, "ativo": ativo}
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _sale(client, headers, lead_id, product_id, status="Pago"):
    response = client.post(
        "/api/sales",
        headers=headers,
        json={"lead_id": lead_id, "product_id": product_id, "forma_pagamento": "Pix", "status_pagamento": status},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _by_id(items, item_id):
    return next(item for item in items if item["id"] == item_id)


def test_products_list_shows_linked_course_or_none(client, admin_headers, course_setup):
    free_id = _product(client, admin_headers)
    items = client.get("/api/products", headers=admin_headers).json()

    linked = _by_id(items, course_setup["product_id"])
    assert linked["curso_id"] == course_setup["course_id"]
    assert linked["curso_nome"] == "IA no Dia a Dia"
    assert linked["libera_lms"] is True

    plain = _by_id(items, free_id)
    assert plain["curso_id"] is None
    assert plain["curso_nome"] is None
    assert plain["libera_lms"] is False


def test_inactive_course_does_not_release_lms_flag(client, admin_headers):
    product_id = _product(client, admin_headers)
    created = client.post(
        "/api/courses",
        headers=admin_headers,
        json={"product_id": product_id, "nome": "Curso parado", "ativo": False},
    )
    assert created.status_code == 201
    item = _by_id(client.get("/api/products", headers=admin_headers).json(), product_id)
    assert item["curso_id"] == created.json()["id"]
    assert item["libera_lms"] is False


def test_one_product_has_at_most_one_course(client, admin_headers, course_setup):
    response = client.post(
        "/api/courses",
        headers=admin_headers,
        json={"product_id": course_setup["product_id"], "nome": "Outro curso"},
    )
    assert response.status_code == 409


def test_course_creation_validation_and_rbac(client, admin_headers, make_user):
    product_id = _product(client, admin_headers)
    blank = client.post(
        "/api/courses", headers=admin_headers, json={"product_id": product_id, "nome": "   "}
    )
    assert blank.status_code == 422
    assert isinstance(blank.json()["detail"], str)

    missing_product = client.post(
        "/api/courses", headers=admin_headers, json={"product_id": 99999, "nome": "X"}
    )
    assert missing_product.status_code == 404

    seller_headers, _ = make_user("vendedor", "vendedor@exemplo.com")
    forbidden = client.post(
        "/api/courses", headers=seller_headers, json={"product_id": product_id, "nome": "Y"}
    )
    assert forbidden.status_code == 403


def test_sale_of_product_without_course_is_allowed_and_flagged_not_applicable(
    client, admin_headers, create_lead
):
    lead = create_lead()
    product_id = _product(client, admin_headers)
    sale = _sale(client, admin_headers, lead["id"], product_id)

    assert client.get("/api/enrollments", headers=admin_headers).json() == []
    row = _by_id(client.get("/api/sales", headers=admin_headers).json(), sale["id"])
    assert row["entrega_tipo"] is None
    assert row["entrega_status"] == "Não aplicável"
    assert row["matricula_status"] is None
    assert "não libera curso" in row["entrega_detalhe"].lower()


def test_paid_sale_with_course_reports_lms_delivery(client, admin_headers, create_lead, course_setup):
    lead = create_lead()
    sale = _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    row = _by_id(client.get("/api/sales", headers=admin_headers).json(), sale["id"])
    assert row["entrega_tipo"] == "LMS"
    assert row["entrega_status"] == "Acesso liberado"
    assert row["curso_nome"] == "IA no Dia a Dia"
    assert row["matricula_status"] == "Acesso liberado"


def test_pending_sale_with_course_has_no_enrollment_yet(client, admin_headers, create_lead, course_setup):
    lead = create_lead()
    sale = _sale(client, admin_headers, lead["id"], course_setup["product_id"], status="Pendente")
    row = _by_id(client.get("/api/sales", headers=admin_headers).json(), sale["id"])
    assert row["entrega_tipo"] == "LMS"
    assert row["entrega_status"] == "Aguardando pagamento"
    assert row["matricula_status"] is None


def test_refund_suspends_and_paid_again_restores_in_sales_listing(
    client, admin_headers, create_lead, course_setup
):
    lead = create_lead()
    sale = _sale(client, admin_headers, lead["id"], course_setup["product_id"])

    def row():
        return _by_id(client.get("/api/sales", headers=admin_headers).json(), sale["id"])

    def status():
        return row()["matricula_status"]

    assert status() == "Acesso liberado"
    assert row()["entrega_status"] == "Acesso liberado"
    patch = lambda value: client.patch(  # noqa: E731
        f"/api/sales/{sale['id']}/payment-status",
        headers=admin_headers,
        json={"status_pagamento": value},
    )
    assert patch("Reembolsado").status_code == 200
    assert status() == "Acesso suspenso"
    assert (row()["entrega_tipo"], row()["entrega_status"]) == ("LMS", "Acesso suspenso")
    assert patch("Pago").status_code == 200
    assert status() == "Acesso liberado"
    assert row()["entrega_status"] == "Acesso liberado"


def test_inactive_course_sale_is_not_applicable(client, admin_headers, create_lead):
    lead = create_lead()
    product_id = _product(client, admin_headers)
    client.post(
        "/api/courses",
        headers=admin_headers,
        json={"product_id": product_id, "nome": "Inativo", "ativo": False},
    )
    sale = _sale(client, admin_headers, lead["id"], product_id)
    row = _by_id(client.get("/api/sales", headers=admin_headers).json(), sale["id"])
    assert row["entrega_status"] == "Não aplicável"
    assert row["curso_ativo"] is False
    assert "inativo" in row["aviso"].lower()
    assert client.get("/api/enrollments", headers=admin_headers).json() == []


def test_lms_is_never_a_status_and_non_paid_never_shows_access(client, admin_headers, create_lead, course_setup):
    """Pendente/Cancelado/Reembolsado (sem acesso prévio) jamais aparecem como acesso liberado."""
    expected = {
        "Pendente": "Aguardando pagamento",
        "Cancelado": "Não aplicável",
        "Reembolsado": "Não aplicável",
    }
    for status, esperado in expected.items():
        lead = create_lead(email=f"{status.lower()}@exemplo.com")
        sale = _sale(client, admin_headers, lead["id"], course_setup["product_id"], status=status)
        row = _by_id(client.get("/api/sales", headers=admin_headers).json(), sale["id"])
        assert row["entrega_tipo"] == "LMS"
        assert row["entrega_status"] == esperado, status
        assert row["entrega_status"] not in ("LMS", "Acesso LMS", "Acesso liberado")


def test_refund_with_another_paid_sale_keeps_access_message(client, admin_headers, create_lead, course_setup):
    lead = create_lead()
    first = _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    _sale(client, admin_headers, lead["id"], course_setup["product_id"])
    client.patch(
        f"/api/sales/{first['id']}/payment-status",
        headers=admin_headers,
        json={"status_pagamento": "Reembolsado"},
    )
    row = _by_id(client.get("/api/sales", headers=admin_headers).json(), first["id"])
    assert row["matricula_status"] == "Acesso liberado"
    assert "outra venda" in row["entrega_detalhe"].lower()


def test_paid_sale_before_course_link_is_flagged_without_enrollment(client, admin_headers, create_lead):
    lead = create_lead()
    product_id = _product(client, admin_headers)
    sale = _sale(client, admin_headers, lead["id"], product_id)  # ainda sem curso
    client.post("/api/courses", headers=admin_headers, json={"product_id": product_id, "nome": "Tardio"})
    row = _by_id(client.get("/api/sales", headers=admin_headers).json(), sale["id"])
    assert row["entrega_tipo"] == "LMS"
    assert row["entrega_status"] == "Matrícula não gerada"
    assert "atenção" in row["aviso"].lower()
    # Sem matrícula retroativa automática: vincular o curso depois NÃO matricula quem já pagou.
    assert client.get("/api/enrollments", headers=admin_headers).json() == []
    again = _by_id(client.get("/api/sales", headers=admin_headers).json(), sale["id"])
    assert again["entrega_status"] == "Matrícula não gerada"
