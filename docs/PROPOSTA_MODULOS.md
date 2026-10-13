# Proposta — compra individual de módulos (para aprovação, SEM migration)

Fato do modelo atual: o acesso é concedido **por `Course`** (`Enrollment` = lead + curso). `CourseContent` pertence a um curso e **não existe entidade comercial de módulo**. Nada foi alterado.

Oferta divulgada hoje (da landing atual): Curso Básico (R$19,90 lançamento) e Programa Completo (R$149,90 lançamento = Curso Básico + Curso Avançado). O site V6 passou a mostrar só isso e removeu "módulos individuais".

## Opções

**A. Curso/programa completo apenas (recomendada para o lançamento).** Cada oferta = um `Product` + um `Course`. Programa Completo pode ser um `Course` próprio ou conceder duas matrículas (Básico e Avançado) numa única venda.
- Prós: zero mudança de schema; usa N1–N4 como estão.
- Contras: não vende módulo avulso.
- Ponto aberto: Programa Completo como 1 curso ou 2 matrículas por venda (a segunda exige pequena regra nova, mas sem mudar tabelas).

**B. Compra individual = cada módulo vira um `Course` pequeno.** Sem mudar schema; o "programa" é um conjunto de cursos.
- Prós: sem migration; já funciona com `Enrollment` por curso.
- Contras: perde a noção de "curso com módulos" na UI; o Programa Completo precisa conceder N matrículas.

**C. Conjunto de conteúdos liberados (entitlement por conteúdo).** Nova tabela de relação (ex.: `product_contents`: produto → conteúdos) e checagem de acesso por conteúdo em vez de só por curso.
- Prós: máxima flexibilidade (módulo avulso, bônus, bundles).
- Contras: exige migration, muda `validate_enrollment_access`, `calculate_enrollment_progress` e os testes de RBAC/LMS; maior risco.

## Recomendação

Lançar com **A**. Só evoluir para B ou C se houver módulo avulso definido pela SARGTECH (nome, conteúdo, preço), o que ainda **não foi informado**. 

## Decisões que preciso de você

1. Programa Completo: um curso único ou Básico + Avançado como duas matrículas?
2. Haverá venda de módulo avulso no lançamento? Se sim, quais módulos e preços?
3. Aprovação da opção (A, B ou C) antes de qualquer migration.
