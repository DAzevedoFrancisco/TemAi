# Configura o ambiente local do Mob/TemAi (Windows / PowerShell).
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

Write-Host "==> Mob — setup local" -ForegroundColor Cyan

if (-not (Test-Path ".venv")) {
    Write-Host "Criando ambiente virtual (.venv)..."
    python -m venv .venv
}

Write-Host "Instalando dependencias..."
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -r requirements.txt

if (-not (Test-Path ".env")) {
    Write-Host "Criando .env a partir de .env.example..."
    Copy-Item ".env.example" ".env"
    Write-Host "Ajusta DB_PASSWORD e outras variaveis em .env se necessario."
}

Write-Host "Criando base de dados e aplicando migracoes..."
& .\.venv\Scripts\python.exe manage.py setup_database

Write-Host ""
Write-Host "Setup concluido." -ForegroundColor Green
Write-Host "Para iniciar: .\scripts\run_local.ps1"
Write-Host "URL: http://127.0.0.1:8000/"
