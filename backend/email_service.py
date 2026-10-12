"""Camada de e-mail desacoplada de fornecedor (2.1.0-rc.1).

Princípios:
- Desligada por padrão (`EMAIL_AUTOMATION_ENABLED=false`).
- Nenhuma chave, remetente ou URL no código: tudo vem de variáveis de ambiente.
- Falha do provedor NUNCA propaga: o chamador recebe um `SendResult`.
- O fornecedor é uma implementação de `EmailProvider`. Hoje existem `smtp` (stdlib,
  funciona com qualquer provedor que ofereça SMTP) e `console` (só registra em log,
  para homologação sem enviar nada). Trocar para uma API específica é adicionar uma
  classe e uma linha em `build_provider`.
- Sem `PAID_PRODUCT_URL` válida (http/https) não existe CTA comercial: nenhum link
  fictício é gerado.
"""

from __future__ import annotations

import logging
import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from typing import Protocol

logger = logging.getLogger("gestao_inteligente.email")

TEMPLATE_DELIVERY = "entrega_material"
TEMPLATE_COMMERCIAL = "convite_comercial"


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


def _env_str(name: str) -> str:
    return os.getenv(name, "").strip()


def _valid_http_url(value: str) -> str | None:
    value = value.strip()
    if value.lower().startswith(("http://", "https://")) and " " not in value and len(value) <= 2000:
        return value
    return None


@dataclass(frozen=True)
class EmailSettings:
    enabled: bool
    provider: str
    from_address: str
    from_name: str
    delivery_url: str | None
    paid_product_url: str | None
    commercial_enabled: bool
    commercial_blocked_in_production: bool
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_starttls: bool

    @property
    def commercial_cta_active(self) -> bool:
        """CTA comercial só existe com flag ligada, URL real válida e fora de produção
        (enquanto não houver mecanismo de descadastro)."""
        return self.commercial_enabled and self.paid_product_url is not None


def load_settings() -> EmailSettings:
    """Lê o ambiente a cada chamada (permite testes e troca sem reimportar)."""
    try:
        port = int(_env_str("SMTP_PORT") or "587")
    except ValueError:
        port = 587
    is_production = _env_str("APP_ENV").lower() == "production"
    commercial_requested = _env_bool("EMAIL_COMMERCIAL_ENABLED", False)
    if commercial_requested and is_production:
        # Sem mecanismo de descadastro adequado, comunicação comercial é BLOQUEADA em
        # produção, mesmo com a flag ligada (decisão da gerência, 2.1.0-rc.1).
        logger.warning("EMAIL_COMMERCIAL_ENABLED ignorado em produção: descadastro ainda não implementado.")
    return EmailSettings(
        enabled=_env_bool("EMAIL_AUTOMATION_ENABLED", False),
        provider=(_env_str("EMAIL_PROVIDER") or "console").lower(),
        from_address=_env_str("EMAIL_FROM_ADDRESS"),
        from_name=_env_str("EMAIL_FROM_NAME"),
        delivery_url=_valid_http_url(_env_str("EBOOK_DELIVERY_URL")),
        paid_product_url=_valid_http_url(_env_str("PAID_PRODUCT_URL")),
        commercial_enabled=commercial_requested and not is_production,
        commercial_blocked_in_production=commercial_requested and is_production,
        smtp_host=_env_str("SMTP_HOST"),
        smtp_port=port,
        smtp_user=_env_str("SMTP_USER"),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_starttls=_env_bool("SMTP_STARTTLS", True),
    )


# ---------------------------------------------------------------------------
# Provedores
# ---------------------------------------------------------------------------


class EmailProvider(Protocol):
    name: str

    def send(self, message: EmailMessage) -> None:  # pragma: no cover - interface
        ...


class ConsoleProvider:
    """Não envia nada: apenas registra que enviaria (sem corpo, sem segredos)."""

    name = "console"

    def send(self, message: EmailMessage) -> None:
        logger.info("[email:console] para=%s assunto=%s", message["To"], message["Subject"])


class SMTPProvider:
    name = "smtp"

    def __init__(self, settings: EmailSettings) -> None:
        self._s = settings

    def send(self, message: EmailMessage) -> None:
        if not self._s.smtp_host:
            raise RuntimeError("SMTP_HOST não configurado.")
        context = ssl.create_default_context()
        if self._s.smtp_port == 465:
            client: smtplib.SMTP = smtplib.SMTP_SSL(
                self._s.smtp_host, self._s.smtp_port, timeout=15, context=context
            )
        else:
            client = smtplib.SMTP(self._s.smtp_host, self._s.smtp_port, timeout=15)
        with client:
            if self._s.smtp_port != 465 and self._s.smtp_starttls:
                client.starttls(context=context)
            if self._s.smtp_user:
                client.login(self._s.smtp_user, self._s.smtp_password)
            client.send_message(message)


