# Publicação e execução pelo GitHub

## 1. Criar o repositório

No GitHub, crie um repositório vazio chamado `reee-track`. Não adicione README, licença nem
`.gitignore` pela interface, pois esses arquivos já existem no projeto. Escolha `Private` enquanto
credenciais, dados ou regras institucionais estiverem em avaliação; torne público somente quando
isso estiver aprovado.

## 2. Enviar o projeto

Configure sua identidade Git com o mesmo nome e e-mail usados no GitHub. Na raiz do projeto,
execute (o `git init` também permite publicar a partir do ZIP):

```bash
git config --global user.name "SEU_NOME"
git config --global user.email "SEU_EMAIL_DO_GITHUB"
git init --initial-branch=main
git add .
git commit -m "feat: disponibiliza REEE-Track 0.5.0"
git remote add origin https://github.com/SEU_USUARIO/reee-track.git
git push -u origin main
```

Se `origin` já existir, confira antes de alterá-lo:

```bash
git remote -v
git remote set-url origin https://github.com/SEU_USUARIO/reee-track.git
git push -u origin main
```

Autentique-se pelo navegador ou use um personal access token. Nunca grave o token no `.env`, em
scripts ou no próprio repositório.

## 3. Clonar e executar em outra máquina

```bash
git clone https://github.com/SEU_USUARIO/reee-track.git
cd reee-track
cp .env.example .env
docker compose up --build
```

No PowerShell, use `Copy-Item .env.example .env`. Depois acesse:

- aplicação: <http://localhost:3000>;
- API: <http://localhost:8000>;
- documentação Swagger: <http://localhost:8000/docs>.

Antes de compartilhar um ambiente real, troque todas as senhas e segredos do `.env`. Em produção,
use `ENVIRONMENT=production`, `SEED_DEMO_DATA=false`, uma URL HTTPS em `PUBLIC_FRONTEND_URL` e
origens explícitas em `CORS_ORIGINS`.

## 4. Validar alterações antes do envio

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check .
pytest

cd ../frontend
pnpm install --frozen-lockfile
pnpm lint
pnpm test -- --run
pnpm build

cd ..
docker compose build
```

O GitHub Actions repete as migrations, os seeds e as suítes backend/frontend a cada `push` e
`pull_request`.

## 5. Fluxo de atualização

```bash
git switch -c feat/nome-da-mudanca
git add .
git commit -m "feat: descreva a mudança"
git push -u origin feat/nome-da-mudanca
```

Abra um pull request no GitHub e só integre a mudança quando o workflow `CI` estiver aprovado.
