"""2.1.0-rc.1 — limpeza controlada de dados de teste."""

import pytest

import data_cleanup
from database import SessionLocal
from models import Enrollment, Lead, Product, Sale, User


@pytest.fixture()
def world(client, admin_headers, create_lead, course_setup, make_user):
    """1 lead real com venda+matrícula, 1 lead de teste com venda+matrícula, 1 indeterminado."""
    real = create_lead(nome="Carlos Madison", email="carlos@real.com.br")
    test = create_lead(nome="Teste QA", email="qa@teste.local")
    unknown = create_lead(nome="Pessoa Qualquer", email="pessoa@empresa.com.br")
    for lead in (real, test):
        sale = client.post(
            "/api/sales",
            headers=admin_headers,
            json={"lead_id": lead["id"], "product_id": course_setup["product_id"], "forma_pagamento": "Pix"},
        )
        assert sale.status_code == 201, sale.text
        client.post(
            f"/api/leads/{lead['id']}/interactions",
            headers=admin_headers,
            json={"tipo": "Ligação", "descricao": "contato"},
        )
    _, test_user = make_user("aluno", "aluno@teste.local", lead_id=test["id"])
    return {"real": real["id"], "test": test["id"], "unknown": unknown["id"], "test_user": test_user["id"]}


def _count(model):
    with SessionLocal() as db:
        return db.query(model).count()


def test_name_matching_normalizes_accents_and_lists_homonyms(world, create_lead):
    create_lead(nome="Daniele Souza", email="d1@x.com")
    create_lead(nome="Daniéle", email="d2@x.com")
    with SessionLocal() as db:
        found = data_cleanup.name_candidates(db)
    assert len(found["Daniele"]) == 2
    assert [c["id"] for c in found["Carlos Madison"]] == [world["real"]]


def test_dry_run_changes_nothing_and_classifies(world):
    with SessionLocal() as db:
        before = data_cleanup.table_counts(db)
        report = data_cleanup.build_report(db, {world["real"]}, database_name="x")
        after = data_cleanup.table_counts(db)
    assert before == after
    classes = {item["id"]: item["classe"] for item in report["leads"]}
    assert classes[world["real"]] == data_cleanup.CLASS_REAL
    assert classes[world["test"]] == data_cleanup.CLASS_TEST
    assert classes[world["unknown"]] == data_cleanup.CLASS_UNDETERMINED
    user_classes = {u["email"]: u["classe"] for u in report["users"]}
    assert user_classes["admin@teste.local"] == data_cleanup.CLASS_ADMIN
    assert user_classes["aluno@teste.local"] == data_cleanup.CLASS_TEST
    assert report["aprovacao_modelo"]["lead_ids"] == [world["test"]]
    # Produto usado por venda de lead real é REAL por referência.
    assert report["products"][0]["classe"] == data_cleanup.CLASS_REAL
    assert "senha" not in str(report).lower().replace("senha_hash", "")


def test_execute_only_deletes_approved_ids_and_keeps_real_and_unknown(world):
    with SessionLocal() as db:
        outcome = data_cleanup.execute_cleanup(
            db,
            preserve_lead_ids={world["real"]},
            approved_lead_ids={world["test"]},
            approved_user_ids={world["test_user"]},
            commit=True,
        )
    assert outcome.committed
    with SessionLocal() as db:
        ids = {row[0] for row in db.query(Lead.id)}
        assert ids == {world["real"], world["unknown"]}
        assert db.query(User).filter(User.email == "admin@teste.local").count() == 1
        assert db.query(Sale).count() == 1
        assert db.query(Enrollment).count() == 1
        assert db.query(Product).count() == 1  # catálogo nunca é excluído por este script


def test_rehearsal_rolls_back(world):
    with SessionLocal() as db:
        outcome = data_cleanup.execute_cleanup(
            db,
            preserve_lead_ids={world["real"]},
            approved_lead_ids={world["test"]},
            approved_user_ids={world["test_user"]},
            commit=False,
        )
    assert not outcome.committed
    assert outcome.deleted["leads"] == 1
    assert _count(Lead) == 3


def test_refuses_to_delete_preserved_lead(world):
    with SessionLocal() as db, pytest.raises(data_cleanup.CleanupError):
        data_cleanup.execute_cleanup(
            db,
            preserve_lead_ids={world["real"]},
            approved_lead_ids={world["real"]},
            approved_user_ids=set(),
            commit=True,
        )
    assert _count(Lead) == 3


def test_refuses_without_preserve_ids_or_with_unknown_id(world):
    with SessionLocal() as db, pytest.raises(data_cleanup.CleanupError):
        data_cleanup.execute_cleanup(
            db, preserve_lead_ids=set(), approved_lead_ids={world["test"]}, approved_user_ids=set(), commit=True
        )
    with SessionLocal() as db, pytest.raises(data_cleanup.CleanupError):
        data_cleanup.execute_cleanup(
            db, preserve_lead_ids={99999}, approved_lead_ids={world["test"]}, approved_user_ids=set(), commit=True
        )
    assert _count(Lead) == 3


def test_refuses_to_delete_admin_user(world):
    with SessionLocal() as db:
        admin_id = db.query(User).filter(User.email == "admin@teste.local").one().id
        with pytest.raises(data_cleanup.CleanupError):
            data_cleanup.execute_cleanup(
                db,
                preserve_lead_ids={world["real"]},
                approved_lead_ids=set(),
                approved_user_ids={admin_id},
                commit=True,
            )


def test_lead_with_unapproved_linked_user_is_skipped(world):
    with SessionLocal() as db:
        outcome = data_cleanup.execute_cleanup(
            db,
            preserve_lead_ids={world["real"]},
            approved_lead_ids={world["test"]},
            approved_user_ids=set(),  # usuário vinculado NÃO aprovado
            commit=True,
        )
    assert outcome.deleted["leads"] == 0
    assert outcome.skipped and outcome.skipped[0]["lead_id"] == world["test"]
    assert _count(Lead) == 3


def test_test_markers_are_conservative():
    assert data_cleanup.looks_like_test("Teste Fulano", None)
    assert data_cleanup.looks_like_test("João", "joao@exemplo.com")
    assert not data_cleanup.looks_like_test("Renato Fonseca", "renato@fonseca.com.br")
    assert not data_cleanup.looks_like_test("Contestado Silva", "c@contest.com")
