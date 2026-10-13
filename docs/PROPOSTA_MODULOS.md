# Oferta SargLab no lançamento — decisão registrada (Opção A)

Decisão (13/10/2026): **Opção A**. Nenhuma migration para módulos avulsos. Nenhuma venda de M0, M1, M2 etc.

## Ofertas iniciais
| Oferta | Preço de lançamento | O que concede |
|---|---|---|
| Curso Básico | R$ 19,90 | Matrícula no Curso Básico |
| Programa Completo | R$ 149,90 | Pacote: matrículas no Curso Básico **e** no Curso Avançado |

O Programa Completo é um **pacote**, não um terceiro curso com conteúdo duplicado. O Curso Avançado pode existir comercialmente depois, como upgrade/jornada específica; não recebe destaque na oferta inicial.

## Restrição do modelo atual
`Course.product_id` é 1:1 (um curso pertence a um produto). Portanto o produto "Programa Completo" não tem como apontar para dois cursos hoje. **Proibido** resolver isso com lógica hardcoded por nome ou ID de produto.

## Requisito para a etapa de pagamentos (antes de ativar checkout)
Relação explícita **produto → cursos concedidos**, por exemplo uma tabela pequena `product_course_grants` (`product_id`, `course_id`, unicidade do par). Regras:
- Venda paga de um produto concede/restaura **uma matrícula por curso do grant**, reutilizando a lógica existente de `Enrollment` (N1–N4).
- Produto sem linhas de grant mantém o comportamento atual (via `Course.product_id`), para não quebrar o que existe.
- Reembolso suspende apenas as matrículas dos cursos que não tenham outra venda paga que os conceda (estender `has_other_paid_sale_for_course` para considerar os grants).
- Os testes de RBAC/LMS existentes devem continuar passando; acrescentar testes do pacote.

**Esta tabela não foi criada.** Será proposta junto com a migration de pagamentos, para aprovação.
