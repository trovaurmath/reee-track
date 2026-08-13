# REEE-Track

Framework modular para rastreabilidade e gestão do descarte de resíduos de equipamentos
eletroeletrônicos. O projeto acompanha cada equipamento desde o recolhimento até a destinação
final, preservando histórico operacional e auditoria.

## 1. Descrição

A versão `0.5.0` acrescenta gestão operacional completa do inventário e armazenamento temporário.
Equipamentos podem ser criados, editados e excluídos com preservação do histórico; depósitos,
estantes, prateleiras e posições possuem capacidade controlada e operações de entrada,
transferência e saída. Permanência acima de 30 dias gera alerta, e todas as mudanças integram a
linha do tempo e a auditoria.

## 2. Objetivo

Substituir registros descentralizados e planilhas paralelas por uma fonte única, auditável e
extensível para o ciclo de descarte de equipamentos eletroeletrônicos.

## 3. Arquitetura

O REEE-Track é um monólito modular. Cada módulo concentra API, casos de uso, regras de domínio e
persistência. A separação permite evolução independente sem a carga operacional de microsserviços.

```text
React → REST API → Application Services → Domain Rules → Repositories → PostgreSQL
```

Consulte [docs/architecture/overview.md](docs/architecture/overview.md) e os registros em
`docs/adr/`.

## 4. Tecnologias

- Python, FastAPI, Pydantic, SQLAlchemy e Alembic;
- PostgreSQL;
- React, TypeScript, Vite e Material UI;
- pytest, Vitest e Testing Library;
- Docker e Docker Compose;
- OpenAPI/Swagger em `/docs`.

## 5. Requisitos

Para a execução recomendada:

- Docker com o plugin Docker Compose;
- portas `3000` e `8000` disponíveis.

Para desenvolvimento sem Docker:

- Python 3.12 ou superior compatível;
- Node.js 22 e pnpm;
- PostgreSQL.

## 6. Instalação

```bash
git clone URL_DO_REPOSITORIO
cd reee-track
cp .env.example .env
docker compose up --build
```

No PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Antes de qualquer implantação real, substitua `JWT_SECRET_KEY`, `POSTGRES_PASSWORD` e
`INITIAL_ADMIN_PASSWORD` no `.env`.

## 7. Configuração

As configurações são lidas exclusivamente de variáveis de ambiente. O `.env.example` documenta
todos os valores necessários e não contém credenciais reais.

Variáveis principais:

| Variável | Finalidade |
|---|---|
| `DATABASE_URL` | Conexão SQLAlchemy |
| `JWT_SECRET_KEY` | Assinatura dos access tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duração do access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Duração máxima da sessão renovável |
| `CORS_ORIGINS` | Origens autorizadas |
| `INITIAL_ADMIN_*` | Administrador criado pelo seed idempotente |
| `PUBLIC_FRONTEND_URL` | URL usada no QR Code de rastreabilidade |
| `SEED_DEMO_DATA` | Cria os 20 equipamentos fictícios na inicialização |

O backend recusa segredos de desenvolvimento e dados demonstrativos quando
`ENVIRONMENT=production`. Nesse ambiente, use `SEED_DEMO_DATA=false`.

## 8. Execução

O Docker Compose inicia, nesta ordem:

1. PostgreSQL e seu health check;
2. backend, migrations, seed de RBAC e, quando habilitado, seed demonstrativo;
3. frontend com proxy para a API.

Serviços disponíveis:

- aplicação: <http://localhost:3000>;
- API: <http://localhost:8000>;
- Swagger: <http://localhost:8000/docs>;
- readiness: <http://localhost:8000/api/v1/health/ready>.

### Hospedagem temporária no Render

O arquivo `render.yaml` prepara a aplicação para execução independente do
computador local, com frontend estático, API FastAPI e PostgreSQL persistente.

1. Acesse <https://dashboard.render.com/blueprints> e conecte a conta do GitHub.
2. Crie um Blueprint usando o repositório `trovaurmath/reee-track`.
3. Informe uma senha forte em `INITIAL_ADMIN_PASSWORD` quando solicitado.
4. Confirme a criação dos recursos gratuitos.
5. Aguarde os três recursos ficarem disponíveis e abra a URL de `reee-track-web`.

O serviço usa os planos gratuitos para demonstrações temporárias. A API pode
suspender após 15 minutos sem tráfego e voltar a responder no primeiro acesso.
O banco PostgreSQL gratuito expira 30 dias após a criação. Novos commits
aprovados pelo CI geram uma nova implantação automaticamente.

