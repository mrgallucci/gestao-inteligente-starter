"""2.1.0-rc.1 — automação de e-mail pós e-book (provedor sempre simulado)."""

import pytest

import email_service
from models import EmailLog

PAYLOAD = {"nome": "Ana Lima", "email": "ana@exemplo.com", "whatsapp": "(24) 99999-0000", "consentimento": True}


class FakeProvider:
    name = "fake"

    def __init__(self, fail: bool = False):
        self.fail = fail
        self.sent = []

    def send(self, message):
        if self.fail:
            raise ConnectionError("provedor fora do ar")
        self.sent.append(message)


@pytest.fixture()
def email_env(monkeypatch):
    for name in (
        "EMAIL_AUTOMATION_ENABLED", "EMAIL_PROVIDER", "EMAIL_FROM_ADDRESS", "EMAIL_FROM_NAME",
        "EMAIL_REPLY_TO", "EBOOK_DELIVERY_URL", "PAID_PRODUCT_URL", "EMAIL_COMMERCIAL_ENABLED", "SMTP_HOST",
    ):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


@pytest.fixture()
def provider(email_env):
    fake = FakeProvider()
    email_env.setattr(email_service, "build_provider", lambda settings: fake)
    return fake


def _enable(monkeypatch, **extra):
    monkeypatch.setenv("EMAIL_AUTOMATION_ENABLED", "true")
    monkeypatch.setenv("EMAIL_FROM_ADDRESS", "contato@exemplo.test")
    monkeypatch.setenv("EMAIL_FROM_NAME", "Equipe Teste")
    for key, value in extra.items():
        monkeypatch.setenv(key, value)


def _logs():
    from database import SessionLocal

    with SessionLocal() as db:
        return [(r.status, r.template, r.detalhe) for r in db.query(EmailLog).order_by(EmailLog.id)]


def _lead_id(client, admin_headers, email):
    """A resposta pública não traz id (anti-enumeração): busca o Lead pelo CRM."""
    leads = client.get("/api/leads", headers=admin_headers).json()
    return next(lead["id"] for lead in leads if (lead["email"] or "").lower() == email.lower())


