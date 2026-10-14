# Script de diagnóstico de salud de Apify y Scraper para el Estudio RICK
# Ubicación: tools/check-scraper-health.ps1

$envFile = Join-Path $PSScriptRoot '..\.env'
if (-not (Test-Path $envFile)) {
    $envFile = "C:\Users\mgome\AppData\Local\hermes\profiles\rick\.env"
}

if (-not (Test-Path $envFile)) {
    Write-Output "ERROR: Archivo .env no encontrado en la raíz del proyecto ni en hermes."
    exit 1
}

$line = (Get-Content $envFile | Where-Object { $_ -match "^\s*APIFY_API_TOKEN\s*=" } | Select-Object -First 1)
if (-not $line) {
    Write-Output "ERROR: APIFY_API_TOKEN no configurado en .env ($envFile)"
    exit 1
}

$tok = (($line -split '=', 2)[1]).Trim().Trim('"').Trim("'")
try {
    $me = Invoke-RestMethod -Uri "https://api.apify.com/v2/users/me?token=$tok"
    $plan = $me.data.plan.tier
    $features = $me.data.effectivePlatformFeatures.ACTORS
    $monthly = Invoke-RestMethod -Uri "https://api.apify.com/v2/users/me/usage/monthly?token=$tok"
    $used = [math]::Round($monthly.data.totalUsageCreditsUsdBeforeVolumeDiscount, 4)
    $max = $me.data.plan.maxMonthlyUsageUsd
    
    Write-Output "=== ESTADO DE SALUD DEL SCRAPER ==="
    Write-Output "Usuario: $($me.data.username) ($($me.data.email))"
    Write-Output "Plan: $plan | Límite mensual: `$$max USD"
    Write-Output "Uso acumulado en el ciclo actual: `$$used USD"
    
    if ($features.isEnabled) {
        Write-Output "Estado: ACTIVO Y OPERATIVO (Listo para scrapear)"
    } else {
        Write-Output "Estado: BLOQUEADO (403)"
        Write-Output "Razón: $($features.disabledReason)"
        Write-Output "Acción requerida: Renovar token en .env o agregar `$5 de saldo en Apify"
    }
} catch {
    Write-Output "ERROR al conectar con Apify: $($_.Exception.Message)"
}
