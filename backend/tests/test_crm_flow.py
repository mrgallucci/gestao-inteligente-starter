"""CRM: leads, funil, interações, follow-ups, campanhas e analytics."""

from datetime import datetime, timedelta

from tests.conftest import new_lead_payload


def test_create_edit_and_list_lead(client, admin_headers):
    created = client.post("/api/leads", headers=admin_headers, json=new_lead_payload())
    assert created.status_code == 201
    lead = created.json()
    assert lead["status"] == "Lead"
    assert lead["contatos"] == 0

    updated = client.put(
        f"/api/leads/{lead['id']}",
        headers=admin_headers,
        json=new_lead_payload(
            cargo="Diretora", segmento="Serviços", tamanho_equipe=25, status="Reunião"
        ),
    )
    assert updated.status_code == 200
    assert updated.json()["cargo"] == "Diretora"
    assert updated.json()["tamanho_equipe"] == 25
    assert updated.json()["status"] == "Reunião"

    fetched = client.get(f"/api/leads/{lead['id']}", headers=admin_headers)
    assert fetched.status_code == 200
    assert [item["id"] for item in client.get("/api/leads", headers=admin_headers).json()] == [
        lead["id"]
    ]
    assert client.get("/api/leads/99999", headers=admin_headers).status_code == 404


def test_vendedor_can_create_and_edit_leads(client, make_user):
    headers, _ = make_user("vendedor", "vendedor@teste.local")
    created = client.post("/api/leads", headers=headers, json=new_lead_payload())
    assert created.status_code == 201
    edited = client.put(
        f"/api/leads/{created.json()['id']}", headers=headers, json=new_lead_payload(cidade="Volta Redonda")
    )
    assert edited.status_code == 200


def test_pipeline_stage_change_and_invalid_stage(client, admin_headers, create_lead):
    lead = create_lead()
    for stage in (
        "Contato realizado",
        "Interessado",
        "Reunião",
        "Proposta",
        "Negociação",
        "Fechado",
        "Pós-venda",
        "Perdido",
    ):
        response = client.patch(
            f"/api/leads/{lead['id']}/status", headers=admin_headers, json={"status": stage}
        )
        assert response.status_code == 200, stage
        assert response.json()["status"] == stage

    invalid = client.patch(
        f"/api/leads/{lead['id']}/status", headers=admin_headers, json={"status": "Inexistente"}
    )
    assert invalid.status_code == 400


def test_lost_lead_keeps_loss_reason(client, admin_headers, create_lead):
    lead = create_lead()
    response = client.put(
        f"/api/leads/{lead['id']}",
        headers=admin_headers,
        json=new_lead_payload(status="Perdido", motivo_perda="Sem orçamento"),
    )
    assert response.status_code == 200
    assert response.json()["motivo_perda"] == "Sem orçamento"


def test_interaction_updates_contact_counter_and_history(client, admin_headers, create_lead):
    lead = create_lead()
    whatsapp = client.post(
        f"/api/leads/{lead['id']}/interactions",
        headers=admin_headers,
        json={"tipo": "WhatsApp", "descricao": "Primeiro contato", "resultado": "Interessado"},
    )
    note = client.post(
        f"/api/leads/{lead['id']}/interactions",
        headers=admin_headers,
        json={"tipo": "Observação", "descricao": "Anotação interna"},
    )
    assert whatsapp.status_code == 201 and note.status_code == 201

    history = client.get(f"/api/leads/{lead['id']}/interactions", headers=admin_headers).json()
    assert len(history) == 2
    # Observação não conta como contato.
    assert client.get(f"/api/leads/{lead['id']}", headers=admin_headers).json()["contatos"] == 1

    assert client.post(
        "/api/leads/99999/interactions",
        headers=admin_headers,
        json={"tipo": "WhatsApp", "descricao": "x"},
    ).status_code == 404


def test_followups_agenda_merges_interactions_and_next_actions(client, admin_headers, create_lead):
    future = (datetime.now() + timedelta(days=2)).replace(microsecond=0).isoformat()
    past = (datetime.now() - timedelta(days=2)).replace(microsecond=0).isoformat()

    lead = create_lead(proxima_acao="Enviar proposta", proxima_acao_em=future)
    client.post(
        f"/api/leads/{lead['id']}/interactions",
        headers=admin_headers,
        json={"tipo": "Ligação", "descricao": "Retornar", "follow_up_em": past},
    )

    items = client.get("/api/followups", headers=admin_headers).json()
    sources = {item["source"] for item in items}
    assert sources == {"interacao", "proxima_acao"}
    # Ordenados por data: o vencido vem primeiro.
    assert items[0]["source"] == "interacao"

    insights = client.get("/api/automation/insights", headers=admin_headers).json()
    assert any(alert["tipo"] == "followup" for alert in insights["alerts"])


def test_followups_ignore_closed_leads_next_actions(client, admin_headers, create_lead):
    future = (datetime.now() + timedelta(days=2)).replace(microsecond=0).isoformat()
    create_lead(status="Pós-venda", proxima_acao="Pesquisa", proxima_acao_em=future)
    create_lead(
        nome="Perdido", email="perdido@exemplo.com", status="Perdido", proxima_acao_em=future
    )
    assert client.get("/api/followups", headers=admin_headers).json() == []


def test_campaign_attribution_and_marketing_metrics(client, admin_headers):
    campaign = client.post(
        "/api/campaigns",
        headers=admin_headers,
        json={
            "nome": "Lançamento",
            "canal": "Instagram",
            "custo": 200,
            "utm_source": "instagram",
            "utm_medium": "social",
            "utm_campaign": "lancamento",
        },
    )
    assert campaign.status_code == 201
    campaign_id = campaign.json()["id"]

    for index in range(2):
        response = client.post(
            "/api/leads",
            headers=admin_headers,
            json=new_lead_payload(
                nome=f"Lead {index}", email=f"lead{index}@exemplo.com", campaign_id=campaign_id
            ),
        )
        assert response.status_code == 201

    assert client.post(
        "/api/leads", headers=admin_headers, json=new_lead_payload(campaign_id=99999)
    ).status_code == 404

    analytics = client.get("/api/marketing-analytics", headers=admin_headers)
    assert analytics.status_code == 200
    row = next(item for item in analytics.json() if item["campaign_id"] == campaign_id)
    assert row["campanha"] == "Lançamento"
    assert row["leads"] == 2
    assert row["convertidos"] == 0
    assert row["cpl"] == 100  # R$ 200 / 2 leads


def test_customer_analytics_and_dashboard_with_data(client, admin_headers, create_lead):
    create_lead()
    create_lead(
        nome="Pessoa B2C", email="b2c@exemplo.com", tipo_cliente="B2C", idade=30, cidade="Volta Redonda"
    )
    assert client.get("/api/customer-analytics", headers=admin_headers).status_code == 200
    dashboard = client.get("/api/dashboard/summary", headers=admin_headers)
    assert dashboard.status_code == 200


def test_omnichannel_summary_counts_by_channel(client, admin_headers, create_lead):
    lead = create_lead()
    for tipo in ("WhatsApp", "WhatsApp", "E-mail"):
        client.post(
            f"/api/leads/{lead['id']}/interactions",
            headers=admin_headers,
            json={"tipo": tipo, "descricao": "contato"},
        )
    summary = client.get("/api/omnichannel/summary", headers=admin_headers).json()
    by_channel = {item["canal"]: item["total"] for item in summary["por_canal"]}
    assert by_channel == {"WhatsApp": 2, "E-mail": 1}
    assert len(summary["recentes"]) == 3
