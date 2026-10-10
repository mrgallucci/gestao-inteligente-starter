"""Uploads administrativos e validação de entrada."""

import pytest

from tests.conftest import new_lead_payload

MAX_BYTES = 50 * 1024 * 1024


def test_admin_can_upload_allowed_file(client, admin_headers, upload_dir):
    response = client.post(
        "/api/course-contents/upload",
        headers=admin_headers,
        files={"file": ("Apostila CLARO.pdf", b"%PDF-1.4 conteudo")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "Apostila CLARO.pdf"
    assert body["stored_name"].endswith(".pdf")
    # O nome original nunca é usado no disco (evita path traversal e colisões).
    assert "Apostila" not in body["stored_name"]
    assert (upload_dir / body["stored_name"]).read_bytes() == b"%PDF-1.4 conteudo"
    assert body["url"].endswith(f"/{body['stored_name']}")


@pytest.mark.parametrize("filename", ["script.exe", "pagina.html", "imagem.svg", "x.php", "sem_extensao"])
def test_upload_rejects_disallowed_types(client, admin_headers, upload_dir, filename):
    response = client.post(
        "/api/course-contents/upload", headers=admin_headers, files={"file": (filename, b"x")}
    )
    assert response.status_code == 400
    assert list(upload_dir.iterdir()) == []


def test_upload_does_not_trust_path_in_filename(client, admin_headers, upload_dir):
    response = client.post(
        "/api/course-contents/upload",
        headers=admin_headers,
        files={"file": ("../../etc/passwd.pdf", b"%PDF")},
    )
    assert response.status_code == 201
    stored = list(upload_dir.iterdir())
    assert len(stored) == 1
    assert stored[0].parent == upload_dir


def test_upload_enforces_50mb_limit(client, admin_headers, upload_dir):
    exactly_limit = client.post(
        "/api/course-contents/upload",
        headers=admin_headers,
        files={"file": ("limite.pdf", b"0" * MAX_BYTES)},
    )
    assert exactly_limit.status_code == 201

    too_big = client.post(
        "/api/course-contents/upload",
        headers=admin_headers,
        files={"file": ("grande.pdf", b"0" * (MAX_BYTES + 1))},
    )
    assert too_big.status_code == 413


def test_upload_requires_authentication(client, upload_dir):
    response = client.post("/api/course-contents/upload", files={"file": ("a.pdf", b"x")})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Validação de entrada
# ---------------------------------------------------------------------------


def test_validation_errors_return_text_detail(client, admin_headers):
    """O frontend exibe `detail` direto na tela, então precisa ser string."""
    response = client.post("/api/products", headers=admin_headers, json={"nome": "", "preco": -5})
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)
    assert "nome" in response.json()["detail"]


@pytest.mark.parametrize(
    "payload",
    [
        {"nome": "Produto", "preco": -1},
        {"nome": "   ", "preco": 10},
        {"nome": "Produto", "preco": "abc"},
    ],
)
def test_product_validation(client, admin_headers, payload):
    assert client.post("/api/products", headers=admin_headers, json=payload).status_code == 422


def test_campaign_cost_cannot_be_negative(client, admin_headers):
    response = client.post(
        "/api/campaigns", headers=admin_headers, json={"nome": "C", "canal": "Instagram", "custo": -10}
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "overrides",
    [
        {"nome": ""},
        {"nome": "   "},
        {"tipo_cliente": "B2X"},
        {"email": "isto-nao-e-email"},
        {"idade": 500},
        {"idade": -1},
        {"tamanho_equipe": -3},
    ],
)
def test_lead_validation(client, admin_headers, overrides):
    response = client.post(
        "/api/leads", headers=admin_headers, json=new_lead_payload(**overrides)
    )
    assert response.status_code == 422, overrides


def test_lead_normalizes_blank_email_and_trims_names(client, admin_headers):
    response = client.post(
        "/api/leads",
        headers=admin_headers,
        json=new_lead_payload(nome="  Maria  ", email="   "),
    )
    assert response.status_code == 201
    assert response.json()["nome"] == "Maria"
    assert response.json()["email"] is None


def test_interaction_requires_type_and_description(client, admin_headers, create_lead):
    lead = create_lead()
    for payload in ({"tipo": "", "descricao": "x"}, {"tipo": "WhatsApp", "descricao": "  "}):
        response = client.post(
            f"/api/leads/{lead['id']}/interactions", headers=admin_headers, json=payload
        )
        assert response.status_code == 422


@pytest.mark.parametrize(
    "url",
    ["javascript:alert(1)", "data:text/html,<script>1</script>", "ftp://exemplo.com/a", "exemplo.com/a"],
)
def test_content_url_must_be_http(client, admin_headers, course_setup, url):
    response = client.post(
        f"/api/courses/{course_setup['course_id']}/contents",
        headers=admin_headers,
        json={"titulo": "Link", "tipo": "material", "ordem": 5, "url_conteudo": url},
    )
    assert response.status_code == 422


def test_content_accepts_http_and_https_urls(client, admin_headers, course_setup):
    for ordem, url in ((5, "https://exemplo.com/a.pdf"), (6, "http://127.0.0.1:8000/uploads/a.pdf")):
        response = client.post(
            f"/api/courses/{course_setup['course_id']}/contents",
            headers=admin_headers,
            json={"titulo": f"Link {ordem}", "tipo": "material", "ordem": ordem, "url_conteudo": url},
        )
        assert response.status_code == 201, response.text
        assert response.json()["url_conteudo"] == url


def test_sql_injection_like_input_is_stored_as_plain_text(client, admin_headers):
    nome = "Robert'); DROP TABLE leads;--"
    created = client.post("/api/leads", headers=admin_headers, json=new_lead_payload(nome=nome))
    assert created.status_code == 201
    assert created.json()["nome"] == nome
    assert client.get("/api/leads", headers=admin_headers).status_code == 200
