import os
import re
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import jwt

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel, Field, field_validator
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from sqlalchemy import case, func, text
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
import email_service

from models import (
    Campaign,
    ContentProgress,
    Course,
    CourseContent,
    EmailLog,
    Enrollment,
    Interaction,
    Lead,
    Product,
    Sale,
    User,
)


# =========================================================
# APLICAÇÃO
# =========================================================


app = FastAPI(
    title="Gestão Inteligente API — SARGTECH",
    version="2.1.0-rc.5",
)


APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
IS_PRODUCTION = APP_ENV == "production"

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_BASE_URL = os.getenv("UPLOAD_BASE_URL", "http://127.0.0.1:8000/uploads").rstrip("/")


def _build_cors_origins() -> list[str]:
    """Origens permitidas no CORS.

    O navegador fala com o Next.js (BFF), então a API em si só precisa aceitar
    o FRONTEND_URL. Origens adicionais (por exemplo, a página do e-book) entram
    por CORS_ORIGINS, separadas por vírgula. Em desenvolvimento, as portas do
    Live Server (5500) continuam liberadas; em produção, não.
    """
    origins = {FRONTEND_URL}
    for item in os.getenv("CORS_ORIGINS", "").split(","):
        item = item.strip().rstrip("/")
        if item:
            origins.add(item)
    if not IS_PRODUCTION:
        origins.update({"http://localhost:5500", "http://127.0.0.1:5500"})
    return sorted(origins)


