"""Atribuição de campanha (UTM), endpoint de contato do site, limite de requisições e CORS do cutover."""

import pytest

import main

ATTR = {
    "utm_source": "instagram",
    "utm_medium": "bio",
    "utm_campaign": "ebook-out",
    "utm_content": "post1",
    "utm_term": "ia",
    "referrer": "https://l.instagram.com/",
    "landing_url": "https://sargtech.com.br/sarglab/ebook/?utm_source=instagram&utm_medium=bio",
    "pagina": "/sarglab/ebook/",
    "consentimento_versao": "landing-2026-10-07",
}
EBOOK = {"nome": "Ana Lima", "email": "ana@exemplo.com", "area_profissional": "vendas", "consentimento": True}
CONTACT = {
    "nome": "Caio Dias",
    "email": "caio@empresa.com",
    "empresa": "Empresa SA",
    "assunto": "CRM e gestão comercial",
    "mensagem": "Quero organizar o funil comercial da equipe.",
    "consentimento": True,
}


def _lead(client, headers, email):
    leads = client.get("/api/leads", headers=headers).json()
    return next(lead for lead in leads if (lead["email"] or "").lower() == email.lower())


def _touchpoints(client, headers, lead_id):
    response = client.get(f"/api/leads/{lead_id}/touchpoints", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture(autouse=True)
def limiter_off(monkeypatch):
    monkeypatch.delenv("PUBLIC_RATE_LIMIT_PER_MIN", raising=False)
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    main.PUBLIC_RATE_LIMITER.reset()


# ---------------------------------------------------------------- e-book + atribuição


def test_ebook_persists_every_attribution_field(client, admin_headers):
    response = client.post("/api/public/leads/ebook", json={**EBOOK, "origem": "instagram", **ATTR})
    assert response.status_code == 201
    lead = _lead(client, admin_headers, "ana@exemplo.com")
    assert lead["origem"] == "instagram"  # comportamento da landing atual preservado
    [tp] = _touchpoints(client, admin_headers, lead["id"])
    for campo, valor in ATTR.items():
        if campo != "consentimento_versao":
            assert tp[campo] == valor, campo
    assert tp["canal"] == "ebook"


def test_ebook_without_attribution_still_works(client, admin_headers):
    """Contrato antigo (landing GitHub Pages): sem campos novos, nada quebra."""
    assert client.post("/api/public/leads/ebook", json=EBOOK).status_code == 201
    lead = _lead(client, admin_headers, "ana@exemplo.com")
    [tp] = _touchpoints(client, admin_headers, lead["id"])
    assert tp["utm_source"] is None and tp["landing_url"] is None


def test_second_download_keeps_first_touch_and_does_not_duplicate_lead(client, admin_headers):
    client.post("/api/public/leads/ebook", json={**EBOOK, **ATTR})
    client.post("/api/public/leads/ebook", json={**EBOOK, "utm_source": "linkedin", "utm_campaign": "outra"})
    leads = [l for l in client.get("/api/leads", headers=admin_headers).json() if l["email"] == "ana@exemplo.com"]
    assert len(leads) == 1
    tps = _touchpoints(client, admin_headers, leads[0]["id"])
    assert [t["utm_source"] for t in tps] == ["instagram", "linkedin"]


def test_oversized_attribution_is_truncated_not_rejected(client, admin_headers):
    long = "x" * 5000
    response = client.post("/api/public/leads/ebook", json={**EBOOK, "referrer": long, "landing_url": long, "utm_campaign": long})
    assert response.status_code == 201
    [tp] = _touchpoints(client, admin_headers, _lead(client, admin_headers, "ana@exemplo.com")["id"])
    assert len(tp["referrer"]) == 500 and len(tp["landing_url"]) == 500 and len(tp["utm_campaign"]) == 180


def test_matching_campaign_is_linked_to_the_lead(client, admin_headers):
    campanha = client.post(
        "/api/campaigns",
        headers=admin_headers,
        json={"nome": "E-book outubro", "canal": "Instagram", "utm_source": "Instagram", "utm_campaign": "Ebook-Out"},
    )
    assert campanha.status_code == 201, campanha.text
    client.post("/api/public/leads/ebook", json={**EBOOK, **ATTR})
    lead = _lead(client, admin_headers, "ana@exemplo.com")
    assert lead["campaign_id"] == campanha.json()["id"]
    assert _touchpoints(client, admin_headers, lead["id"])[0]["campaign_id"] == campanha.json()["id"]


def test_campaign_with_different_source_is_not_linked(client, admin_headers):
    client.post("/api/campaigns", headers=admin_headers, json={"nome": "X", "canal": "Google", "utm_source": "google", "utm_campaign": "ebook-out"})
    client.post("/api/public/leads/ebook", json={**EBOOK, **ATTR})
    assert _lead(client, admin_headers, "ana@exemplo.com")["campaign_id"] is None


# ---------------------------------------------------------------- contato institucional


def test_contact_creates_identifiable_lead_with_message_and_attribution(client, admin_headers):
    response = client.post("/api/public/leads/contact", json={**CONTACT, **ATTR, "origem": "site-contato", "pagina": "/contato/"})
    assert response.status_code == 201
    assert "id" not in response.json()
    lead = _lead(client, admin_headers, "caio@empresa.com")
    assert lead["origem"] == "site-contato"
    assert lead["tipo_cliente"] == "B2B" and lead["empresa"] == "Empresa SA"
    assert lead["consentimento_contato"] is True
    interacoes = client.get(f"/api/leads/{lead['id']}/interactions", headers=admin_headers).json()
    assert any("funil comercial" in i["descricao"] and i["tipo"] == "Contato pelo site" for i in interacoes)
    [tp] = _touchpoints(client, admin_headers, lead["id"])
    assert tp["canal"] == "contato" and tp["utm_source"] == "instagram"


def test_contact_is_a_separate_endpoint_from_ebook(client, admin_headers):
    client.post("/api/public/leads/contact", json=CONTACT)
    lead = _lead(client, admin_headers, "caio@empresa.com")
    assert lead["formato_interesse"] != "E-book"
    assert lead["origem"] != "direto"


def test_waitlist_origin_is_mapped_and_unknown_origin_falls_back(client, admin_headers):
    client.post("/api/public/leads/contact", json={**CONTACT, "email": "a@x.com", "origem": "sarglab-cursos-aviso", "interesse": "sarglab-completo"})
    client.post("/api/public/leads/contact", json={**CONTACT, "email": "b@x.com", "origem": "<script>"})
    assert _lead(client, admin_headers, "a@x.com")["origem"] == "site-sarglab-aviso"
    assert _lead(client, admin_headers, "a@x.com")["oferta_interesse"] == "sarglab-completo"
    assert _lead(client, admin_headers, "b@x.com")["origem"] == "site-contato"


def test_contact_existing_email_reuses_lead_and_adds_interaction(client, admin_headers, create_lead):
    create_lead(nome="Caio", email="caio@empresa.com", origem="Indicação")
    first = client.post("/api/public/leads/contact", json=CONTACT)
    assert first.status_code == 201
    leads = [l for l in client.get("/api/leads", headers=admin_headers).json() if l["email"] == "caio@empresa.com"]
    assert len(leads) == 1 and leads[0]["origem"] == "Indicação"
    interacoes = client.get(f"/api/leads/{leads[0]['id']}/interactions", headers=admin_headers).json()
    assert any(i["tipo"] == "Contato pelo site" for i in interacoes)


@pytest.mark.parametrize(
    "mudanca",
    [
        {"consentimento": False},
        {"mensagem": "curta"},
        {"email": "sem-arroba"},
        {"nome": "   "},
        {"assunto": ""},
        {"mensagem": "x" * 2501},
    ],
)
def test_contact_validation_rejects_bad_input(client, mudanca):
    assert client.post("/api/public/leads/contact", json={**CONTACT, **mudanca}).status_code in (400, 422)


# ---------------------------------------------------------------- leitura / RBAC


def test_attribution_report_aggregates_and_is_admin_only(client, admin_headers, make_user, create_lead):
    client.post("/api/public/leads/ebook", json={**EBOOK, **ATTR})
    client.post("/api/public/leads/ebook", json={**EBOOK, **ATTR})  # mesmo Lead, 2 envios
    client.post("/api/public/leads/ebook", json={**EBOOK, "email": "b@x.com", **ATTR})
    client.post("/api/public/leads/contact", json=CONTACT)
    response = client.get("/api/marketing-analytics/attribution", headers=admin_headers)
    assert response.status_code == 200
    itens = {(i["canal"], i["utm_source"]): i for i in response.json()["itens"]}
    assert itens[("ebook", "instagram")]["envios"] == 3
    assert itens[("ebook", "instagram")]["leads"] == 2
    assert itens[("contato", "(não informado)")]["envios"] == 1

    vendedor, _ = make_user("vendedor", "v@teste.local")
    lead = create_lead()
    aluno, _ = make_user("aluno", "a@teste.local", lead_id=lead["id"])
    assert client.get("/api/marketing-analytics/attribution").status_code == 401
    assert client.get("/api/marketing-analytics/attribution", headers=vendedor).status_code == 403
    assert client.get("/api/marketing-analytics/attribution", headers=aluno).status_code == 403


def test_touchpoints_are_staff_only_and_404_for_unknown_lead(client, admin_headers, make_user, create_lead):
    lead = create_lead()
    vendedor, _ = make_user("vendedor", "v@teste.local")
    aluno, _ = make_user("aluno", "a@teste.local", lead_id=lead["id"])
    assert client.get(f"/api/leads/{lead['id']}/touchpoints").status_code == 401
    assert client.get(f"/api/leads/{lead['id']}/touchpoints", headers=vendedor).status_code == 200
    assert client.get(f"/api/leads/{lead['id']}/touchpoints", headers=aluno).status_code == 403
    assert client.get("/api/leads/999999/touchpoints", headers=admin_headers).status_code == 404


# ---------------------------------------------------------------- limite de requisições


def test_rate_limit_is_off_by_default(client):
    for i in range(30):
        assert client.post("/api/public/leads/contact", json={**CONTACT, "email": f"u{i}@x.com"}).status_code == 201


def test_rate_limit_blocks_after_threshold_per_endpoint(client, monkeypatch):
    monkeypatch.setenv("PUBLIC_RATE_LIMIT_PER_MIN", "2")
    codes = [client.post("/api/public/leads/contact", json={**CONTACT, "email": f"u{i}@x.com"}).status_code for i in range(3)]
    assert codes == [201, 201, 429]
    # o e-book tem a sua própria cota
    assert client.post("/api/public/leads/ebook", json=EBOOK).status_code == 201


def test_rate_limiter_window_expires():
    limiter = main.SlidingWindowLimiter()
    assert limiter.allow("k", 1, 60, now=0) is True
    assert limiter.allow("k", 1, 60, now=10) is False
    assert limiter.allow("k", 1, 60, now=61) is True


def test_client_ip_only_trusts_forwarded_header_when_enabled(monkeypatch):
    class Req:
        headers = {"x-forwarded-for": "9.9.9.9, 203.0.113.7"}
        client = type("C", (), {"host": "10.0.0.1"})()

    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    assert main._client_ip(Req()) == "10.0.0.1"
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "true")
    assert main._client_ip(Req()) == "203.0.113.7"


# ---------------------------------------------------------------- CORS do cutover


def test_cors_accepts_site_domain_and_keeps_github_pages(monkeypatch):
    monkeypatch.setattr(main, "IS_PRODUCTION", True)
    monkeypatch.setattr(main, "FRONTEND_URL", "https://crm.sargtech.com.br")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://sargtech.com.br,https://www.sargtech.com.br,https://mrgallucci.github.io",
    )
    origens = main._build_cors_origins()
    for esperado in ("https://sargtech.com.br", "https://www.sargtech.com.br", "https://mrgallucci.github.io", "https://crm.sargtech.com.br"):
        assert esperado in origens
