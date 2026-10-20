"""Etapa 1: estado administrativo da Assistente Sara (sem DB ou LLM)."""
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/agent", tags=["Assistente Sara"])

# INTEGRAÇÃO: a rota é registrada em main.py com Depends(require_roles(...)).
@router.get("/status")
def status():
    return {
        "agent": "Assistente Sara",
        "status": "estrutura_inicial",
        "mode": "integracao_crm",
        "integrations": {"whatsapp": False, "llm": False, "database": False},
    }
