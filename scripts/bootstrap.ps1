$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    Write-Host "Arquivo .env criado. Revise as credenciais antes de uso fora do desenvolvimento."
}

docker compose up --build

