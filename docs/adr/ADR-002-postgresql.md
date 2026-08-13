# ADR-002 — Usar PostgreSQL como banco principal

- Status: aceito
- Data: 2026-08-12

## Contexto

Rastreabilidade exige transações, integridade referencial, índices, JSON para metadados e consultas
analíticas.

## Decisão

Usar PostgreSQL em desenvolvimento compartilhado e produção, administrado por migrations Alembic.

## Consequências

O projeto ganha constraints e recursos adequados para busca e relatórios. Testes unitários podem usar
SQLite, mas comportamentos específicos precisam de testes de integração PostgreSQL.

