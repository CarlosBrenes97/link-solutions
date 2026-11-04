# Descarga nopCommerce en tienda\nopCommerce y copia los plugins propios.
# Uso: .\setup_tienda.ps1 -Version release-4.90.8
param([Parameter(Mandatory = $true)][string]$Version)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (Test-Path "nopCommerce") { Write-Error "tienda\nopCommerce ya existe. Bórrala si quieres volver a descargar."; exit 1 }
git clone --branch $Version --depth 1 https://github.com/nopSolutions/nopCommerce.git nopCommerce
Remove-Item -Recurse -Force "nopCommerce\.git"
Get-ChildItem -Directory "plugins" -ErrorAction SilentlyContinue | ForEach-Object {
  $destino = "nopCommerce\src\Plugins\$($_.Name)"
  if (Test-Path $destino) { Remove-Item -Recurse -Force $destino }
  Copy-Item -Recurse $_.FullName $destino
  Write-Host "Plugin copiado: $($_.Name) (agregarlo a la solución en Visual Studio)"
}
Write-Host "Listo. Abrir tienda\nopCommerce\src\NopCommerce.sln"
