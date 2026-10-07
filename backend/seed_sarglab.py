"""Seed opcional do contexto comercial atual do SargLab.

Uso:
    python seed_sarglab.py

Não cria usuários nem credenciais. O primeiro admin continua sendo criado por
POST /api/auth/bootstrap-admin.
"""

from decimal import Decimal

from database import SessionLocal
from models import Campaign, Course, CourseContent, Product


def get_or_create_product(db, nome: str, preco: Decimal, descricao: str):
    item = db.query(Product).filter(Product.nome == nome).first()
    if item:
        return item
    item = Product(nome=nome, preco=preco, descricao=descricao, ativo=True)
    db.add(item)
    db.flush()
    return item


def main():
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.nome == "SargLab — Lançamento Instagram").first()
        if not campaign:
            db.add(Campaign(
                nome="SargLab — Lançamento Instagram",
                canal="Instagram",
                descricao="Campanha de lançamento e captura de leads via @sarglab.ia.",
                custo=Decimal("0"),
                ativo=True,
                utm_source="instagram",
                utm_medium="social",
                utm_campaign="sarglab_lancamento",
            ))

        online = get_or_create_product(
            db,
            "SargLab — IA no Dia a Dia | Turma aberta online",
            Decimal("147.00"),
            "Workshop prático de 2 horas, cerca de 80% prática. Faixas comerciais históricas do lançamento: piloto R$ 47, lançamento R$ 97 e preço cheio R$ 147.",
        )
        get_or_create_product(
            db,
            "SargLab — IA no Dia a Dia | Presencial",
            Decimal("197.00"),
            "Workshop presencial. Faixa comercial de referência: R$ 197 a R$ 297 por participante/turma conforme configuração.",
        )
        get_or_create_product(
            db,
            "SargLab — IA no Trabalho | Piloto B2B",
            Decimal("1200.00"),
            "Piloto corporativo para PMEs. Faixa sugerida: R$ 1.200 a R$ 1.600; condição-base: 50% na confirmação e 50% até o workshop.",
        )

        course = db.query(Course).filter(Course.product_id == online.id).first()
        if not course:
            course = Course(
                product_id=online.id,
                nome="SargLab — IA no Dia a Dia",
                descricao="Trilha de apoio ao workshop com Método CLARO, segurança e aplicação prática.",
                ativo=True,
            )
            db.add(course)
            db.flush()

        default_contents = [
            (1, "Abertura e diagnóstico", "material", 8),
            (2, "IA no dia a dia: o que é e o que não é", "video", 12),
            (3, "Método CLARO", "video", 25),
            (4, "Segurança, privacidade e validação", "video", 20),
            (5, "Exercícios práticos por contexto de trabalho", "material", 45),
            (6, "Plano de aplicação e próximos 7 dias", "material", 10),
        ]
        for ordem, titulo, tipo, duracao in default_contents:
            exists = db.query(CourseContent).filter(
                CourseContent.course_id == course.id,
                CourseContent.ordem == ordem,
            ).first()
            if not exists:
                db.add(CourseContent(
                    course_id=course.id,
                    titulo=titulo,
                    tipo=tipo,
                    ordem=ordem,
                    duracao_minutos=duracao,
                    descricao=None,
                    url_conteudo=None,
                    ativo=True,
                ))

        db.commit()
        print("Seed SargLab concluído.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