def _interactions(client, admin_headers, lead_id):
    response = client.get(f"/api/leads/{lead_id}/interactions", headers=admin_headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_default_is_disabled_nothing_sent_or_logged(client, provider):
    response = client.post("/api/public/leads/ebook", json=PAYLOAD)
    assert response.status_code == 201
    assert provider.sent == []
    assert _logs() == []


def test_enabled_sends_delivery_and_registers_interaction(client, admin_headers, provider, email_env):
    _enable(email_env, EBOOK_DELIVERY_URL="https://exemplo.test/ebook.pdf")
    response = client.post("/api/public/leads/ebook", json=PAYLOAD)
    assert response.status_code == 201

    assert len(provider.sent) == 1
    message = provider.sent[0]
    assert message["To"] == "ana@exemplo.com"
    body = message.get_body(preferencelist=("plain",)).get_content()
    html = message.get_body(preferencelist=("html",)).get_content()
    assert message["Subject"] == "Seu acesso ao e-book SargLab"
    assert "https://exemplo.test/ebook.pdf" in body
    assert "Acessar e-book" in html
    assert "SargLab — IA para quem tem trabalho pra fazer" in html
    assert _logs() == [("enviado", "entrega_material", None)]

    interactions = _interactions(client, admin_headers, _lead_id(client, admin_headers, PAYLOAD["email"]))
    tipos = [i["tipo"] for i in interactions]
    assert tipos.count("Download e-book") == 1
    assert tipos.count("E-mail automático") == 1


def test_no_commercial_link_without_paid_product_url(client, provider, email_env):
    _enable(email_env, EMAIL_COMMERCIAL_ENABLED="true")  # flag ligada, mas SEM URL
    client.post("/api/public/leads/ebook", json=PAYLOAD)
    body = provider.sent[0].get_body(preferencelist=("plain",)).get_content()
    assert "http" not in body


def test_commercial_cta_needs_flag_and_url(client, provider, email_env):
    _enable(email_env, PAID_PRODUCT_URL="https://loja.exemplo.test/produto")
    client.post("/api/public/leads/ebook", json=PAYLOAD)  # URL sem flag comercial
    assert "loja.exemplo.test" not in provider.sent[0].get_body(preferencelist=("plain",)).get_content()

    email_env.setenv("EMAIL_COMMERCIAL_ENABLED", "true")
    client.post("/api/public/leads/ebook", json={**PAYLOAD, "email": "bia@exemplo.com"})
    assert "loja.exemplo.test" in provider.sent[1].get_body(preferencelist=("plain",)).get_content()


def test_invalid_paid_url_is_discarded(email_env):
    email_env.setenv("PAID_PRODUCT_URL", "javascript:alert(1)")
    email_env.setenv("EMAIL_COMMERCIAL_ENABLED", "true")
    assert email_service.load_settings().paid_product_url is None
    assert email_service.load_settings().commercial_cta_active is False


def test_provider_failure_never_blocks_lead_and_is_logged(client, admin_headers, email_env):
    _enable(email_env)
    email_env.setattr(email_service, "build_provider", lambda settings: FakeProvider(fail=True))
    response = client.post("/api/public/leads/ebook", json=PAYLOAD)
    assert response.status_code == 201

    leads = client.get("/api/leads", headers=admin_headers).json()
    assert any(lead["email"] == "ana@exemplo.com" for lead in leads)
    status, template, detail = _logs()[0]
    assert (status, template) == ("falha", "entrega_material")
    assert "provedor fora do ar" in detail
    assert [i["tipo"] for i in _interactions(client, admin_headers, _lead_id(client, admin_headers, PAYLOAD["email"]))] == ["Download e-book"]


def test_missing_sender_logs_failure_without_sending(client, provider, email_env):
    email_env.setenv("EMAIL_AUTOMATION_ENABLED", "true")  # sem EMAIL_FROM_ADDRESS
    assert client.post("/api/public/leads/ebook", json=PAYLOAD).status_code == 201
    assert provider.sent == []
    assert _logs()[0][0] == "falha"


def test_reply_to_can_point_to_commercial_inbox(client, provider, email_env):
    _enable(email_env)
    email_env.setenv("EMAIL_REPLY_TO", "SARGrowth@proton.me")
    assert client.post("/api/public/leads/ebook", json=PAYLOAD).status_code == 201
    assert provider.sent[0]["Reply-To"] == "SARGrowth@proton.me"


def test_without_consent_nothing_is_sent(provider, email_env):
    _enable(email_env)
    result = email_service.send_template(
        template=email_service.TEMPLATE_DELIVERY,
        nome="Caio", email="caio@exemplo.com", consentimento=False,
    )
    assert result.status == "ignorado"
    assert provider.sent == []


def test_commercial_template_is_inert_until_flag_and_url(provider, email_env):
    _enable(email_env)
    result = email_service.send_template(
        template=email_service.TEMPLATE_COMMERCIAL, nome="Caio", email="c@exemplo.com", consentimento=True
    )
    assert result.status == "ignorado"
    assert provider.sent == []

    email_env.setenv("EMAIL_COMMERCIAL_ENABLED", "true")
    email_env.setenv("PAID_PRODUCT_URL", "https://loja.exemplo.test/p")
    ok = email_service.send_template(
        template=email_service.TEMPLATE_COMMERCIAL, nome="Caio", email="c@exemplo.com", consentimento=True
    )
    assert ok.status == "enviado"


def test_html_template_escapes_name(email_env):
    _, _, html = email_service.render_template(email_service.TEMPLATE_DELIVERY, nome="<script>x</script> Zé")
    assert "<script>" not in html


def test_error_text_hides_smtp_secrets(email_env):
    email_env.setenv("SMTP_PASSWORD", "segredo-super")
    settings = email_service.load_settings()
    text = email_service._safe_error(RuntimeError("login falhou com segredo-super"), settings)
    assert "segredo-super" not in text


def test_email_logs_endpoint_is_admin_only(client, admin_headers, make_user):
    assert client.get("/api/email-logs", headers=admin_headers).status_code == 200
    seller, _ = make_user("vendedor", "v@exemplo.com")
    assert client.get("/api/email-logs", headers=seller).status_code == 403
    assert client.get("/api/email-logs").status_code in (401, 403)


def _lead_count(email):
    from database import SessionLocal
    from models import Lead
    from sqlalchemy import func

    with SessionLocal() as db:
        return db.query(Lead).filter(func.lower(Lead.email) == email).count()


def test_repeat_download_reuses_lead_registers_interaction_and_sends_again(
    client, admin_headers, provider, email_env
):
    _enable(email_env)
    first = client.post("/api/public/leads/ebook", json=PAYLOAD)
    assert first.status_code == 201
    lead_id = _lead_id(client, admin_headers, PAYLOAD["email"])

    again = client.post("/api/public/leads/ebook", json={**PAYLOAD, "email": "ANA@exemplo.com"})
    assert again.status_code == 201
    assert "id" not in again.json() and "status" not in again.json()  # sem expor o Lead existente
    assert _lead_count("ana@exemplo.com") == 1

    tipos = [i["tipo"] for i in _interactions(client, admin_headers, lead_id)]
    assert tipos.count("Download e-book") == 2
    assert tipos.count("E-mail automático") == 2
    assert len(provider.sent) == 2


def test_repeat_download_with_automation_off_still_works_and_registers(client, admin_headers, provider):
    client.post("/api/public/leads/ebook", json=PAYLOAD)
    lead_id = _lead_id(client, admin_headers, PAYLOAD["email"])
    assert client.post("/api/public/leads/ebook", json=PAYLOAD).status_code == 201
    assert provider.sent == []
    assert [i["tipo"] for i in _interactions(client, admin_headers, lead_id)] == ["Download e-book", "Download e-book"]


def test_repeat_download_of_crm_lead_without_consent_records_consent_and_sends(
    client, admin_headers, create_lead, provider, email_env
):
    _enable(email_env)
    lead = create_lead(nome="Rui", email="rui@exemplo.com", consentimento_contato=False)
    response = client.post(
        "/api/public/leads/ebook", json={"nome": "Rui", "email": "rui@exemplo.com", "whatsapp": "(24) 99999-0000", "consentimento": True}
    )
    assert response.status_code == 201
    assert _lead_count("rui@exemplo.com") == 1
    assert len(provider.sent) == 1
    detail = client.get(f"/api/leads/{lead['id']}", headers=admin_headers).json()
    assert detail["consentimento_contato"] is True


def test_repeat_download_still_requires_consent(client, create_lead):
    create_lead(nome="Rui", email="rui@exemplo.com")
    response = client.post(
        "/api/public/leads/ebook", json={"nome": "Rui", "email": "rui@exemplo.com", "whatsapp": "(24) 99999-0000", "consentimento": False}
    )
    assert response.status_code == 400


def test_commercial_cta_is_blocked_in_production(email_env):
    email_env.setenv("APP_ENV", "production")
    email_env.setenv("EMAIL_COMMERCIAL_ENABLED", "true")
    email_env.setenv("PAID_PRODUCT_URL", "https://loja.exemplo.test/p")
    settings = email_service.load_settings()
    assert settings.commercial_cta_active is False
    assert settings.commercial_blocked_in_production is True
    _, text, _ = email_service.render_template(
        email_service.TEMPLATE_DELIVERY, nome="A", include_commercial_cta=settings.commercial_cta_active,
        paid_product_url=settings.paid_product_url,
    )
    assert "loja.exemplo.test" not in text


GENERIC = {"mensagem": "Solicitação registrada com sucesso. Verifique seu e-mail."}


def test_public_response_is_identical_for_new_and_existing_email(client, admin_headers, provider, email_env):
    """Anti-enumeração: mesmo HTTP e mesmo corpo para e-mail novo e já existente."""
    _enable(email_env)
    novo = client.post("/api/public/leads/ebook", json=PAYLOAD)
    existente = client.post("/api/public/leads/ebook", json=PAYLOAD)
    assert novo.status_code == existente.status_code == 201
    assert novo.json() == existente.json() == GENERIC
    assert novo.content == existente.content  # byte a byte

    # Contato que já existia no CRM (cadastrado pelo painel), com outro nome na requisição.
    email_env.setattr(email_service, "build_provider", lambda settings: provider)
    client.post("/api/leads", headers=admin_headers, json={
        "nome": "Cadastrado no CRM", "origem": "Instagram", "objetivo": "x", "interesse": "Alto",
        "email": "crm@exemplo.com", "consentimento_contato": True,
    })
    crm = client.post("/api/public/leads/ebook", json={"nome": "Outro Nome", "email": "crm@exemplo.com", "whatsapp": "(24) 99999-0000", "consentimento": True})
    assert crm.status_code == 201 and crm.content == novo.content

    corpo = novo.json()
    for proibido in ("id", "status", "nome", "email", "created", "reused", "existente", "criado"):
        assert proibido not in corpo


def test_uniform_response_does_not_change_internal_behaviour(client, admin_headers, provider, email_env):
    _enable(email_env)
    client.post("/api/public/leads/ebook", json=PAYLOAD)
    client.post("/api/public/leads/ebook", json=PAYLOAD)

    assert _lead_count("ana@exemplo.com") == 1  # sem duplicata
    lead_id = _lead_id(client, admin_headers, "ana@exemplo.com")
    tipos = [i["tipo"] for i in _interactions(client, admin_headers, lead_id)]
    assert tipos.count("Download e-book") == 2  # primeiro download + novo download
    assert tipos.count("E-mail automático") == 2  # automação segue funcionando nos dois
    assert len(provider.sent) == 2
    detail = client.get(f"/api/leads/{lead_id}", headers=admin_headers).json()
    assert detail["consentimento_contato"] is True


def test_provider_failure_does_not_break_uniform_response_for_existing_lead(client, admin_headers, email_env):
    _enable(email_env)
    email_env.setattr(email_service, "build_provider", lambda settings: FakeProvider(fail=True))
    novo = client.post("/api/public/leads/ebook", json=PAYLOAD)
    existente = client.post("/api/public/leads/ebook", json=PAYLOAD)
    assert novo.status_code == existente.status_code == 201
    assert novo.json() == existente.json() == GENERIC
    assert _lead_count("ana@exemplo.com") == 1
    assert [status for status, _, _ in _logs()] == ["falha", "falha"]  # logs preservados


def test_uniform_response_still_requires_consent_for_both_cases(client, create_lead):
    create_lead(nome="Rui", email="rui@exemplo.com")
    sem = {"nome": "X", "whatsapp": "(24) 99999-0000", "consentimento": False}
    novo = client.post("/api/public/leads/ebook", json={**sem, "email": "novo@exemplo.com"})
    existente = client.post("/api/public/leads/ebook", json={**sem, "email": "rui@exemplo.com"})
    assert novo.status_code == existente.status_code == 400
    assert novo.json() == existente.json()


# SargLab — Edição Instagram: contrato de entrega independente do e-book original.
def test_instagram_ebook_delivery_uses_own_title_and_pdf(client, provider, email_env):
    _enable(email_env, EBOOK_DELIVERY_URL="https://exemplo.test/ebook-original.pdf")
    email_env.setenv("EBOOK_INSTAGRAM_DELIVERY_URL", "https://exemplo.test/instagram-sob-analise.pdf")
    response = client.post("/api/public/leads/ebook/instagram", json=PAYLOAD)
    assert response.status_code == 201
    assert len(provider.sent) == 1
    msg = provider.sent[0]
    assert "Instagram sob análise" in msg["Subject"]
    body = msg.get_body(preferencelist=("plain",)).get_content()
    assert "https://exemplo.test/instagram-sob-analise.pdf" in body
    assert "ebook-original.pdf" not in body
    assert _logs() == [("enviado", "entrega_instagram", None)]


def test_original_and_instagram_share_lead_but_deliver_different_material(client, provider, email_env):
    _enable(email_env, EBOOK_DELIVERY_URL="https://exemplo.test/original.pdf")
    email_env.setenv("EBOOK_INSTAGRAM_DELIVERY_URL", "https://exemplo.test/instagram.pdf")
    r1 = client.post("/api/public/leads/ebook", json=PAYLOAD)
    r2 = client.post("/api/public/leads/ebook/instagram", json=PAYLOAD)
    assert r1.status_code == 201 and r2.status_code == 201
    assert r1.json() == r2.json()
    assert _lead_count(PAYLOAD["email"]) == 1
    assert len(provider.sent) == 2
    text1 = provider.sent[0].get_body(preferencelist=("plain",)).get_content()
    text2 = provider.sent[1].get_body(preferencelist=("plain",)).get_content()
    assert "original.pdf" in text1 and "instagram.pdf" not in text1
    assert "instagram.pdf" in text2 and "original.pdf" not in text2
    assert [(status, template) for status, template, _ in _logs()] == [
        ("enviado", "entrega_material"), ("enviado", "entrega_instagram")
    ]