As credenciais iniciais são lidas do `.env`. Nos valores de demonstração:

```text
usuário: admin
senha: change-this-password
```

## 9. Banco de dados

As migrations ficam em `backend/migrations/versions`. O entrypoint executa `alembic upgrade head`
antes de iniciar a API.

Comandos manuais:

```bash
docker compose run --rm backend alembic current
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python -m app.cli seed-rbac
docker compose run --rm backend python -m app.cli seed-demo
```

Os seeds podem ser executados repetidamente. O primeiro atualiza os cinco papéis de sistema; o
segundo preserva os catálogos e equipamentos já criados e completa apenas os dados ausentes.

## 10. API

Principais endpoints implementados até a V0.5:

```text
GET  /api/v1/health/live
GET  /api/v1/health/ready
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
GET  /api/v1/users
POST /api/v1/users
GET  /api/v1/roles
GET  /api/v1/audit-logs
GET  /api/v1/catalogs/equipment
GET  /api/v1/equipments
POST /api/v1/equipments
GET  /api/v1/equipments/{tracking_code}
PATCH /api/v1/equipments/{tracking_code}
DELETE /api/v1/equipments/{equipment_id}
GET  /api/v1/equipments/{tracking_code}/timeline
GET  /api/v1/equipments/{tracking_code}/qr-code
GET  /api/v1/equipments/{tracking_code}/label
GET  /api/v1/equipments/{equipment_id}/workflow-options
POST /api/v1/equipments/{equipment_id}/transitions
POST /api/v1/equipments/{equipment_id}/timeline-notes
GET  /api/v1/traceability/events
GET  /api/v1/storage/dashboard
GET  /api/v1/storage/locations
POST /api/v1/storage/locations
PATCH /api/v1/storage/locations/{location_id}
DELETE /api/v1/storage/locations/{location_id}
GET  /api/v1/storage/occupancies
GET  /api/v1/storage/movements
POST /api/v1/storage/movements
GET  /api/v1/triages/queue
POST /api/v1/equipments/{tracking_code}/triages
GET  /api/v1/triages/{triage_id}
PUT  /api/v1/triages/{triage_id}/answers
POST /api/v1/triages/{triage_id}/complete
POST /api/v1/triages/{triage_id}/cancel
GET  /api/v1/triage-config/criteria
POST /api/v1/triage-config/criteria
GET  /api/v1/triage-config/classifications
```

O login segue `application/x-www-form-urlencoded`, permitindo uso direto do botão Authorize no
Swagger. O access token fica somente em memória no frontend. O refresh token fica em cookie
`HttpOnly`, é armazenado como hash no banco e rotacionado a cada renovação.

## 11. Testes

Backend:

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -e ".[dev]"
pytest
ruff check .
```

Frontend:

```bash
cd frontend
pnpm install
pnpm test -- --run
pnpm build
```

Os testes backend usam SQLite isolado para feedback rápido. O pipeline também executa todas as
migrations e os dois seeds em PostgreSQL antes da suíte automatizada.

## 12. Estrutura das pastas

```text
backend/       API, domínio, migrations, seed e testes
frontend/      aplicação React e testes de interface
docs/          arquitetura e decisões arquiteturais
scripts/       inicialização, migrations, seed e testes
storage/       ponto local ignorado para arquivos de desenvolvimento
```

## 13. Como contribuir

Consulte [CONTRIBUTING.md](CONTRIBUTING.md). O projeto utiliza Conventional Commits e exige testes
para regras de negócio e autorização.

Para publicar, clonar e atualizar o projeto pelo GitHub, consulte
[docs/GITHUB.md](docs/GITHUB.md).

## 14. Roadmap

- `V0.1`: infraestrutura, banco, autenticação e RBAC — concluída;
- `V0.2`: cadastro, busca, QR Code, etiqueta e seed de equipamentos — concluída;
- `V0.3`: triagem, classificação configurável e layout operacional — concluída;
- `V0.4`: workflow, eventos, notas e timeline consolidada — concluída;
- `V0.5`: CRUD do inventário, armazenamento e movimentação — concluída;
- `V0.6`: destinação, empresas, documentos e remessas;
- `V0.7`: dashboard e KPIs;
- `V0.8`: importação e exportação;
- `V0.9`: auditoria ampliada, segurança e testes;
- `V1.0`: MVP estável e documentado.

O estado detalhado está em [PROJECT_STATE.md](PROJECT_STATE.md).
