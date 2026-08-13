# Como contribuir

## Preparação

1. Crie uma branch a partir da branch principal.
2. Copie `.env.example` para `.env`.
3. Suba o ambiente com `docker compose up --build`.
4. Verifique os health checks antes de alterar o código.

## Organização do código

- endpoints apenas validam o protocolo HTTP e chamam casos de uso;
- regras de negócio ficam no domínio ou nos services;
- consultas SQLAlchemy ficam nos repositories;
- autorização usa `require_permissions` e códigos centralizados;
- toda mudança de banco exige migration Alembic;
- segredos nunca devem ser commitados.

## Qualidade

Antes de abrir uma contribuição:

```bash
cd backend
ruff check .
pytest

cd ../frontend
pnpm lint
pnpm test -- --run
pnpm build
```

Adicione testes para regras novas, especialmente transições de estado, permissões, auditoria e
integridade do histórico.

## Commits

Use Conventional Commits:

```text
feat: add equipment registration
fix: reject invalid workflow transition
test: cover auditor permissions
docs: update local setup
refactor: extract authentication service
```

## Pull requests

Descreva:

- problema resolvido;
- abordagem adotada;
- migrations incluídas;
- testes executados;
- riscos ou decisões que precisam de revisão.

Atualize `PROJECT_STATE.md` e crie um ADR quando a alteração modificar uma decisão estrutural.

