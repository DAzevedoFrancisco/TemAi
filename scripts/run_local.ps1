# Inicia o servidor de desenvolvimento local.
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

if (-not (Test-Path ".venv")) {
    Write-Host "Ambiente virtual nao encontrado. Executa primeiro: .\scripts\setup_local.ps1" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path ".env")) {
    Write-Host "Ficheiro .env nao encontrado. Executa primeiro: .\scripts\setup_local.ps1" -ForegroundColor Yellow
    exit 1
}

& .\.venv\Scripts\python.exe manage.py runserver
