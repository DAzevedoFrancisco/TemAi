# Inicia o servidor acessivel na rede local (ex.: telemovel no hotspot).
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

if (-not (Test-Path '.venv')) {
    Write-Host 'Ambiente virtual nao encontrado. Executa primeiro: .\scripts\setup_local.ps1' -ForegroundColor Yellow
    exit 1
}

$ip = (
    Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object {
        $_.InterfaceAlias -match 'Wi-Fi|Wireless' -and
        $_.IPAddress -notmatch '^(127\.|169\.254\.)'
    } |
    Select-Object -First 1 -ExpandProperty IPAddress
)

if (-not $ip) {
    $ip = (
        Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -notmatch '^(127\.|169\.254\.)' } |
        Select-Object -First 1 -ExpandProperty IPAddress
    )
}

if (-not $ip) {
    Write-Host 'Nao foi possivel detetar o IP local. Usa ipconfig.' -ForegroundColor Yellow
    $ip = 'SEU_IP_AQUI'
}

Write-Host ''
Write-Host '==> Mob - servidor na rede local' -ForegroundColor Cyan
Write-Host "No telemovel, abre: http://${ip}:8000/"
Write-Host ''
Write-Host 'Se nao abrir, permite a porta 8000 no Firewall do Windows.'
Write-Host ''

& .\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