app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Erros de validação (422) com `detail` em texto.

    O padrão do FastAPI devolve `detail` como lista de objetos; o frontend exibe
    `detail` diretamente na tela, então precisa de uma string.
    """
    mensagens: list[str] = []
    for erro in exc.errors():
        caminho = [
            str(parte)
            for parte in erro.get("loc", ())
            if parte not in ("body", "query", "path")
        ]
        campo = ".".join(caminho)
        mensagem = str(erro.get("msg", "valor inválido"))
        if mensagem.startswith("Value error, "):
            mensagem = mensagem[len("Value error, "):]
        mensagens.append(f"{campo}: {mensagem}" if campo else mensagem)

    return JSONResponse(
        status_code=422,
        content={"detail": "Dados inválidos — " + "; ".join(mensagens)},
    )


# =========================================================
# CONFIGURAÇÃO DE AUTENTICAÇÃO
# =========================================================


PASSWORD_HASHER = PasswordHasher()


JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY"
)

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "480",
    )
)


if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY não encontrada no .env"
    )

_JWT_SECRET_PLACEHOLDER = "troque-por-uma-chave-secreta-forte"

if IS_PRODUCTION and (
    JWT_SECRET_KEY == _JWT_SECRET_PLACEHOLDER or len(JWT_SECRET_KEY) < 32
):
    raise RuntimeError(
        "JWT_SECRET_KEY insegura para APP_ENV=production: use um valor "
        "aleatório com pelo menos 32 caracteres "
        "(python -c \"import secrets; print(secrets.token_urlsafe(48))\")."
    )

# Hash descartável usado para igualar o tempo de resposta do login quando o
# e-mail não existe (evita enumeração de usuários por tempo de resposta).
_DUMMY_PASSWORD_HASH = PASSWORD_HASHER.hash("senha-descartavel-sem-uso")


bearer_scheme = HTTPBearer(
    auto_error=False
)


# =========================================================
# CONSTANTES
# =========================================================


STATUS_VALIDOS = {
    "Lead",
    "Contato realizado",
    "Interessado",
    "Reunião",
    "Proposta",
    "Negociação",
    "Fechado",
    "Pós-venda",
    "Perdido",
}


STATUS_ORDEM = [
    "Lead",
    "Contato realizado",
    "Interessado",
    "Reunião",
    "Proposta",
    "Negociação",
    "Fechado",
    "Pós-venda",
    "Perdido",
]

CONVERTED_STATUSES = {"Fechado", "Pós-venda"}
PAYMENT_STATUSES = {"Pago", "Pendente", "Cancelado", "Reembolsado"}
TIPOS_CLIENTE = {"B2B", "B2C"}

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean_text(value: str | None) -> str | None:
    """Remove espaços nas pontas; texto vazio vira None."""
    if value is None:
        return None
    value = value.strip()
    return value or None


def _validate_email(value: str | None) -> str | None:
    value = _clean_text(value)
    if value is not None and not _EMAIL_PATTERN.match(value):
        raise ValueError("E-mail inválido.")
    return value


def _validate_http_url(value: str | None) -> str | None:
    """Aceita apenas links http(s); bloqueia esquemas como javascript: e data:."""
    value = _clean_text(value)
    if value is not None and not re.match(r"^https?://\S+$", value, re.IGNORECASE):
        raise ValueError("A URL deve começar com http:// ou https://.")
    return value


# =========================================================
# MODELOS PYDANTIC
# =========================================================


class LeadCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    origem: str = Field(min_length=1, max_length=100)
    objetivo: str = Field(min_length=1, max_length=255)
    status: str = "Lead"
    interesse: str = Field(default="Médio", min_length=1, max_length=50)

    idade: int | None = Field(default=None, ge=0, le=120)
    genero: str | None = None
    cidade: str | None = None
    faixa_orcamento: str | None = None

    tipo_cliente: str = "B2C"
    empresa: str | None = None
    cargo: str | None = None
    email: str | None = None
    area_profissional: str | None = None
    telefone: str | None = None
    consentimento_contato: bool = False
    segmento: str | None = None
    tamanho_equipe: int | None = Field(default=None, ge=0)
    dor_gatilho: str | None = None
    proxima_acao: str | None = None
    proxima_acao_em: datetime | None = None
    motivo_perda: str | None = None
    formato_interesse: str | None = None
    oferta_interesse: str | None = None

    campaign_id: int | None = None

    @field_validator("nome", "origem", "objetivo", "interesse")
    @classmethod
    def _strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Campo obrigatório.")
        return value

    @field_validator("tipo_cliente")
    @classmethod
    def _validate_tipo_cliente(cls, value: str) -> str:
        if value not in TIPOS_CLIENTE:
            raise ValueError("Tipo de cliente deve ser B2B ou B2C.")
        return value

    @field_validator("email")
    @classmethod
    def _validate_lead_email(cls, value: str | None) -> str | None:
        return _validate_email(value)


class LeadUpdate(LeadCreate):
    pass


class LeadStatusUpdate(BaseModel):
    status: str


class InteractionCreate(BaseModel):
    tipo: str = Field(min_length=1, max_length=50)
    descricao: str = Field(min_length=1)

    resultado: str | None = Field(default=None, max_length=100)
    follow_up_em: datetime | None = None

    @field_validator("tipo", "descricao")
    @classmethod
    def _strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Campo obrigatório.")
        return value


class ProductCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    descricao: str | None = None
    preco: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    ativo: bool = True

    @field_validator("nome")
    @classmethod
    def _strip_nome(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Nome é obrigatório.")
        return value


class SaleCreate(BaseModel):
    lead_id: int
    product_id: int
    quantidade: int = 1

    forma_pagamento: str = Field(min_length=1, max_length=50)
    status_pagamento: str = "Pago"


class SalePaymentStatusUpdate(BaseModel):
    status_pagamento: str


class CampaignCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    canal: str = Field(min_length=1, max_length=80)
    descricao: str | None = None
    custo: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    ativo: bool = True
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None


class CourseCreate(BaseModel):
    product_id: int
    nome: str = Field(min_length=1, max_length=150)
    descricao: str | None = None
    ativo: bool = True

    @field_validator("nome")
    @classmethod
    def _strip_course_nome(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Nome é obrigatório.")
        return value

    @field_validator("descricao")
    @classmethod
    def _strip_course_descricao(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class CourseContentCreate(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    tipo: str
    ordem: int = Field(ge=0)

    duracao_minutos: int | None = Field(default=None, ge=0)
    descricao: str | None = None
    url_conteudo: str | None = None

    ativo: bool = True

    @field_validator("url_conteudo")
    @classmethod
    def _validate_url(cls, value: str | None) -> str | None:
        return _validate_http_url(value)


class CourseContentUpdate(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    tipo: str
    ordem: int = Field(ge=0)

    duracao_minutos: int | None = Field(default=None, ge=0)
    descricao: str | None = None
    url_conteudo: str | None = None

    ativo: bool = True

    @field_validator("url_conteudo")
    @classmethod
    def _validate_url(cls, value: str | None) -> str | None:
        return _validate_http_url(value)


class ContentProgressUpdate(BaseModel):
    progresso: int


class BootstrapAdminCreate(BaseModel):
    nome: str
    email: str
    senha: str


class LoginRequest(BaseModel):
    email: str
    senha: str

class UserCreate(BaseModel):
    nome: str
    email: str
    senha: str
    role: str
    lead_id: int | None = None
    ativo: bool = True


class UserUpdate(BaseModel):
    nome: str
    email: str
    role: str
    lead_id: int | None = None
    ativo: bool = True
    senha: str | None = None

class EbookLeadCreate(BaseModel):
    nome: str
    email: str
    whatsapp: str | None = None
    area_profissional: str | None = None

    origem: str = "direto"
    utm_medium: str | None = None
    utm_campaign: str | None = None

    consentimento: bool

# =========================================================
# FUNÇÕES DE AUTENTICAÇÃO
# =========================================================


def create_access_token(
    user: User,
):
    agora = datetime.now(
        timezone.utc
    )

    expiracao = (
        agora
        + timedelta(
            minutes=
            ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user.id),
        "role": user.role,
        "iat": agora,
        "exp": expiracao,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def get_current_user(
    credentials:
        HTTPAuthorizationCredentials
        | None
        = Depends(bearer_scheme),

    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Autenticação necessária",
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[
                JWT_ALGORITHM
            ],
        )

        user_id_raw = payload.get(
            "sub"
        )

        if user_id_raw is None:
            raise ValueError()

        user_id = int(
            user_id_raw
        )

    except (
        InvalidTokenError,
        TypeError,
        ValueError,
    ):
        raise HTTPException(
            status_code=401,
            detail=(
                "Token inválido ou expirado"
            ),
        )

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if not user or not user.ativo:
        raise HTTPException(
            status_code=401,
            detail=(
                "Usuário inválido ou inativo"
            ),
        )

    return user


def require_roles(
    *allowed_roles: str,
):
    def role_checker(
        current_user: User = Depends(
            get_current_user
        ),
    ):
        if (
            current_user.role
            not in allowed_roles
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Seu perfil não possui "
                    "permissão para esta ação."
                ),
            )

        return current_user

    return role_checker


def validate_enrollment_access(
    enrollment_id: int,
    current_user: User,
    db: Session,
):
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.id
            == enrollment_id
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(
            status_code=404,
            detail="Matrícula não encontrada",
        )

    if current_user.role == "admin":
        return enrollment

    if current_user.role == "aluno":
        if current_user.lead_id is None:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Usuário aluno não está "
                    "associado a um cliente."
                ),
            )

        if (
            enrollment.lead_id
            != current_user.lead_id
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Você não possui acesso "
                    "a esta matrícula."
                ),
            )

        if enrollment.status == "Acesso suspenso":
            raise HTTPException(
                status_code=403,
                detail="Acesso ao curso suspenso. Verifique a situação do pagamento.",
            )

        return enrollment

    raise HTTPException(
        status_code=403,
        detail="Acesso não autorizado.",
    )


# =========================================================
# REGRAS DE VENDA → LEAD → MATRÍCULA
# =========================================================


def mark_lead_closed_after_payment(lead: Lead | None) -> None:
    """Venda paga leva o Lead a "Fechado", mas nunca faz o funil regredir.

    Um Lead que já está em "Pós-venda" permanece em "Pós-venda".
    """
    if lead is not None and lead.status != "Pós-venda":
        lead.status = "Fechado"


def has_other_paid_sale_for_course(
    db: Session,
    lead_id: int,
    product_id: int,
    exclude_sale_id: int | None = None,
) -> bool:
    """Existe outra venda Paga do mesmo produto (curso) para o mesmo Lead?

    Cada curso está ligado a um único produto, então vendas pagas do mesmo
    produto para o mesmo Lead dão direito à mesma matrícula.
    """
    query = db.query(Sale.id).filter(
        Sale.lead_id == lead_id,
        Sale.product_id == product_id,
        Sale.status_pagamento == "Pago",
    )

    if exclude_sale_id is not None:
        query = query.filter(Sale.id != exclude_sale_id)

    return query.first() is not None


def restore_enrollment_access(enrollment: Enrollment) -> None:
    """Reativa uma matrícula suspensa preservando o estado acadêmico.

    A suspensão só troca o status; as datas de acesso/conclusão e o progresso
    dos conteúdos continuam gravados. O status volta coerente com eles:
    "Concluído" se o curso foi concluído, "Em andamento" se já houve acesso e
    "Acesso liberado" se o aluno ainda não acessou.
    """
    if enrollment.status != "Acesso suspenso":
        return

    if enrollment.concluido_em is not None:
        enrollment.status = "Concluído"
    elif enrollment.primeiro_acesso_em is not None:
        enrollment.status = "Em andamento"
    else:
        enrollment.status = "Acesso liberado"


# =========================================================
# FUNÇÕES AUXILIARES LMS
# =========================================================


def calculate_enrollment_progress(
    db: Session,
    enrollment_id: int,
    course_id: int,
):
    contents = (
        db.query(CourseContent)
        .filter(
            CourseContent.course_id
            == course_id,

            CourseContent.ativo.is_(
                True
            ),
        )
        .all()
    )

    if not contents:
        return 0.0

    progress_rows = (
        db.query(ContentProgress)
        .filter(
            ContentProgress.enrollment_id
            == enrollment_id
        )
        .all()
    )

    progress_map = {
        item.content_id:
            item.progresso
        for item in progress_rows
    }

    total = sum(
        progress_map.get(
            content.id,
            0,
        )
        for content in contents
    )

    return round(
        total / len(contents),
        2,
    )
def validate_user_role_and_lead(
    role: str,
    lead_id: int | None,
    db: Session,
    exclude_user_id: int | None = None,
):
    roles_validos = {
        "admin",
        "vendedor",
        "aluno",
    }

    if role not in roles_validos:
        raise HTTPException(
            status_code=400,
            detail="Perfil de usuário inválido.",
        )

    if role != "aluno":
        return None

    if lead_id is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Usuário aluno precisa estar "
                "associado a um Lead."
            ),
        )

    lead = (
        db.query(Lead)
        .filter(
            Lead.id == lead_id
        )
        .first()
    )

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead não encontrado.",
        )

    query = (
        db.query(User)
        .filter(
            User.lead_id == lead_id
        )
    )

    if exclude_user_id is not None:
        query = query.filter(
            User.id != exclude_user_id
        )

    existing_user = query.first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail=(
                "Este Lead já possui "
                "uma conta de usuário."
            ),
        )

    return lead_id

# =========================================================
# SISTEMA / HEALTH
# =========================================================


@app.get("/")
def root():
    return {
        "message":
            "Gestão Inteligente API — SARGTECH online"
    }


@app.get("/health")
def health():
    return {
        "status": "online"
    }


@app.get("/health/database")
def database_health(
    db: Session = Depends(get_db),
):
    try:
        result = db.execute(
            text("SELECT 1")
        ).scalar()
    except Exception:
        # 503 permite que o orquestrador/monitor detecte banco fora do ar
        # sem expor detalhes da conexão na resposta.
        raise HTTPException(
            status_code=503,
            detail="Banco de dados indisponível.",
        )

    return {
        "database": "online",
        "test": result,
    }


# =========================================================
# AUTENTICAÇÃO
# =========================================================


@app.post(
    "/api/auth/bootstrap-admin",
    status_code=201,
)
def bootstrap_admin(
    data: BootstrapAdminCreate,
    db: Session = Depends(get_db),
):
    total_users = (
        db.query(
            func.count(User.id)
        )
        .scalar()
        or 0
    )

    if total_users > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                "O administrador inicial "
                "já foi configurado."
            ),
        )

    nome = data.nome.strip()

    email = (
        data.email
        .strip()
        .lower()
    )

    if not nome:
        raise HTTPException(
            status_code=400,
            detail="Nome é obrigatório.",
        )

    if len(data.senha) < 8:
        raise HTTPException(
            status_code=400,
            detail=(
                "A senha deve possuir "
                "pelo menos 8 caracteres."
            ),
        )

    admin = User(
        nome=nome,
        email=email,

        senha_hash=
        PASSWORD_HASHER.hash(
            data.senha
        ),

        role="admin",
        ativo=True,
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    return {
        "id": admin.id,
        "nome": admin.nome,
        "email": admin.email,
        "role": admin.role,
    }


@app.post("/api/auth/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    email = (
        data.email
        .strip()
        .lower()
    )

    user = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )

    if not user:
        # Executa uma verificação descartável para que a resposta demore o
        # mesmo tempo de um e-mail existente com senha errada.
        try:
            PASSWORD_HASHER.verify(_DUMMY_PASSWORD_HASH, data.senha)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            pass

        raise HTTPException(
            status_code=401,
            detail=(
                "E-mail ou senha inválidos"
            ),
        )

    try:
        PASSWORD_HASHER.verify(
            user.senha_hash,
            data.senha,
        )
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        raise HTTPException(
            status_code=401,
            detail=(
                "E-mail ou senha inválidos"
            ),
        )

    if not user.ativo:
        raise HTTPException(
            status_code=403,
            detail="Usuário inativo",
        )

    user.ultimo_login_em = (
        datetime.now()
    )

    db.commit()

    token = create_access_token(
        user
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,

        "user": {
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "role": user.role,
            "lead_id": user.lead_id,
            "ativo": user.ativo,
        },
    }


@app.get("/api/auth/me")
def auth_me(
    current_user: User = Depends(
        get_current_user
    ),
):
    return {
        "id": current_user.id,
        "nome": current_user.nome,
        "email": current_user.email,
        "role": current_user.role,
        "lead_id":
            current_user.lead_id,
        "ativo":
            current_user.ativo,
    }


# =========================================================
# DASHBOARD / BI
# =========================================================


@app.get("/api/dashboard/summary")
def dashboard_summary(
    current_user: User = Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):

    total_leads = (
        db.query(
            func.count(Lead.id)
        )
        .scalar()
        or 0
    )

    vendidos = (
        db.query(
            func.count(Lead.id)
        )
        .filter(
            Lead.status.in_(CONVERTED_STATUSES)
        )
        .scalar()
        or 0
    )

    perdidos = (
        db.query(
            func.count(Lead.id)
        )
        .filter(
            Lead.status == "Perdido"
        )
        .scalar()
        or 0
    )

    leads_ativos = (
        total_leads
        - vendidos
        - perdidos
    )

    taxa_conversao = (
        round(
            (
                vendidos
                / total_leads
            )
            * 100,
            2,
        )
        if total_leads > 0
        else 0.0
    )

    total_contatos = (
        db.query(
            func.coalesce(
                func.sum(
                    Lead.contatos
                ),
                0,
            )
        )
        .scalar()
        or 0
    )

    total_interacoes = (
        db.query(
            func.count(
                Interaction.id
            )
        )
        .scalar()
        or 0
    )

    followups_agendados = (
        db.query(
            func.count(
                Interaction.id
            )
        )
        .filter(
            Interaction.follow_up_em
            .is_not(None)
        )
        .scalar()
        or 0
    )

    vendas_pagas = (
        db.query(
            func.count(Sale.id)
        )
        .filter(
            Sale.status_pagamento
            == "Pago"
        )
        .scalar()
        or 0
    )

    receita_total = (
        db.query(
            func.coalesce(
                func.sum(
                    Sale.valor_total
                ),
                0,
            )
        )
        .filter(
            Sale.status_pagamento
            == "Pago"
        )
        .scalar()
        or 0
    )

    receita_total = float(
        receita_total
    )

    ticket_medio = (
        round(
            receita_total
            / vendas_pagas,
            2,
        )
        if vendas_pagas > 0
        else 0.0
    )

    status_rows = (
        db.query(
            Lead.status,
            func.count(Lead.id),
        )
        .group_by(
            Lead.status
        )
        .all()
    )

    status_counts = {
        status: 0
        for status in STATUS_ORDEM
    }

    for status, total in status_rows:
        status_counts[status] = total

    por_status = [
        {
            "status": status,
            "total":
                status_counts[
                    status
                ],
        }
        for status in STATUS_ORDEM
    ]

    origem_rows = (
        db.query(
            Lead.origem,
            func.count(Lead.id),
        )
        .group_by(
            Lead.origem
        )
        .order_by(
            func.count(
                Lead.id
            ).desc()
        )
        .all()
    )

    por_origem = [
        {
            "origem": origem,
            "total": total,
        }
        for origem, total
        in origem_rows
    ]

    produto_rows = (
        db.query(
            Product.id,
            Product.nome,
            func.count(Sale.id),

            func.coalesce(
                func.sum(
                    Sale.valor_total
                ),
                0,
            ),
        )
        .join(
            Sale,
            Sale.product_id
            == Product.id,
        )
        .filter(
            Sale.status_pagamento
            == "Pago"
        )
        .group_by(
            Product.id,
            Product.nome,
        )
        .order_by(
            func.sum(
                Sale.valor_total
            ).desc()
        )
        .all()
    )

    por_produto = [
        {
            "product_id":
                product_id,

            "produto":
                nome,

            "vendas":
                vendas,

            "receita":
                float(receita),
        }
        for (
            product_id,
            nome,
            vendas,
            receita,
        ) in produto_rows
    ]

    receita_origem_rows = (
        db.query(
            Lead.origem,

            func.coalesce(
                func.sum(
                    Sale.valor_total
                ),
                0,
            ),
        )
        .join(
            Sale,
            Sale.lead_id
            == Lead.id,
        )
        .filter(
            Sale.status_pagamento
            == "Pago"
        )
        .group_by(
            Lead.origem
        )
        .order_by(
            func.sum(
                Sale.valor_total
            ).desc()
        )
        .all()
    )

    receita_por_origem = [
        {
            "origem": origem,
            "receita":
                float(receita),
        }
        for origem, receita
        in receita_origem_rows
    ]

    conversao_por_origem = []

    for origem, total in origem_rows:
        convertidos = (
            db.query(
                func.count(Lead.id)
            )
            .filter(
                Lead.origem
                == origem,

                Lead.status.in_(CONVERTED_STATUSES),
            )
            .scalar()
            or 0
        )

        taxa = (
            round(
                (
                    convertidos
                    / total
                )
                * 100,
                2,
            )
            if total > 0
            else 0.0
        )

        conversao_por_origem.append(
            {
                "origem": origem,
                "leads": total,
                "convertidos":
                    convertidos,
                "conversao":
                    taxa,
            }
        )

    return {
        "total_leads":
            total_leads,

        "leads_ativos":
            leads_ativos,

        "vendidos":
            vendidos,

        "perdidos":
            perdidos,

        "taxa_conversao":
            taxa_conversao,

        "total_contatos":
            total_contatos,

        "total_interacoes":
            total_interacoes,

        "followups_agendados":
            followups_agendados,

        "vendas_pagas":
            vendas_pagas,

        "receita_total":
            receita_total,

        "ticket_medio":
            ticket_medio,

        "por_status":
            por_status,

        "por_origem":
            por_origem,

        "por_produto":
            por_produto,

        "receita_por_origem":
            receita_por_origem,

        "conversao_por_origem":
            conversao_por_origem,
    }


# =========================================================
# E-MAIL PÓS E-BOOK
# =========================================================


def send_ebook_delivery_email(lead_id: int) -> None:
    """Envia o e-mail de entrega do material e registra o resultado.

    Usa sessão própria (executa após a resposta). Nunca levanta exceção.
    """
    try:
        settings = email_service.load_settings()
        if not settings.enabled:
            return  # feature flag desligada: nada é enviado nem registrado

        with SessionLocal() as db:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead or not lead.email:
                return

            result = email_service.send_template(
                template=email_service.TEMPLATE_DELIVERY,
                nome=lead.nome,
                email=lead.email,
                consentimento=lead.consentimento_contato,
                settings=settings,
            )
            db.add(
                EmailLog(
                    lead_id=lead.id,
                    destinatario=lead.email,
                    template=result.template,
                    provider=result.provider,
                    status=result.status,
                    detalhe=result.detail,
                )
            )
            if result.status == "enviado":
                db.add(
                    Interaction(
                        lead_id=lead.id,
                        tipo="E-mail automático",
                        descricao="Entrega do e-book enviada por e-mail automático.",
                        resultado="Enviado",
                    )
                )
            db.commit()
    except Exception:  # noqa: BLE001 - nunca pode afetar o fluxo do Lead
        email_service.logger.exception("Falha inesperada na automação de e-mail do lead %s", lead_id)


@app.get("/api/email-logs")
def list_email_logs(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    rows = db.query(EmailLog).order_by(EmailLog.id.desc()).limit(100).all()
    return [
        {
            "id": row.id,
            "lead_id": row.lead_id,
            "destinatario": row.destinatario,
            "template": row.template,
            "provider": row.provider,
            "status": row.status,
            "detalhe": row.detalhe,
            "criado_em": row.criado_em,
        }
        for row in rows
    ]


# =========================================================
# LEADS
# =========================================================

# Resposta pública ÚNICA (mesmo HTTP 201 e mesmo corpo) para e-mail novo e e-mail já
# existente: impede enumeração de e-mails cadastrados. Não incluir id, nome, status ou
# qualquer flag created/reused aqui.
EBOOK_PUBLIC_RESPONSE = {
    "mensagem": "Solicitação registrada com sucesso. Verifique seu e-mail.",
}


@app.post(
    "/api/public/leads/ebook",
    status_code=201,
)
def create_ebook_lead(
    data: EbookLeadCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    nome = data.nome.strip()
    email = data.email.strip().lower()

    if not nome:
        raise HTTPException(
            status_code=400,
            detail="Nome é obrigatório.",
        )

    if not email:
        raise HTTPException(
            status_code=400,
            detail="E-mail é obrigatório.",
        )

    if not data.consentimento:
        raise HTTPException(
            status_code=400,
            detail="Consentimento é obrigatório.",
        )

    lead_existente = (
        db.query(Lead)
        .filter(
            func.lower(Lead.email) == email
        )
        .first()
    )

    if lead_existente:
        # E-mail já conhecido: NÃO cria duplicata e NÃO bloqueia o fluxo. Reutiliza o
        # Lead, registra o novo download na linha do tempo e dispara o e-mail conforme
        # o consentimento. A resposta é idêntica à de e-mail novo (EBOOK_PUBLIC_RESPONSE).
        lead_existente.consentimento_contato = True  # consentimento dado neste download
        db.add(
            Interaction(
                lead_id=lead_existente.id,
                tipo="Download e-book",
                descricao="Novo download do e-book gratuito por este contato.",
                resultado="Registrado",
            )
        )
        db.commit()

        background_tasks.add_task(send_ebook_delivery_email, lead_existente.id)

        return dict(EBOOK_PUBLIC_RESPONSE)

    novo_lead = Lead(
        nome=nome,

        email=email,
        telefone=data.whatsapp,
        area_profissional=
            data.area_profissional,

        origem=
            data.origem or "direto",

        objetivo=
            "Baixar e-book gratuito",

        status="Lead",

        interesse="Médio",

        tipo_cliente="B2C",

        consentimento_contato=True,

        formato_interesse="E-book",

        oferta_interesse=(
            "SargLab — IA para quem "
            "tem trabalho pra fazer"
        ),

        contatos=0,
    )

    db.add(novo_lead)
    db.commit()
    db.refresh(novo_lead)

    # E-mail pós-download: roda DEPOIS do commit e fora da requisição. Qualquer
    # falha do provedor fica registrada, mas nunca desfaz nem bloqueia o Lead.
    background_tasks.add_task(send_ebook_delivery_email, novo_lead.id)

    return dict(EBOOK_PUBLIC_RESPONSE)

@app.get("/api/leads")
def list_leads(
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    return (
        db.query(Lead)
        .order_by(
            Lead.id.desc()
        )
        .all()
    )


@app.get("/api/leads/{lead_id}")
def get_lead(
    lead_id: int,
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    lead = (
        db.query(Lead)
        .filter(
            Lead.id == lead_id
        )
        .first()
    )

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead não encontrado",
        )

    return lead


@app.post(
    "/api/leads",
    status_code=201,
)
def create_lead(
    lead: LeadCreate,
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    if (
        lead.status
        not in STATUS_VALIDOS
    ):
        raise HTTPException(
            status_code=400,
            detail="Status inválido",
        )

    if (
        lead.campaign_id
        is not None
    ):
        campanha = (
            db.query(Campaign)
            .filter(
                Campaign.id
                == lead.campaign_id
            )
            .first()
        )

        if not campanha:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Campanha não encontrada"
                ),
            )

    novo_lead = Lead(
        nome=lead.nome,
        origem=lead.origem,
        objetivo=lead.objetivo,
        status=lead.status,
        interesse=lead.interesse,

        contatos=0,

        idade=lead.idade,
        genero=lead.genero,
        cidade=lead.cidade,

        faixa_orcamento=lead.faixa_orcamento,
        tipo_cliente=lead.tipo_cliente,
        empresa=lead.empresa,
        cargo=lead.cargo,
        email=lead.email,
        telefone=lead.telefone,
        consentimento_contato=lead.consentimento_contato,
        segmento=lead.segmento,
        tamanho_equipe=lead.tamanho_equipe,
        dor_gatilho=lead.dor_gatilho,
        proxima_acao=lead.proxima_acao,
        proxima_acao_em=lead.proxima_acao_em,
        motivo_perda=lead.motivo_perda,
        formato_interesse=lead.formato_interesse,
        oferta_interesse=lead.oferta_interesse,
        campaign_id=lead.campaign_id,
    )

    db.add(novo_lead)
    db.commit()
    db.refresh(novo_lead)

    return novo_lead


@app.put("/api/leads/{lead_id}")
def update_lead(
    lead_id: int,
    data: LeadUpdate,
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")

    if data.status not in STATUS_VALIDOS:
        raise HTTPException(status_code=400, detail="Status inválido")

    if data.campaign_id is not None:
        campanha = db.query(Campaign).filter(Campaign.id == data.campaign_id).first()
        if not campanha:
            raise HTTPException(status_code=404, detail="Campanha não encontrada")

    for field in (
        "nome", "origem", "objetivo", "status", "interesse", "idade", "genero",
        "cidade", "faixa_orcamento", "tipo_cliente", "empresa", "cargo", "email",
        "telefone", "consentimento_contato", "segmento", "tamanho_equipe",
        "dor_gatilho", "proxima_acao", "proxima_acao_em", "motivo_perda",
        "formato_interesse", "oferta_interesse", "campaign_id",
    ):
        setattr(lead, field, getattr(data, field))

    db.commit()
    db.refresh(lead)
    return lead


@app.patch(
    "/api/leads/{lead_id}/status"
)
def update_lead_status(
    lead_id: int,
    payload: LeadStatusUpdate,
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    if (
        payload.status
        not in STATUS_VALIDOS
    ):
        raise HTTPException(
            status_code=400,
            detail="Status inválido",
        )

    lead = (
        db.query(Lead)
        .filter(
            Lead.id == lead_id
        )
        .first()
    )

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead não encontrado",
        )

    lead.status = payload.status

    db.commit()
    db.refresh(lead)

    return lead


# =========================================================
# INTERAÇÕES
# =========================================================


@app.get(
    "/api/leads/{lead_id}/interactions"
)
def list_interactions(
    lead_id: int,
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    lead = (
        db.query(Lead)
        .filter(
            Lead.id == lead_id
        )
        .first()
    )

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead não encontrado",
        )

    return (
        db.query(Interaction)
        .filter(
            Interaction.lead_id
            == lead_id
        )
        .order_by(
            Interaction.criado_em
            .desc()
        )
        .all()
    )


@app.post(
    "/api/leads/{lead_id}/interactions",
    status_code=201,
)
def create_interaction(
    lead_id: int,
    interaction: InteractionCreate,
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    lead = (
        db.query(Lead)
        .filter(
            Lead.id == lead_id
        )
        .first()
    )

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead não encontrado",
        )

    nova_interacao = Interaction(
        lead_id=lead.id,
        tipo=interaction.tipo,
        descricao=
            interaction.descricao,
        resultado=
            interaction.resultado,
        follow_up_em=
            interaction.follow_up_em,
    )

    db.add(nova_interacao)

    tipos_contato = {
        "WhatsApp",
        "Ligação",
        "Reunião",
        "Follow-up",
    }

    if (
        interaction.tipo
        in tipos_contato
    ):
        lead.contatos += 1

    db.commit()
    db.refresh(nova_interacao)

    return nova_interacao


# =========================================================
# FOLLOW-UPS
# =========================================================


@app.get("/api/followups")
def list_followups(
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    interaction_rows = (
        db.query(Interaction, Lead)
        .join(Lead, Interaction.lead_id == Lead.id)
        .filter(Interaction.follow_up_em.is_not(None))
        .all()
    )

    items = [
        {
            "id": f"interaction-{interaction.id}",
            "source": "interacao",
            "interaction_id": interaction.id,
            "lead_id": lead.id,
            "lead_nome": lead.nome,
            "empresa": lead.empresa,
            "tipo": interaction.tipo,
            "descricao": interaction.descricao,
            "resultado": interaction.resultado,
            "follow_up_em": interaction.follow_up_em,
        }
        for interaction, lead in interaction_rows
    ]

    lead_rows = (
        db.query(Lead)
        .filter(Lead.proxima_acao_em.is_not(None))
        .filter(Lead.status.notin_(["Pós-venda", "Perdido"]))
        .all()
    )
    items.extend(
        {
            "id": f"lead-{lead.id}",
            "source": "proxima_acao",
            "interaction_id": None,
            "lead_id": lead.id,
            "lead_nome": lead.nome,
            "empresa": lead.empresa,
            "tipo": "Próxima ação",
            "descricao": lead.proxima_acao or "Próxima ação comercial",
            "resultado": lead.status,
            "follow_up_em": lead.proxima_acao_em,
        }
        for lead in lead_rows
    )

    items.sort(key=lambda item: item["follow_up_em"] or datetime.max)
    return items


def describe_sale_delivery(sale, course, enrollments_by_key) -> dict:
    """Entrega de uma venda, separando TIPO de STATUS (2.1.0-rc.1).

    - `entrega_tipo`: o que o produto entrega — "LMS" (produto com curso) ou None.
    - `entrega_status`: situação real — "Acesso liberado", "Aguardando pagamento",
      "Acesso suspenso", "Matrícula não gerada" (venda paga sem matrícula; estado de ATENÇÃO) ou
      "Não aplicável" (produto sem curso, curso inativo ou venda cancelada/reembolsada
      que nunca gerou acesso).
    - `aviso`: texto de alerta quando há algo que o operador precisa saber (curso inativo).
    """
    base = {
        "entrega_tipo": None,
        "entrega_status": "Não aplicável",
        "entrega_detalhe": "Este produto não libera curso.",
        "aviso": None,
        "curso_id": None,
        "curso_nome": None,
        "curso_ativo": None,
        "matricula_status": None,
    }
    if course is None:
        return base

    base.update(
        {
            "entrega_tipo": "LMS",
            "curso_id": course.id,
            "curso_nome": course.nome,
            "curso_ativo": course.ativo,
        }
    )
    if not course.ativo:
        base.update(
            {
                "entrega_status": "Não aplicável",
                "entrega_detalhe": "O curso vinculado está inativo e não libera acesso.",
                "aviso": "Curso inativo: a venda é válida, mas não gera matrícula.",
            }
        )
        return base

    enrollment = enrollments_by_key.get((sale.lead_id, course.id))
    base["matricula_status"] = enrollment.status if enrollment else None
    suspended = enrollment is not None and enrollment.status == "Acesso suspenso"

    if sale.status_pagamento == "Pago":
        if enrollment is None:
            base.update(
                {
                    "entrega_status": "Matrícula não gerada",
                    "entrega_detalhe": "Venda paga sem matrícula gerada (ex.: curso vinculado depois da venda).",
                    "aviso": (
                        "Atenção: esta venda paga não gerou matrícula. Não há concessão "
                        "retroativa automática; a liberação depende de decisão operacional."
                    ),
                }
            )
        elif suspended:
            base.update(
                {
                    "entrega_status": "Acesso suspenso",
                    "entrega_detalhe": "Matrícula suspensa por outra venda cancelada/reembolsada.",
                }
            )
        else:
            base.update(
                {
                    "entrega_status": "Acesso liberado",
                    "entrega_detalhe": f"Acesso ao curso “{course.nome}” liberado.",
                }
            )
    elif sale.status_pagamento == "Pendente":
        base.update(
            {
                "entrega_status": "Aguardando pagamento",
                "entrega_detalhe": f"“{course.nome}” será liberado quando o pagamento for confirmado.",
            }
        )
    else:  # Cancelado / Reembolsado
        if suspended:
            base.update(
                {
                    "entrega_status": "Acesso suspenso",
                    "entrega_detalhe": f"Pagamento {sale.status_pagamento.lower()}: acesso suspenso.",
                }
            )
        elif enrollment is not None:
            base.update(
                {
                    "entrega_status": "Acesso liberado",
                    "entrega_detalhe": "Acesso mantido por outra venda paga do mesmo curso.",
                }
            )
        else:
            base.update(
                {
                    "entrega_status": "Não aplicável",
                    "entrega_detalhe": f"Pagamento {sale.status_pagamento.lower()}: não gerou acesso.",
                }
            )
    return base


# =========================================================
# PRODUTOS
# =========================================================


@app.get("/api/products")
def list_products(
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Product, Course)
        .outerjoin(Course, Course.product_id == Product.id)
        .order_by(Product.id.desc())
        .all()
    )

    return [
        {
            "id": product.id,
            "nome": product.nome,
            "descricao": product.descricao,
            "preco": product.preco,
            "ativo": product.ativo,
            "criado_em": product.criado_em,
            # Curso vinculado (relação 1 Produto → no máximo 1 Curso).
            "curso_id": course.id if course else None,
            "curso_nome": course.nome if course else None,
            "curso_ativo": course.ativo if course else None,
            "libera_lms": bool(course and course.ativo),
        }
        for product, course in rows
    ]


@app.post(
    "/api/products",
    status_code=201,
)
def create_product(
    product: ProductCreate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    novo_produto = Product(
        nome=product.nome,
        descricao=
            product.descricao,
        preco=product.preco,
        ativo=product.ativo,
    )

    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)

    return novo_produto


# =========================================================
# VENDAS
# =========================================================


@app.get("/api/sales")
def list_sales(
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    vendas = (
        db.query(
            Sale,
            Lead,
            Product,
        )
        .join(
            Lead,
            Sale.lead_id
            == Lead.id,
        )
        .join(
            Product,
            Sale.product_id
            == Product.id,
        )
        .order_by(
            Sale.criado_em.desc()
        )
        .all()
    )

    courses_by_product = {
        course.product_id: course for course in db.query(Course).all()
    }
    enrollments_by_key = {
        (enrollment.lead_id, enrollment.course_id): enrollment
        for enrollment in db.query(Enrollment).all()
    }

    return [
        {
            "id": venda.id,

            "lead_id":
                lead.id,

            "lead_nome":
                lead.nome,

            "product_id":
                produto.id,

            "produto_nome":
                produto.nome,

            "quantidade":
                venda.quantidade,

            "valor_unitario":
                venda.valor_unitario,

            "valor_total":
                venda.valor_total,

            "forma_pagamento":
                venda.forma_pagamento,

            "status_pagamento":
                venda.status_pagamento,

            "criado_em":
                venda.criado_em,

            **describe_sale_delivery(
                venda,
                courses_by_product.get(venda.product_id),
                enrollments_by_key,
            ),
        }
        for venda, lead, produto
        in vendas
    ]


@app.post(
    "/api/sales",
    status_code=201,
)
def create_sale(
    sale: SaleCreate,
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    lead = (
        db.query(Lead)
        .filter(
            Lead.id == sale.lead_id
        )
        .first()
    )

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead não encontrado",
        )

    produto = (
        db.query(Product)
        .filter(
            Product.id
            == sale.product_id
        )
        .first()
    )

    if not produto:
        raise HTTPException(
            status_code=404,
            detail=(
                "Produto não encontrado"
            ),
        )

    if not produto.ativo:
        raise HTTPException(
            status_code=400,
            detail="Produto está inativo",
        )

    if sale.quantidade <= 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "Quantidade deve ser "
                "maior que zero"
            ),
        )

    if sale.status_pagamento not in PAYMENT_STATUSES:
        raise HTTPException(status_code=400, detail="Status de pagamento inválido")

    valor_total = (
        produto.preco
        * sale.quantidade
    )

    nova_venda = Sale(
        lead_id=lead.id,

        product_id=
            produto.id,

        quantidade=
            sale.quantidade,

        valor_unitario=
            produto.preco,

        valor_total=
            valor_total,

        forma_pagamento=
            sale.forma_pagamento,

        status_pagamento=
            sale.status_pagamento,
    )

    db.add(nova_venda)

    # Precisamos do ID da venda
    # antes do commit final.
    db.flush()

    if (
        sale.status_pagamento
        == "Pago"
    ):
        mark_lead_closed_after_payment(lead)

        curso = (
            db.query(Course)
            .filter(
                Course.product_id
                == produto.id,

                Course.ativo.is_(
                    True
                ),
            )
            .first()
        )

        if curso:
            matricula_existente = (
                db.query(Enrollment)
                .filter(
                    Enrollment.lead_id
                    == lead.id,

                    Enrollment.course_id
                    == curso.id,
                )
                .first()
            )

            if not matricula_existente:
                nova_matricula = (
                    Enrollment(
                        lead_id=
                            lead.id,

                        course_id=
                            curso.id,

                        sale_id=
                            nova_venda.id,

                        status=
                            "Acesso liberado",
                    )
                )

                db.add(
                    nova_matricula
                )

            else:
                # Nova compra válida do mesmo curso restaura o acesso de uma
                # matrícula suspensa, preservando o estado acadêmico.
                restore_enrollment_access(
                    matricula_existente
                )

    db.commit()
    db.refresh(nova_venda)

    return nova_venda


@app.patch("/api/sales/{sale_id}/payment-status")
def update_sale_payment_status(
    sale_id: int,
    data: SalePaymentStatusUpdate,
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Venda não encontrada")

    next_status = data.status_pagamento.strip()
    if next_status not in PAYMENT_STATUSES:
        raise HTTPException(status_code=400, detail="Status de pagamento inválido")

    sale.status_pagamento = next_status
    course = (
        db.query(Course)
        .filter(Course.product_id == sale.product_id, Course.ativo.is_(True))
        .first()
    )
    existing = None
    if course:
        existing = (
            db.query(Enrollment)
            .filter(Enrollment.lead_id == sale.lead_id, Enrollment.course_id == course.id)
            .first()
        )

    if next_status == "Pago":
        lead = db.query(Lead).filter(Lead.id == sale.lead_id).first()
        mark_lead_closed_after_payment(lead)

        if course:
            if not existing:
                db.add(Enrollment(
                    lead_id=sale.lead_id,
                    course_id=course.id,
                    sale_id=sale.id,
                    status="Acesso liberado",
                ))
            else:
                restore_enrollment_access(existing)

    elif next_status in {"Cancelado", "Reembolsado"} and existing:
        # O acesso só é suspenso se não restar outra venda Paga válida do
        # mesmo curso para este Lead.
        if not has_other_paid_sale_for_course(
            db,
            sale.lead_id,
            sale.product_id,
            exclude_sale_id=sale.id,
        ):
            existing.status = "Acesso suspenso"

    db.commit()
    db.refresh(sale)
    return sale


# =========================================================
# CAMPANHAS
# =========================================================


@app.get("/api/campaigns")
def list_campaigns(
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    return (
        db.query(Campaign)
        .order_by(
            Campaign.id.desc()
        )
        .all()
    )


@app.post(
    "/api/campaigns",
    status_code=201,
)
def create_campaign(
    campaign: CampaignCreate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    nova_campanha = Campaign(
        nome=campaign.nome,
        canal=campaign.canal,
        descricao=
            campaign.descricao,
        custo=campaign.custo,
        ativo=campaign.ativo,
        utm_source=campaign.utm_source,
        utm_medium=campaign.utm_medium,
        utm_campaign=campaign.utm_campaign,
    )

    db.add(nova_campanha)
    db.commit()
    db.refresh(nova_campanha)

    return nova_campanha


# =========================================================
# MARKETING ANALYTICS
# =========================================================


@app.get("/api/marketing-analytics")
def marketing_analytics(
    current_user: User = Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    campanhas = (
        db.query(Campaign)
        .order_by(
            Campaign.id.asc()
        )
        .all()
    )

    resultado = []

    for campanha in campanhas:
        total_leads = (
            db.query(
                func.count(Lead.id)
            )
            .filter(
                Lead.campaign_id
                == campanha.id
            )
            .scalar()
            or 0
        )

        leads_convertidos = (
            db.query(
                func.count(
                    func.distinct(
                        Sale.lead_id
                    )
                )
            )
            .join(
                Lead,
                Sale.lead_id
                == Lead.id,
            )
            .filter(
                Lead.campaign_id
                == campanha.id,

                Sale.status_pagamento
                == "Pago",
            )
            .scalar()
            or 0
        )

        vendas = (
            db.query(
                func.count(Sale.id)
            )
            .join(
                Lead,
                Sale.lead_id
                == Lead.id,
            )
            .filter(
                Lead.campaign_id
                == campanha.id,

                Sale.status_pagamento
                == "Pago",
            )
            .scalar()
            or 0
        )

        receita = (
            db.query(
                func.coalesce(
                    func.sum(
                        Sale.valor_total
                    ),
                    0,
                )
            )
            .join(
                Lead,
                Sale.lead_id
                == Lead.id,
            )
            .filter(
                Lead.campaign_id
                == campanha.id,

                Sale.status_pagamento
                == "Pago",
            )
            .scalar()
            or 0
        )

        custo = float(
            campanha.custo
        )

        receita = float(
            receita
        )

        conversao = (
            round(
                (
                    leads_convertidos
                    / total_leads
                )
                * 100,
                2,
            )
            if total_leads > 0
            else 0
        )

        cpl = (
            round(
                custo
                / total_leads,
                2,
            )
            if total_leads > 0
            else 0
        )

        cac = (
            round(
                custo
                / leads_convertidos,
                2,
            )
            if leads_convertidos > 0
            else None
        )

        roi = (
            round(
                (
                    (
                        receita
                        - custo
                    )
                    / custo
                )
                * 100,
                2,
            )
            if custo > 0
            else None
        )

        resultado.append(
            {
                "campaign_id":
                    campanha.id,

                "campanha":
                    campanha.nome,

                "canal":
                    campanha.canal,

                "custo":
                    custo,

                "leads":
                    total_leads,

                "convertidos":
                    leads_convertidos,

                "vendas":
                    vendas,

                "receita":
                    receita,

                "conversao":
                    conversao,

                "cpl":
                    cpl,

                "cac":
                    cac,

                "roi":
                    roi,
            }
        )

    return resultado


# =========================================================
# CUSTOMER ANALYTICS
# =========================================================


@app.get("/api/customer-analytics")
def customer_analytics(
    current_user: User = Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    vendido_case = case(
        (
            Lead.status.in_(CONVERTED_STATUSES),
            1,
        ),
        else_=0,
    )

    faixa_etaria = case(
        (
            Lead.idade.is_(None),
            "Não informado",
        ),
        (
            Lead.idade < 18,
            "Menos de 18",
        ),
        (
            Lead.idade <= 24,
            "18 a 24",
        ),
        (
            Lead.idade <= 34,
            "25 a 34",
        ),
        (
            Lead.idade <= 44,
            "35 a 44",
        ),
        (
            Lead.idade <= 54,
            "45 a 54",
        ),
        else_="55 ou mais",
    )

    idade_rows = (
        db.query(
            faixa_etaria.label(
                "faixa"
            ),
            func.count(Lead.id),
            func.sum(
                vendido_case
            ),
        )
        .group_by(
            faixa_etaria
        )
        .all()
    )

    por_faixa_etaria = []

    for (
        faixa,
        leads,
        vendidos,
    ) in idade_rows:
        vendidos = vendidos or 0

        conversao = (
            round(
                (
                    vendidos
                    / leads
                )
                * 100,
                2,
            )
            if leads > 0
            else 0
        )

        por_faixa_etaria.append(
            {
                "faixa": faixa,
                "leads": leads,
                "vendidos": vendidos,
                "conversao":
                    conversao,
            }
        )

    genero_expr = func.coalesce(
        Lead.genero,
        "Não informado",
    )

    genero_rows = (
        db.query(
            genero_expr.label(
                "genero"
            ),
            func.count(Lead.id),
            func.sum(
                vendido_case
            ),
        )
        .group_by(
            genero_expr
        )
        .all()
    )

    por_genero = []

    for (
        genero,
        leads,
        vendidos,
    ) in genero_rows:
        vendidos = vendidos or 0

        conversao = (
            round(
                (
                    vendidos
                    / leads
                )
                * 100,
                2,
            )
            if leads > 0
            else 0
        )

        por_genero.append(
            {
                "genero": genero,
                "leads": leads,
                "vendidos": vendidos,
                "conversao":
                    conversao,
            }
        )

    cidade_expr = func.coalesce(
        Lead.cidade,
        "Não informado",
    )

    cidade_rows = (
        db.query(
            cidade_expr.label(
                "cidade"
            ),
            func.count(Lead.id),
            func.sum(
                vendido_case
            ),
        )
        .group_by(
            cidade_expr
        )
        .order_by(
            func.count(
                Lead.id
            ).desc()
        )
        .all()
    )

    por_cidade = []

    for (
        cidade,
        leads,
        vendidos,
    ) in cidade_rows:
        vendidos = vendidos or 0

        conversao = (
            round(
                (
                    vendidos
                    / leads
                )
                * 100,
                2,
            )
            if leads > 0
            else 0
        )

        por_cidade.append(
            {
                "cidade":
                    cidade,

                "leads":
                    leads,

                "vendidos":
                    vendidos,

                "conversao":
                    conversao,
            }
        )

    orcamento_expr = func.coalesce(
        Lead.faixa_orcamento,
        "Não informado",
    )

    orcamento_rows = (
        db.query(
            orcamento_expr.label(
                "faixa"
            ),
            func.count(Lead.id),
            func.sum(
                vendido_case
            ),
        )
        .group_by(
            orcamento_expr
        )
        .all()
    )

    por_orcamento = []

    for (
        faixa,
        leads,
        vendidos,
    ) in orcamento_rows:
        vendidos = vendidos or 0

        conversao = (
            round(
                (
                    vendidos
                    / leads
                )
                * 100,
                2,
            )
            if leads > 0
            else 0
        )

        por_orcamento.append(
            {
                "faixa": faixa,
                "leads": leads,
                "vendidos": vendidos,
                "conversao":
                    conversao,
            }
        )

    objetivo_rows = (
        db.query(
            Lead.objetivo,
            func.count(Lead.id),
            func.sum(
                vendido_case
            ),
        )
        .group_by(
            Lead.objetivo
        )
        .order_by(
            func.count(
                Lead.id
            ).desc()
        )
        .all()
    )

    por_objetivo = []

    for (
        objetivo,
        leads,
        vendidos,
    ) in objetivo_rows:
        vendidos = vendidos or 0

        conversao = (
            round(
                (
                    vendidos
                    / leads
                )
                * 100,
                2,
            )
            if leads > 0
            else 0
        )

        por_objetivo.append(
            {
                "objetivo":
                    objetivo,

                "leads":
                    leads,

                "vendidos":
                    vendidos,

                "conversao":
                    conversao,
            }
        )

    receita_orcamento_rows = (
        db.query(
            orcamento_expr.label(
                "faixa"
            ),

            func.coalesce(
                func.sum(
                    Sale.valor_total
                ),
                0,
            ),
        )
        .join(
            Sale,
            Sale.lead_id
            == Lead.id,
        )
        .filter(
            Sale.status_pagamento
            == "Pago"
        )
        .group_by(
            orcamento_expr
        )
        .order_by(
            func.sum(
                Sale.valor_total
            ).desc()
        )
        .all()
    )

    receita_por_orcamento = [
        {
            "faixa": faixa,
            "receita":
                float(receita),
        }
        for faixa, receita
        in receita_orcamento_rows
    ]

    receita_objetivo_rows = (
        db.query(
            Lead.objetivo,

            func.coalesce(
                func.sum(
                    Sale.valor_total
                ),
                0,
            ),
        )
        .join(
            Sale,
            Sale.lead_id
            == Lead.id,
        )
        .filter(
            Sale.status_pagamento
            == "Pago"
        )
        .group_by(
            Lead.objetivo
        )
        .order_by(
            func.sum(
                Sale.valor_total
            ).desc()
        )
        .all()
    )

    receita_por_objetivo = [
        {
            "objetivo":
                objetivo,

            "receita":
                float(receita),
        }
        for objetivo, receita
        in receita_objetivo_rows
    ]

    def grouped_conversion(expr, key_name: str):
        rows = (
            db.query(
                expr.label(key_name),
                func.count(Lead.id),
                func.sum(vendido_case),
            )
            .group_by(expr)
            .order_by(func.count(Lead.id).desc())
            .all()
        )
        result = []
        for label, leads, vendidos in rows:
            vendidos = vendidos or 0
            result.append({
                key_name: label,
                "leads": leads,
                "vendidos": vendidos,
                "conversao": round((vendidos / leads) * 100, 2) if leads else 0.0,
            })
        return result

    tipo_cliente_expr = func.coalesce(Lead.tipo_cliente, "Não informado")
    segmento_expr = func.coalesce(Lead.segmento, "Não informado")
    oferta_expr = func.coalesce(Lead.oferta_interesse, "Não informado")
    formato_expr = func.coalesce(Lead.formato_interesse, "Não informado")
    tamanho_equipe_expr = case(
        (Lead.tamanho_equipe.is_(None), "Não informado"),
        (Lead.tamanho_equipe <= 5, "1 a 5"),
        (Lead.tamanho_equipe <= 20, "6 a 20"),
        (Lead.tamanho_equipe <= 50, "21 a 50"),
        (Lead.tamanho_equipe <= 80, "51 a 80"),
        else_="81+",
    )

    por_tipo_cliente = grouped_conversion(tipo_cliente_expr, "tipo")
    por_segmento = grouped_conversion(segmento_expr, "segmento")
    por_oferta = grouped_conversion(oferta_expr, "oferta")
    por_formato = grouped_conversion(formato_expr, "formato")
    por_tamanho_equipe = grouped_conversion(tamanho_equipe_expr, "faixa")

    return {
        "por_faixa_etaria":
            por_faixa_etaria,

        "por_genero":
            por_genero,

        "por_cidade":
            por_cidade,

        "por_orcamento":
            por_orcamento,

        "por_objetivo":
            por_objetivo,

        "receita_por_orcamento":
            receita_por_orcamento,

        "receita_por_objetivo":
            receita_por_objetivo,

        "por_tipo_cliente": por_tipo_cliente,
        "por_segmento": por_segmento,
        "por_oferta": por_oferta,
        "por_formato": por_formato,
        "por_tamanho_equipe": por_tamanho_equipe,
    }


@app.post("/api/course-contents/upload", status_code=201)
async def upload_course_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("admin")),
):
    allowed_extensions = {
        ".pdf", ".mp4", ".webm", ".mov", ".doc", ".docx",
        ".ppt", ".pptx", ".xls", ".xlsx", ".png", ".jpg", ".jpeg",
    }
    suffix = Path(file.filename or "arquivo").suffix.lower()
    if suffix not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Tipo de arquivo não permitido.")

    content = await file.read(50 * 1024 * 1024 + 1)
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Arquivo excede o limite de 50 MB.")

    safe_name = f"{uuid.uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / safe_name
    destination.write_bytes(content)

    return {
        "filename": file.filename,
        "stored_name": safe_name,
        "url": f"{UPLOAD_BASE_URL}/{safe_name}",
    }


# =========================================================
# CURSOS
# =========================================================


@app.get("/api/courses")
def list_courses(current_user: User = Depends(
    require_roles("admin")
),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            Course,
            Product,
        )
        .join(
            Product,
            Course.product_id
            == Product.id,
        )
        .order_by(
            Course.id.desc()
        )
        .all()
    )

    return [
        {
            "id":
                course.id,

            "product_id":
                product.id,

            "produto":
                product.nome,

            "nome":
                course.nome,

            "descricao":
                course.descricao,

            "ativo":
                course.ativo,

            "criado_em":
                course.criado_em,
        }
        for course, product
        in rows
    ]


@app.post(
    "/api/courses",
    status_code=201,
)
def create_course(
    course: CourseCreate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter(
            Product.id
            == course.product_id
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail=(
                "Produto não encontrado"
            ),
        )

    existing = (
        db.query(Course)
        .filter(
            Course.product_id
            == course.product_id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "Este produto já possui "
                "um curso."
            ),
        )

    novo_curso = Course(
        product_id=
            course.product_id,

        nome=
            course.nome,

        descricao=
            course.descricao,

        ativo=
            course.ativo,
    )

    db.add(novo_curso)
    db.commit()
    db.refresh(novo_curso)

    return novo_curso


# =========================================================
# CONTEÚDOS DOS CURSOS
# =========================================================


@app.get(
    "/api/courses/{course_id}/contents"
)
def list_course_contents(
    course_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    course = (
        db.query(Course)
        .filter(
            Course.id == course_id
        )
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Curso não encontrado",
        )

    return (
        db.query(CourseContent)
        .filter(
            CourseContent.course_id
            == course_id,
        )
        .order_by(
            CourseContent.ordem
            .asc()
        )
        .all()
    )


@app.post(
    "/api/courses/{course_id}/contents",
    status_code=201,
)
def create_course_content(
    course_id: int,
    content: CourseContentCreate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    course = (
        db.query(Course)
        .filter(
            Course.id == course_id
        )
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Curso não encontrado",
        )

    tipos_validos = {
        "video",
        "apostila",
        "material",
    }

    if (
        content.tipo
        not in tipos_validos
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Tipo deve ser video, "
                "apostila ou material."
            ),
        )

    ordem_existente = (
        db.query(CourseContent)
        .filter(
            CourseContent.course_id == course_id,
            CourseContent.ordem == content.ordem,
            CourseContent.ativo.is_(True),
        )
        .first()
    )

    if ordem_existente:
        raise HTTPException(
            status_code=409,
            detail="Já existe um conteúdo ativo com esta ordem.",
        )

    novo_conteudo = CourseContent(
        course_id=course_id,

        titulo=
            content.titulo,

        tipo=
            content.tipo,

        ordem=
            content.ordem,

        duracao_minutos=
            content.duracao_minutos,

        descricao=
            content.descricao,

        url_conteudo=
            content.url_conteudo,

        ativo=
            content.ativo,
    )

    db.add(novo_conteudo)
    db.commit()
    db.refresh(novo_conteudo)

    return novo_conteudo


@app.put(
    "/api/course-contents/{content_id}"
)
def update_course_content(
    content_id: int,
    data: CourseContentUpdate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    content = (
        db.query(CourseContent)
        .filter(
            CourseContent.id
            == content_id
        )
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=404,
            detail=(
                "Conteúdo não encontrado"
            ),
        )

    tipos_validos = {
        "video",
        "apostila",
        "material",
    }

    if (
        data.tipo
        not in tipos_validos
    ):
        raise HTTPException(
            status_code=400,
            detail="Tipo inválido.",
        )

    ordem_existente = (
        db.query(CourseContent)
        .filter(
            CourseContent.course_id == content.course_id,
            CourseContent.ordem == data.ordem,
            CourseContent.id != content.id,
            CourseContent.ativo.is_(True),
        )
        .first()
    )

    if ordem_existente and data.ativo:
        raise HTTPException(
            status_code=409,
            detail="Já existe outro conteúdo ativo com esta ordem.",
        )

    content.titulo = (
        data.titulo
    )

    content.tipo = (
        data.tipo
    )

    content.ordem = (
        data.ordem
    )

    content.duracao_minutos = (
        data.duracao_minutos
    )

    content.descricao = (
        data.descricao
    )

    content.url_conteudo = (
        data.url_conteudo
    )

    content.ativo = (
        data.ativo
    )

    db.commit()
    db.refresh(content)

    return content


@app.delete(
    "/api/course-contents/{content_id}"
)
def delete_course_content(
    content_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    content = (
        db.query(CourseContent)
        .filter(
            CourseContent.id
            == content_id
        )
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=404,
            detail=(
                "Conteúdo não encontrado"
            ),
        )

    content.ativo = False
    db.commit()
    db.refresh(content)

    return {
        "message": "Conteúdo desativado com sucesso.",
        "id": content.id,
        "ativo": content.ativo,
    }


# =========================================================
# MATRÍCULAS - LISTAGEM ADMINISTRATIVA
# =========================================================


@app.get("/api/enrollments")
def list_enrollments(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            Enrollment,
            Lead,
            Course,
        )
        .join(
            Lead,
            Enrollment.lead_id
            == Lead.id,
        )
        .join(
            Course,
            Enrollment.course_id
            == Course.id,
        )
        .order_by(
            Enrollment.id.desc()
        )
        .all()
    )

    resultado = []

    for (
        enrollment,
        lead,
        course,
    ) in rows:
        progresso = (
            calculate_enrollment_progress(
                db,
                enrollment.id,
                course.id,
            )
        )

        resultado.append(
            {
                "id":
                    enrollment.id,

                "lead_id":
                    lead.id,

                "aluno":
                    lead.nome,

                "origem":
                    lead.origem,

                "course_id":
                    course.id,

                "curso":
                    course.nome,

                "status":
                    enrollment.status,

                "progresso":
                    progresso,

                "acesso_liberado_em":
                    enrollment
                    .acesso_liberado_em,

                "primeiro_acesso_em":
                    enrollment
                    .primeiro_acesso_em,

                "ultimo_acesso_em":
                    enrollment
                    .ultimo_acesso_em,

                "concluido_em":
                    enrollment
                    .concluido_em,
            }
        )

    return resultado


# =========================================================
# MINHAS MATRÍCULAS - ALUNO
# =========================================================


@app.get("/api/my/enrollments")
def my_enrollments(
    current_user: User = Depends(
        require_roles(
            "aluno"
        )
    ),
    db: Session = Depends(get_db),
):
    if (
        current_user.lead_id
        is None
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Usuário não está "
                "associado a um cliente."
            ),
        )

    rows = (
        db.query(
            Enrollment,
            Course,
        )
        .join(
            Course,
            Enrollment.course_id
            == Course.id,
        )
        .filter(
            Enrollment.lead_id
            == current_user.lead_id
        )
        .order_by(
            Enrollment.id.desc()
        )
        .all()
    )

    return [
        {
            "id":
                enrollment.id,

            "course_id":
                course.id,

            "curso":
                course.nome,

            "descricao":
                course.descricao,

            "status":
                enrollment.status,

            "progresso":
                calculate_enrollment_progress(
                    db,
                    enrollment.id,
                    course.id,
                ),
        }
        for enrollment, course
        in rows
    ]


# =========================================================
# MATRÍCULA INDIVIDUAL PROTEGIDA
# =========================================================


@app.get(
    "/api/enrollments/{enrollment_id}"
)
def get_enrollment(
    enrollment_id: int,

    current_user: User = Depends(
        require_roles(
            "admin",
            "aluno",
        )
    ),

    db: Session = Depends(get_db),
):
    enrollment = (
        validate_enrollment_access(
            enrollment_id,
            current_user,
            db,
        )
    )

    lead = (
        db.query(Lead)
        .filter(
            Lead.id
            == enrollment.lead_id
        )
        .first()
    )

    course = (
        db.query(Course)
        .filter(
            Course.id
            == enrollment.course_id
        )
        .first()
    )

    if not lead or not course:
        raise HTTPException(
            status_code=404,
            detail=(
                "Dados da matrícula "
                "não encontrados"
            ),
        )

    contents = (
        db.query(CourseContent)
        .filter(
            CourseContent.course_id
            == course.id,

            CourseContent.ativo.is_(
                True
            ),
        )
        .order_by(
            CourseContent.ordem
            .asc()
        )
        .all()
    )

    progress_rows = (
        db.query(ContentProgress)
        .filter(
            ContentProgress.enrollment_id
            == enrollment.id
        )
        .all()
    )

    progress_map = {
        item.content_id:
            item
        for item in progress_rows
    }

    conteudos = []

    for content in contents:
        progress = progress_map.get(
            content.id
        )

        conteudos.append(
            {
                "id":
                    content.id,

                "titulo":
                    content.titulo,

                "tipo":
                    content.tipo,

                "ordem":
                    content.ordem,

                "duracao_minutos":
                    content.duracao_minutos,

                "descricao":
                    content.descricao,

                "url_conteudo":
                    content.url_conteudo,

                "progresso":
                    (
                        progress.progresso
                        if progress
                        else 0
                    ),

                "aberto_em":
                    (
                        progress.aberto_em
                        if progress
                        else None
                    ),

                "ultima_atividade_em":
                    (
                        progress
                        .ultima_atividade_em
                        if progress
                        else None
                    ),

                "concluido_em":
                    (
                        progress.concluido_em
                        if progress
                        else None
                    ),
            }
        )

    progresso_curso = (
        calculate_enrollment_progress(
            db,
            enrollment.id,
            course.id,
        )
    )

    return {
        "id":
            enrollment.id,

        "lead_id":
            lead.id,

        "aluno":
            lead.nome,

        "course_id":
            course.id,

        "curso":
            course.nome,

        "descricao":
            course.descricao,

        "status":
            enrollment.status,

        "progresso":
            progresso_curso,

        "acesso_liberado_em":
            enrollment
            .acesso_liberado_em,

        "primeiro_acesso_em":
            enrollment
            .primeiro_acesso_em,

        "ultimo_acesso_em":
            enrollment
            .ultimo_acesso_em,

        "concluido_em":
            enrollment
            .concluido_em,

        "conteudos":
            conteudos,
    }


# =========================================================
# REGISTRAR ACESSO AO CURSO
# =========================================================


@app.post(
    "/api/enrollments/{enrollment_id}/access"
)
def register_course_access(
    enrollment_id: int,

    current_user: User = Depends(
        require_roles(
            "admin",
            "aluno",
        )
    ),

    db: Session = Depends(get_db),
):
    enrollment = (
        validate_enrollment_access(
            enrollment_id,
            current_user,
            db,
        )
    )

    agora = datetime.now()

    if (
        enrollment.primeiro_acesso_em
        is None
    ):
        enrollment.primeiro_acesso_em = (
            agora
        )

    enrollment.ultimo_acesso_em = (
        agora
    )

    if (
        enrollment.status
        == "Acesso liberado"
    ):
        enrollment.status = (
            "Em andamento"
        )

    db.commit()
    db.refresh(enrollment)

    return enrollment


# =========================================================
# ABRIR CONTEÚDO
# =========================================================


@app.post(
    "/api/enrollments/"
    "{enrollment_id}/contents/"
    "{content_id}/open"
)
def open_course_content(
    enrollment_id: int,
    content_id: int,

    current_user: User = Depends(
        require_roles(
            "admin",
            "aluno",
        )
    ),

    db: Session = Depends(get_db),
):
    enrollment = (
        validate_enrollment_access(
            enrollment_id,
            current_user,
            db,
        )
    )

    content = (
        db.query(CourseContent)
        .filter(
            CourseContent.id
            == content_id
        )
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=404,
            detail=(
                "Conteúdo não encontrado"
            ),
        )

    if (
        content.course_id
        != enrollment.course_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Conteúdo não pertence "
                "ao curso da matrícula."
            ),
        )

    progresso = (
        db.query(ContentProgress)
        .filter(
            ContentProgress.enrollment_id
            == enrollment.id,

            ContentProgress.content_id
            == content.id,
        )
        .first()
    )

    agora = datetime.now()

    if not progresso:
        progresso = ContentProgress(
            enrollment_id=
                enrollment.id,

            content_id=
                content.id,

            progresso=0,

            aberto_em=
                agora,

            ultima_atividade_em=
                agora,
        )

        db.add(progresso)

    else:
        if (
            progresso.aberto_em
            is None
        ):
            progresso.aberto_em = (
                agora
            )

        progresso.ultima_atividade_em = (
            agora
        )

    if (
        enrollment.primeiro_acesso_em
        is None
    ):
        enrollment.primeiro_acesso_em = (
            agora
        )

    enrollment.ultimo_acesso_em = (
        agora
    )

    # Uma matrícula suspensa por cancelamento/reembolso só volta a ser liberada
    # pela situação financeira (venda Paga). Abrir conteúdo, inclusive como
    # admin, não pode reativá-la.
    if enrollment.status not in (
        "Concluído",
        "Acesso suspenso",
    ):
        enrollment.status = (
            "Em andamento"
        )

    db.commit()
    db.refresh(progresso)

    return progresso


# =========================================================
# ATUALIZAR PROGRESSO
# =========================================================


@app.patch(
    "/api/enrollments/"
    "{enrollment_id}/contents/"
    "{content_id}/progress"
)
def update_content_progress(
    enrollment_id: int,
    content_id: int,
    data: ContentProgressUpdate,

    current_user: User = Depends(
        require_roles(
            "admin",
            "aluno",
        )
    ),

    db: Session = Depends(get_db),
):
    if (
        data.progresso < 0
        or data.progresso > 100
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Progresso deve estar "
                "entre 0 e 100."
            ),
        )

    enrollment = (
        validate_enrollment_access(
            enrollment_id,
            current_user,
            db,
        )
    )

    content = (
        db.query(CourseContent)
        .filter(
            CourseContent.id
            == content_id
        )
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=404,
            detail=(
                "Conteúdo não encontrado"
            ),
        )

    if (
        content.course_id
        != enrollment.course_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Conteúdo não pertence "
                "ao curso da matrícula."
            ),
        )

    progresso = (
        db.query(ContentProgress)
        .filter(
            ContentProgress.enrollment_id
            == enrollment.id,

            ContentProgress.content_id
            == content.id,
        )
        .first()
    )

    agora = datetime.now()

    if not progresso:
        progresso = ContentProgress(
            enrollment_id=
                enrollment.id,

            content_id=
                content.id,

            aberto_em=
                agora,
        )

        db.add(progresso)

    progresso.progresso = (
        data.progresso
    )

    progresso.ultima_atividade_em = (
        agora
    )

    if (
        progresso.aberto_em
        is None
    ):
        progresso.aberto_em = (
            agora
        )

    if (
        data.progresso == 100
    ):
        progresso.concluido_em = (
            agora
        )
    else:
        progresso.concluido_em = (
            None
        )

    if (
        enrollment.primeiro_acesso_em
        is None
    ):
        enrollment.primeiro_acesso_em = (
            agora
        )

    enrollment.ultimo_acesso_em = (
        agora
    )

    db.flush()

    conteudos = (
        db.query(CourseContent)
        .filter(
            CourseContent.course_id
            == enrollment.course_id,

            CourseContent.ativo.is_(
                True
            ),
        )
        .all()
    )

    progressos = (
        db.query(ContentProgress)
        .filter(
            ContentProgress.enrollment_id
            == enrollment.id
        )
        .all()
    )

    progress_map = {
        item.content_id:
            item.progresso
        for item in progressos
    }

    if conteudos:
        progresso_total = (
            sum(
                progress_map.get(
                    item.id,
                    0,
                )
                for item in conteudos
            )
            / len(conteudos)
        )
    else:
        progresso_total = 0

    if enrollment.status == "Acesso suspenso":
        # Não altera status nem conclusão de matrícula suspensa (ver
        # open_course_content): a liberação depende do financeiro.
        pass

    elif progresso_total >= 100:
        enrollment.status = (
            "Concluído"
        )

        if (
            enrollment.concluido_em
            is None
        ):
            enrollment.concluido_em = (
                agora
            )

    else:
        enrollment.status = (
            "Em andamento"
        )

        enrollment.concluido_em = (
            None
        )

    db.commit()
    db.refresh(progresso)

    return {
        "content_id":
            content.id,

        "progresso":
            progresso.progresso,

        "progresso_curso":
            round(
                progresso_total,
                2,
            ),

        "status_curso":
            enrollment.status,
    }


# =========================================================
# LMS ANALYTICS
# =========================================================


@app.get("/api/lms-analytics")
def lms_analytics(
    current_user: User = Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    agora = datetime.now()

    limite_abandono = (
        agora
        - timedelta(
            days=7
        )
    )

    total_matriculas = (
        db.query(
            func.count(
                Enrollment.id
            )
        )
        .scalar()
        or 0
    )

    primeiro_acesso = (
        db.query(
            func.count(
                Enrollment.id
            )
        )
        .filter(
            Enrollment
            .primeiro_acesso_em
            .is_not(None)
        )
        .scalar()
        or 0
    )

    nunca_acessaram = (
        total_matriculas
        - primeiro_acesso
    )

    concluidos = (
        db.query(
            func.count(
                Enrollment.id
            )
        )
        .filter(
            Enrollment.status
            == "Concluído"
        )
        .scalar()
        or 0
    )

    em_andamento = (
        db.query(
            func.count(
                Enrollment.id
            )
        )
        .filter(
            Enrollment.status
            == "Em andamento"
        )
        .scalar()
        or 0
    )

    possivel_abandono = (
        db.query(
            func.count(
                Enrollment.id
            )
        )
        .filter(
            Enrollment
            .primeiro_acesso_em
            .is_not(None),

            Enrollment
            .ultimo_acesso_em
            < limite_abandono,

            Enrollment
            .concluido_em
            .is_(None),
        )
        .scalar()
        or 0
    )

    enrollments = (
        db.query(Enrollment)
        .all()
    )

    progressos = []

    for enrollment in enrollments:
        progresso = (
            calculate_enrollment_progress(
                db,
                enrollment.id,
                enrollment.course_id,
            )
        )

        progressos.append(
            progresso
        )

    progresso_medio = (
        round(
            sum(progressos)
            / len(progressos),
            2,
        )
        if progressos
        else 0.0
    )

    taxa_primeiro_acesso = (
        round(
            (
                primeiro_acesso
                / total_matriculas
            )
            * 100,
            2,
        )
        if total_matriculas > 0
        else 0.0
    )

    taxa_conclusao = (
        round(
            (
                concluidos
                / total_matriculas
            )
            * 100,
            2,
        )
        if total_matriculas > 0
        else 0.0
    )

    contents = (
        db.query(
            CourseContent,
            Course,
        )
        .join(
            Course,
            CourseContent.course_id
            == Course.id,
        )
        .filter(
            CourseContent.ativo.is_(
                True
            )
        )
        .order_by(
            Course.id.asc(),
            CourseContent.ordem.asc(),
        )
        .all()
    )

    por_conteudo = []

    for (
        content,
        course,
    ) in contents:
        matriculas_curso = (
            db.query(
                func.count(
                    Enrollment.id
                )
            )
            .filter(
                Enrollment.course_id
                == course.id
            )
            .scalar()
            or 0
        )

        aberturas = (
            db.query(
                func.count(
                    func.distinct(
                        ContentProgress
                        .enrollment_id
                    )
                )
            )
            .filter(
                ContentProgress.content_id
                == content.id,

                ContentProgress.aberto_em
                .is_not(None),
            )
            .scalar()
            or 0
        )

        conclusoes = (
            db.query(
                func.count(
                    func.distinct(
                        ContentProgress
                        .enrollment_id
                    )
                )
            )
            .filter(
                ContentProgress.content_id
                == content.id,

                ContentProgress.progresso
                == 100,
            )
            .scalar()
            or 0
        )

        progresso_conteudo = (
            db.query(
                func.avg(
                    ContentProgress
                    .progresso
                )
            )
            .filter(
                ContentProgress.content_id
                == content.id
            )
            .scalar()
        )

        progresso_conteudo = (
            round(
                float(
                    progresso_conteudo
                ),
                2,
            )
            if progresso_conteudo
            is not None
            else 0.0
        )

        taxa_abertura = (
            round(
                (
                    aberturas
                    / matriculas_curso
                )
                * 100,
                2,
            )
            if matriculas_curso > 0
            else 0.0
        )

        por_conteudo.append(
            {
                "content_id":
                    content.id,

                "course_id":
                    course.id,

                "curso":
                    course.nome,

                "titulo":
                    content.titulo,

                "tipo":
                    content.tipo,

                "ordem":
                    content.ordem,

                "matriculas":
                    matriculas_curso,

                "aberturas":
                    aberturas,

                "conclusoes":
                    conclusoes,

                "taxa_abertura":
                    taxa_abertura,

                "progresso_medio":
                    progresso_conteudo,
            }
        )

    return {
        "total_matriculas":
            total_matriculas,

        "acessos_liberados":
            total_matriculas,

        "primeiro_acesso":
            primeiro_acesso,

        "nunca_acessaram":
            nunca_acessaram,

        "em_andamento":
            em_andamento,

        "concluidos":
            concluidos,

        "possivel_abandono":
            possivel_abandono,

        "progresso_medio":
            progresso_medio,

        "taxa_primeiro_acesso":
            taxa_primeiro_acesso,

        "taxa_conclusao":
            taxa_conclusao,

        "por_conteudo":
            por_conteudo,
    }
# =========================================================
# FINANCEIRO COMERCIAL
# =========================================================


@app.get("/api/finance/summary")
def finance_summary(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    statuses = ["Pago", "Pendente", "Cancelado", "Reembolsado"]
    valores = {}
    quantidades = {}
    for status in statuses:
        valores[status] = float(
            db.query(func.coalesce(func.sum(Sale.valor_total), 0))
            .filter(Sale.status_pagamento == status)
            .scalar()
            or 0
        )
        quantidades[status] = (
            db.query(func.count(Sale.id))
            .filter(Sale.status_pagamento == status)
            .scalar()
            or 0
        )

    return {
        "receita_paga": valores["Pago"],
        "a_receber": valores["Pendente"],
        "reembolsado": valores["Reembolsado"],
        "cancelado": valores["Cancelado"],
        "quantidades": quantidades,
        "saldo_liquido": valores["Pago"] - valores["Reembolsado"],
    }


# =========================================================
# OMNICHANNEL / AUTOMAÇÕES
# =========================================================


@app.get("/api/omnichannel/summary")
def omnichannel_summary(
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Interaction.tipo, func.count(Interaction.id))
        .group_by(Interaction.tipo)
        .order_by(func.count(Interaction.id).desc())
        .all()
    )
    recent = (
        db.query(Interaction, Lead)
        .join(Lead, Interaction.lead_id == Lead.id)
        .order_by(Interaction.criado_em.desc())
        .limit(20)
        .all()
    )
    return {
        "por_canal": [{"canal": tipo, "total": total} for tipo, total in rows],
        "recentes": [
            {
                "interaction_id": interaction.id,
                "lead_id": lead.id,
                "lead_nome": lead.nome,
                "tipo": interaction.tipo,
                "resultado": interaction.resultado,
                "criado_em": interaction.criado_em,
            }
            for interaction, lead in recent
        ],
    }


@app.get("/api/automation/insights")
def automation_insights(
    current_user: User = Depends(require_roles("admin", "vendedor")),
    db: Session = Depends(get_db),
):
    agora = datetime.now()
    limite_inatividade = agora - timedelta(days=7)

    followups_interacoes_atrasados = (
        db.query(func.count(Interaction.id))
        .filter(
            Interaction.follow_up_em.is_not(None),
            Interaction.follow_up_em < agora,
        )
        .scalar()
        or 0
    )
    proximas_acoes_atrasadas = (
        db.query(func.count(Lead.id))
        .filter(
            Lead.proxima_acao_em.is_not(None),
            Lead.proxima_acao_em < agora,
            ~Lead.status.in_(CONVERTED_STATUSES | {"Perdido"}),
        )
        .scalar()
        or 0
    )
    followups_atrasados = followups_interacoes_atrasados + proximas_acoes_atrasadas

    leads_sem_interacao = (
        db.query(func.count(Lead.id))
        .outerjoin(Interaction, Interaction.lead_id == Lead.id)
        .filter(Interaction.id.is_(None), ~Lead.status.in_(CONVERTED_STATUSES | {"Perdido"}))
        .scalar()
        or 0
    )

    pagamentos_pendentes = (
        db.query(func.count(Sale.id))
        .filter(Sale.status_pagamento == "Pendente")
        .scalar()
        or 0
    )

    abandono_lms = (
        db.query(func.count(Enrollment.id))
        .filter(
            Enrollment.primeiro_acesso_em.is_not(None),
            Enrollment.ultimo_acesso_em < limite_inatividade,
            Enrollment.concluido_em.is_(None),
        )
        .scalar()
        or 0
    )

    alerts = []
    if followups_atrasados:
        alerts.append({"tipo": "followup", "prioridade": "alta", "titulo": "Ações comerciais atrasadas", "total": followups_atrasados, "acao": "Revisar follow-ups e próximas ações do CRM."})
    if leads_sem_interacao:
        alerts.append({"tipo": "lead", "prioridade": "media", "titulo": "Leads sem interação", "total": leads_sem_interacao, "acao": "Realizar o primeiro contato."})
    if pagamentos_pendentes:
        alerts.append({"tipo": "financeiro", "prioridade": "media", "titulo": "Pagamentos pendentes", "total": pagamentos_pendentes, "acao": "Verificar cobrança e condição comercial."})
    if abandono_lms:
        alerts.append({"tipo": "lms", "prioridade": "baixa", "titulo": "Possível abandono no LMS", "total": abandono_lms, "acao": "Planejar contato de engajamento."})

    return {"gerado_em": agora, "alerts": alerts}


# =========================================================
# GESTÃO DE USUÁRIOS
# =========================================================


@app.get("/api/users")
def list_users(
    current_user: User = Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            User,
            Lead,
        )
        .outerjoin(
            Lead,
            User.lead_id == Lead.id,
        )
        .order_by(
            User.id.asc()
        )
        .all()
    )

    return [
        {
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "role": user.role,
            "lead_id": user.lead_id,

            "lead_nome":
                lead.nome
                if lead
                else None,

            "ativo": user.ativo,

            "ultimo_login_em":
                user.ultimo_login_em,

            "criado_em":
                user.criado_em,
        }
        for user, lead in rows
    ]
@app.get("/api/admin/lead-options")
def user_lead_options(
    current_user: User = Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            Lead,
            User,
        )
        .outerjoin(
            User,
            User.lead_id == Lead.id,
        )
        .order_by(
            Lead.nome.asc()
        )
        .all()
    )

    return [
        {
            "id": lead.id,
            "nome": lead.nome,
            "status": lead.status,

            "user_id":
                user.id
                if user
                else None,

            "user_email":
                user.email
                if user
                else None,
        }
        for lead, user in rows
    ]
@app.post(
    "/api/users",
    status_code=201,
)
def create_user(
    data: UserCreate,

    current_user: User = Depends(
        require_roles("admin")
    ),

    db: Session = Depends(get_db),
):
    nome = data.nome.strip()

    email = (
        data.email
        .strip()
        .lower()
    )

    if not nome:
        raise HTTPException(
            status_code=400,
            detail="Nome é obrigatório.",
        )

    if len(data.senha) < 8:
        raise HTTPException(
            status_code=400,
            detail=(
                "A senha deve possuir "
                "pelo menos 8 caracteres."
            ),
        )

    existing_email = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe um usuário "
                "com este e-mail."
            ),
        )

    lead_id = (
        validate_user_role_and_lead(
            data.role,
            data.lead_id,
            db,
        )
    )

    novo_usuario = User(
        nome=nome,
        email=email,

        senha_hash=
            PASSWORD_HASHER.hash(
                data.senha
            ),

        role=data.role,
        lead_id=lead_id,
        ativo=data.ativo,
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {
        "id": novo_usuario.id,
        "nome": novo_usuario.nome,
        "email": novo_usuario.email,
        "role": novo_usuario.role,
        "lead_id": novo_usuario.lead_id,
        "ativo": novo_usuario.ativo,
    }


@app.put("/api/users/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    nome = data.nome.strip()
    email = data.email.strip().lower()

    if not nome:
        raise HTTPException(status_code=400, detail="Nome é obrigatório.")

    duplicate_email = (
        db.query(User)
        .filter(User.email == email, User.id != user.id)
        .first()
    )
    if duplicate_email:
        raise HTTPException(status_code=409, detail="Já existe outro usuário com este e-mail.")

    if user.id == current_user.id:
        if not data.ativo:
            raise HTTPException(status_code=400, detail="Você não pode desativar sua própria conta.")
        if data.role != "admin":
            raise HTTPException(
                status_code=400,
                detail="Você não pode remover seu próprio perfil de administrador.",
            )

    if user.role == "admin" and user.ativo and (data.role != "admin" or not data.ativo):
        admins_ativos = (
            db.query(func.count(User.id))
            .filter(User.role == "admin", User.ativo.is_(True))
            .scalar()
            or 0
        )
        if admins_ativos <= 1:
            raise HTTPException(
                status_code=400,
                detail="O sistema precisa manter pelo menos um administrador ativo.",
            )

    lead_id = validate_user_role_and_lead(
        data.role, data.lead_id, db, exclude_user_id=user.id
    )

    user.nome = nome
    user.email = email
    user.role = data.role
    user.lead_id = lead_id
    user.ativo = data.ativo

    if data.senha is not None and data.senha.strip():
        if len(data.senha) < 8:
            raise HTTPException(
                status_code=400,
                detail="A nova senha deve possuir pelo menos 8 caracteres.",
            )
        user.senha_hash = PASSWORD_HASHER.hash(data.senha)

    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "nome": user.nome,
        "email": user.email,
        "role": user.role,
        "lead_id": user.lead_id,
        "ativo": user.ativo,
    }