def build_provider(settings: EmailSettings) -> EmailProvider:
    if settings.provider == "smtp":
        return SMTPProvider(settings)
    if settings.provider == "console":
        return ConsoleProvider()
    raise RuntimeError(f"EMAIL_PROVIDER desconhecido: {settings.provider!r}")


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

_SUBJECTS = {
    TEMPLATE_DELIVERY: "Seu e-book está a caminho",
    TEMPLATE_COMMERCIAL: "Um próximo passo para você",
}


def _first_name(nome: str) -> str:
    parts = (nome or "").strip().split()
    return parts[0] if parts else ""


def render_template(
    template: str,
    *,
    nome: str,
    delivery_url: str | None = None,
    paid_product_url: str | None = None,
    include_commercial_cta: bool = False,
) -> tuple[str, str, str]:
    """Devolve (assunto, texto, html). Nenhum link é inventado."""
    first = _first_name(nome)
    greeting = f"Olá, {first}!" if first else "Olá!"
    text_lines = [greeting, ""]
    html_parts = [f"<p>{escape(greeting)}</p>"]

    if template == TEMPLATE_DELIVERY:
        text_lines.append("Obrigado por baixar o nosso e-book.")
        html_parts.append("<p>Obrigado por baixar o nosso e-book.</p>")
        if delivery_url:
            text_lines += ["Acesse o material aqui:", delivery_url]
            html_parts.append(
                f'<p>Acesse o material: <a href="{escape(delivery_url, quote=True)}">abrir e-book</a></p>'
            )
        if include_commercial_cta and paid_product_url:
            text_lines += ["", "Se quiser ir além, conheça a versão completa:", paid_product_url]
            html_parts.append(
                f'<p>Se quiser ir além, <a href="{escape(paid_product_url, quote=True)}">conheça a versão completa</a>.</p>'
            )
    elif template == TEMPLATE_COMMERCIAL:
        if not paid_product_url:
            raise ValueError("Convite comercial exige URL do produto pago.")
        text_lines += ["Preparamos uma versão completa para você:", paid_product_url]
        html_parts.append(
            f'<p>Preparamos uma versão completa para você: '
            f'<a href="{escape(paid_product_url, quote=True)}">conhecer</a>.</p>'
        )
    else:
        raise ValueError(f"Template desconhecido: {template}")

    text_lines += ["", "Para deixar de receber e-mails, responda esta mensagem pedindo a remoção."]
    html_parts.append(
        '<p style="color:#7B879B;font-size:12px">Para deixar de receber e-mails, '
        "responda esta mensagem pedindo a remoção.</p>"
    )
    return _SUBJECTS[template], "\n".join(text_lines), "".join(html_parts)


def build_message(settings: EmailSettings, to: str, subject: str, text: str, html: str) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((settings.from_name, settings.from_address))
    message["To"] = to
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    return message


# ---------------------------------------------------------------------------
# Envio
# ---------------------------------------------------------------------------


@dataclass
class SendResult:
    status: str  # "enviado" | "falha" | "ignorado"
    template: str
    provider: str
    detail: str | None = None


def _safe_error(exc: Exception, settings: EmailSettings) -> str:
    """Mensagem curta de erro, sem segredos."""
    text = f"{type(exc).__name__}: {exc}"
    for secret in (settings.smtp_password, settings.smtp_user):
        if secret:
            text = text.replace(secret, "***")
    return text[:300]


def send_template(
    *,
    template: str,
    nome: str,
    email: str,
    consentimento: bool,
    settings: EmailSettings | None = None,
    provider: EmailProvider | None = None,
) -> SendResult:
    """Envia um template respeitando flag, consentimento e configuração. Nunca levanta."""
    settings = settings or load_settings()
    if not settings.enabled:
        return SendResult("ignorado", template, settings.provider, "Automação de e-mail desligada.")
    if not consentimento:
        return SendResult("ignorado", template, settings.provider, "Lead sem consentimento de contato.")
    if not settings.from_address:
        return SendResult("falha", template, settings.provider, "EMAIL_FROM_ADDRESS não configurado.")

    try:
        include_cta = template == TEMPLATE_DELIVERY and settings.commercial_cta_active
        if template == TEMPLATE_COMMERCIAL and not settings.commercial_cta_active:
            return SendResult("ignorado", template, settings.provider, "Etapa comercial inativa (flag ou URL ausente).")
        subject, text, html = render_template(
            template,
            nome=nome,
            delivery_url=settings.delivery_url,
            paid_product_url=settings.paid_product_url,
            include_commercial_cta=include_cta,
        )
        message = build_message(settings, email, subject, text, html)
        (provider or build_provider(settings)).send(message)
        return SendResult("enviado", template, settings.provider)
    except Exception as exc:  # noqa: BLE001 - falha de provedor nunca pode propagar
        logger.warning("Falha ao enviar e-mail (%s): %s", template, _safe_error(exc, settings))
        return SendResult("falha", template, settings.provider, _safe_error(exc, settings))
