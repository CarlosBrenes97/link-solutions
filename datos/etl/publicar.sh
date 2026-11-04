#!/usr/bin/env bash
# Publica la Azure Function. Copia ia/ junto al código para que el ETL pueda importarla.
# Uso:  ./publicar.sh NOMBRE-DE-LA-FUNCTION-APP
set -euo pipefail
[ $# -eq 1 ] || { echo "Uso: $0 NOMBRE-DE-LA-FUNCTION-APP"; exit 1; }
cd "$(dirname "$0")"
rm -rf ia && cp -r ../../ia ./ia
func azure functionapp publish "$1" --python
rm -rf ia
