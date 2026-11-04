#!/usr/bin/env bash
# Descarga nopCommerce en tienda/nopCommerce y enlaza los plugins propios.
# Uso: ./setup_tienda.sh release-4.90.8      (ver las versiones con: git ls-remote --tags <repo> "release-*")
set -euo pipefail
VERSION="${1:-}"
[ -n "$VERSION" ] || { echo "Falta la versión. Ejemplo: $0 release-4.90.8"; exit 1; }
cd "$(dirname "$0")"
if [ -d nopCommerce ]; then echo "tienda/nopCommerce ya existe. Bórrala si quieres volver a descargar."; exit 1; fi
git clone --branch "$VERSION" --depth 1 https://github.com/nopSolutions/nopCommerce.git nopCommerce
rm -rf nopCommerce/.git
for p in plugins/*/; do
  [ -d "$p" ] || continue
  nombre="$(basename "$p")"
  rm -rf "nopCommerce/src/Plugins/$nombre"
  cp -r "$p" "nopCommerce/src/Plugins/$nombre"
  echo "Plugin copiado: $nombre (recordar agregarlo a la solución en Visual Studio)"
done
echo "Listo. Abrir tienda/nopCommerce/src/NopCommerce.sln"
