# automatizacion_pcaps_proyecto

Automatizacion local para descargar, procesar y analizar capturas PCAP/PCAPNG C-ITS/V2X.

El flujo objetivo es:

```text
DS4MoveUS API -> PCAP -> pcap2db -> NDJSON -> ndjson2pg -> PostgreSQL -> analytics views -> Superset/Grafana
```

## Estructura

- `automation_pcaps/`: worker local, UI web, cliente API, estado SQLite y orquestacion del pipeline.
- `pcap2db/`: submodulo que convierte PCAP/PCAPNG a tablas NDJSON.
- `ndjson2pg/`: submodulo que carga las tablas NDJSON en PostgreSQL.
- `analytics/sql/`: vistas SQL comunes para dashboards.
- `analytics/superset/`: Superset local con Docker Compose.
- `analytics/grafana/`: guia de uso para Grafana.
- `analytics/docs/`: notas de validacion y decisiones.
- `figma_make_extract/`: referencias exportadas de diseno.

## Clonado y Submodulos

Clonar con submodulos:

```powershell
git clone --recurse-submodules https://github.com/acuerui/automatizacion_pcaps_proyecto.git
cd automatizacion_pcaps_proyecto
```

Si ya lo has clonado:

```powershell
git submodule update --init --recursive
```

Los submodulos quedan fijados a los commits registrados por este repo. Para revisar su estado:

```powershell
git submodule status --recursive
```

## Configuracion Local

No guardes secretos en git. Los ficheros locales sensibles estan ignorados:

- `analytics/superset/.env`
- `automation_pcaps/config.local.json`
- `ndjson2pg/.env`

Crear configuracion de automatizacion:

```powershell
Copy-Item automation_pcaps\config.example.json automation_pcaps\config.local.json
```

Configurar credenciales de API por variables de entorno:

```powershell
$env:DS4MOVEUS_USER="<usuario>"
$env:DS4MOVEUS_PASSWORD="<password>"
```

Si `ingest_to_postgres` esta activo, configura la conexion PostgreSQL en `ndjson2pg/.env` siguiendo el README del submodulo.

## Dependencias

Requisitos principales:

- Python 3.10+ recomendado.
- Wireshark/tshark disponible en PATH, o ruta configurada en `tshark_path`.
- Dependencias Python de `pcap2db`.
- Dependencias Python de `ndjson2pg`.
- Docker Desktop para Superset.
- Acceso al PostgreSQL V2X, normalmente via VPN.

Instalacion orientativa de dependencias de submodulos:

```powershell
pip install -r pcap2db\requirements.txt
pip install -r ndjson2pg\requirements.txt
```

## Arranque de Automatizacion

Desde la raiz del repo:

```powershell
python automation_pcaps\runner.py --config automation_pcaps\config.local.json
```

UI local:

```text
http://127.0.0.1:8088
```

Para levantar la UI con el worker parado:

```powershell
python automation_pcaps\runner.py --config automation_pcaps\config.local.json --no-start
```

## Analytics

Aplicar vistas SQL sobre el PostgreSQL donde `ndjson2pg` cargo los datos:

```powershell
psql "host=<host> port=5432 dbname=<db> user=<user>" -f analytics/sql/001_cits_dashboard_views.sql
```

Vistas principales:

- `vw_capture_summary`
- `vw_message_type_counts`
- `vw_station_summary`
- `vw_v2x_time_series`
- `vw_dataset_quality`
- `vw_pki_summary`
- `vw_geo_events`

## Superset Local

Desde `analytics/superset`:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

UI Superset:

```text
http://localhost:8088
```

Nota: Superset y la UI de `automation_pcaps` usan el puerto `8088` por defecto. Si necesitas ambos a la vez, cambia `SUPERSET_PORT` en `analytics/superset/.env` o `port` en `automation_pcaps/config.local.json`.

## Datos y Secretos

No versionar:

- `.env` con credenciales reales.
- `config.local.json`.
- PCAP/PCAPNG.
- NDJSON/JSONL generados.
- SQLite/local state.
- `__pycache__` y artefactos de entorno.

La politica actual esta en `.gitignore`.

## Documentacion Especifica

- `automation_pcaps/README.md`: funcionamiento del worker y UI.
- `analytics/README.md`: capa SQL comun para dashboards.
- `analytics/superset/README.md`: arranque y uso de Superset.
- `analytics/superset/V2X_END_TO_END_DASHBOARD.md`: blueprint del dashboard principal.
