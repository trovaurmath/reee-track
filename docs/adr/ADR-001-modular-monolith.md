# ADR-001 — Adotar monólito modular

- Status: aceito
- Data: 2026-08-12

## Contexto

O projeto possui vários domínios, mas será mantido inicialmente por uma equipe pequena e precisa ser
simples de executar e compreender.

## Decisão

Adotar um único backend implantável, dividido por módulos de negócio e camadas internas.

## Consequências

Transações entre módulos permanecem simples e o ambiente exige menos infraestrutura. Limites de
módulos e adapters serão preservados para permitir extrações futuras quando houver necessidade real.

