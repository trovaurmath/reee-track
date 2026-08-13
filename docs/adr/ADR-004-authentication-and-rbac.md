# ADR-004 — Autenticação local e RBAC centralizado

- Status: aceito
- Data: 2026-08-12

## Contexto

O MVP precisa funcionar sem provedor de identidade externo e não deve espalhar verificações de papéis
pelos endpoints.

## Decisão

Usar access token JWT curto, refresh token opaco rotativo e políticas baseadas em códigos de permissão.
Senhas são protegidas com Argon2id.

## Consequências

SSO poderá substituir a autenticação por adapter no futuro. A autorização continua independente do
método de login.

