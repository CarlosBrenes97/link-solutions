# Link Solutions: plataforma de e-commerce con datos e IA

Proyecto II del curso IF-6201 (UCR). Una tienda en línea (nopCommerce) publicada en Azure, con un Data Warehouse que se
actualiza solo cada día, gráficos en Power BI y módulos de inteligencia artificial.

| Rol | Persona | Carpeta principal |
|---|---|---|
| CIO | Carlos Brenes González | `tienda/` |
| CDO | Karla Martínez Carmona | `datos/`, `bi/` |
| CAIO | María José Nájera Cervantes | `ia/` |

## Estructura

```
tienda/    nopCommerce: script para descargarlo y plugins propios (Carlos)
datos/
  sql/        scripts del almacén de datos
  generador/  datos de ejemplo (clientes, ventas, comentarios)
  etl/        ETL en Python y Azure Function programada
ia/        pronóstico de ventas y resumen de comentarios (María José)
bi/        reporte de Power BI (.pbix) y capturas
docs/      guía técnica (PDF), reparto y documento de propuesta
```

## Cómo empezar (cada persona, una vez)

1. Clonar el repo y copiar `.env.example` a `.env` (nunca se sube a Git).
2. Python 3.11 o superior y un entorno virtual:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows        (Linux o Mac: source .venv/bin/activate)
   pip install -r datos/generador/requirements.txt -r datos/etl/requirements.txt
   ```
3. Generar los datos de ejemplo:
   ```bash
   python datos/generador/generar_datos.py
   ```
4. Probar el ETL sin Azure, con una base SQLite temporal:
   ```bash
   # Windows PowerShell: $env:DATA_DIR="datos/generador/salida"
   DATA_DIR=datos/generador/salida python datos/etl/tests/test_etl_sqlite.py
   ```
   Debe terminar en `OK`.

La tienda se prepara aparte, ver `tienda/README.md`.

## Cómo trabajamos

Ver [`CONTRIBUTING.md`](CONTRIBUTING.md): una rama por historia de usuario, pull requests revisados por otra persona, sin
secretos en el repositorio.

## Documentación

- [`docs/Guia_Ecommerce_Link_Solutions.pdf`](docs/Guia_Ecommerce_Link_Solutions.pdf): qué hay que hacer y cómo.
- [`docs/reparto.md`](docs/reparto.md): quién hace qué en cada sprint.
- Tablero: Trello, «Link Solutions».

## Estado de las piezas

| Pieza | Estado |
|---|---|
| Generador de datos | Probado |
| ETL con CSV (SQLite de prueba) | Probado, es idempotente |
| ETL contra nopCommerce real | **Pendiente de verificar**: los nombres de tablas y columnas de `extraer_tienda` |
| Pronóstico | Probado con datos de ejemplo (error de backtest cercano al 12%) |
| Resumen de comentarios con LLM | Escrito, **sin probar**: necesita clave de API |
| Azure Function | Escrita, **sin desplegar** |
