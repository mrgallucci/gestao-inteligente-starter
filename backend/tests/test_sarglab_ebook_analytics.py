"""Analytics administrativo dos dois guias SargLab, com foco em atribuição real."""
import email_service

A = {
    "nome": "Ana Lima", "email": "ana@exemplo.com",
    "whatsapp": "(24) 99999-0000", "consentimento": True,
    "area_profissional": "vendas",
}
B = {**A, "nome": "Bia", "email": "bia@exemplo.com"}


def test_analytics_vazio_e_parametros(client, admin_headers):
    r = client.get("/api/sarglab/ebooks/analytics", headers=admin_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["produto"] == "instagram"
    assert data["resumo"]["solicitacoes"] == 0
    assert data["resumo"]["leads_unicos"] == 0
    assert data["emails"]["envios_smtp"] == 0
    assert data["por_dia"] == [] and data["recentes"] == []
    assert client.get("/api/sarglab/ebooks/analytics?produto=errado", headers=admin_headers).status_code == 400
    assert client.get("/api/sarglab/ebooks/analytics?dias=9999", headers=admin_headers).status_code == 400


def test_analytics_isola_ebooks_e_deduplica_por_lead(client, admin_headers, monkeypatch):
    class Fake:
        name = "fake"
        def send(self, message):
            pass

    monkeypatch.setenv("EMAIL_AUTOMATION_ENABLED", "true")
    monkeypatch.setenv("EMAIL_FROM_ADDRESS", "teste@exemplo.test")
    monkeypatch.setenv("EMAIL_PROVIDER", "console")
    monkeypatch.setattr(email_service, "build_provider", lambda settings: Fake())

    base = "/api/public/leads/ebook"
    assert client.post(base + "/instagram", json={**A, "utm_source": "instagram", "utm_campaign": "story"}).status_code == 201
    assert client.post(base + "/instagram", json={**A, "utm_source": "instagram", "utm_campaign": "story"}).status_code == 201
    assert client.post(base + "/instagram", json={**B, "utm_source": "facebook", "utm_campaign": "feed"}).status_code == 201
    assert client.post(base, json={**A, "utm_source": "linkedin", "utm_campaign": "primeiro"}).status_code == 201

    def get(produto):
        r = client.get("/api/sarglab/ebooks/analytics?produto=" + produto + "&dias=0", headers=admin_headers)
        assert r.status_code == 200, r.text
        return r.json()

    instagram = get("instagram")
    assert instagram["resumo"]["solicitacoes"] == 3
    assert instagram["resumo"]["leads_unicos"] == 2
    assert instagram["resumo"]["solicitacoes_adicionais"] == 1
    assert instagram["emails"]["envios_smtp"] == 3
    assert instagram["emails"]["total_registros"] == 3
    por_origem = {x["origem"]: x for x in instagram["por_origem"]}
    assert por_origem["instagram"] == {"origem": "instagram", "solicitacoes": 2, "leads_unicos": 1}
    assert por_origem["facebook"]["solicitacoes"] == 1
    assert sum(x["solicitacoes"] for x in instagram["por_campanha"]) == 3
    assert len(instagram["recentes"]) == 3
    assert {x["produto"] for x in instagram["recentes"]} == {"instagram"}
    assert all("lead_id" in x for x in instagram["recentes"])

    first = get("primeiro")
    assert first["resumo"]["solicitacoes"] == 1
    assert first["resumo"]["leads_unicos"] == 1
    assert first["emails"]["envios_smtp"] == 1

    all_data = get("todos")
    assert all_data["resumo"]["solicitacoes"] == 4
    assert all_data["resumo"]["leads_unicos"] == 2
    assert all_data["resumo"]["solicitacoes_adicionais"] == 2
    assert all_data["emails"]["envios_smtp"] == 4
    assert sum(x["solicitacoes"] for x in all_data["por_dia"]) == 4


def test_analytics_protegido_por_perfil(client, admin_headers, make_user, create_lead):
    assert client.get("/api/sarglab/ebooks/analytics").status_code == 401
    seller, _ = make_user("vendedor", "vendedor@example.org")
    alumno_lead = create_lead(email="aluno-lead@exemplo.com")
    student, _ = make_user("aluno", "aluno@example.org", lead_id=alumno_lead["id"])
    assert client.get("/api/sarglab/ebooks/analytics", headers=seller).status_code == 403
    assert client.get("/api/sarglab/ebooks/analytics", headers=student).status_code == 403
    assert client.get("/api/sarglab/ebooks/analytics", headers=admin_headers).status_code == 200
