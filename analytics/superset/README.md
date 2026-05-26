# Superset local para C-ITS/V2X

Esta carpeta levanta Apache Superset en local con Docker Compose.

Superset usa una base PostgreSQL interna solo para metadatos. Los datos V2X siguen viviendo en el PostgreSQL de la VPN.

## Arranque

Desde esta carpeta:

```powershell
cd analytics\superset
copy .env.example .env
docker compose up --build
```

Abrir:

```text
http://localhost:8088
```

Credenciales iniciales:

```text
usuario y password definidos en `.env`
```

Cambialas antes del primer arranque. No reutilices esas credenciales fuera de pruebas locales.

## Conectar PostgreSQL V2X

Con la VPN activa, crear una nueva conexion en Superset:

```text
Settings > Database Connections > + Database
```

Usar SQLAlchemy URI:

```text
postgresql+psycopg2://<user>:<password>@<host>:<port>/<database>
```

En `Advanced > Other > Schemas allowed for CSV upload`, no hace falta tocar nada para esta prueba.

Si el test de conexion falla:

- comprobar que la VPN esta conectada;
- comprobar que Docker Desktop puede alcanzar el host PostgreSQL V2X;
- probar desde Windows: `Test-NetConnection <host> -Port <port>`;
- revisar usuario/password en `ndjson2pg/.env`.

## Datasets

Crear un dataset por vista:

- `public.vw_capture_summary`
- `public.vw_message_type_counts`
- `public.vw_station_summary`
- `public.vw_v2x_time_series`
- `public.vw_dataset_quality`
- `public.vw_pki_summary`
- `public.vw_geo_events`

Ruta:

```text
Datasets > + Dataset
```

Seleccionar la base V2X, schema `public`, y la vista correspondiente.

Columnas temporales recomendadas:

- `vw_capture_summary`: `first_packet_timestamp`
- `vw_message_type_counts`: `first_seen_at`
- `vw_station_summary`: `first_seen_at`
- `vw_v2x_time_series`: `bucket_second`
- `vw_geo_events`: `packet_timestamp`

## Primer dashboard

Construir primero `V2X End-to-End`.

La guia de charts esta en:

```text
analytics/superset/V2X_END_TO_END_DASHBOARD.md
```

Paneles iniciales recomendados:

- Big Number: paquetes totales.
- Big Number: mensajes ITS totales.
- Big Number: estaciones detectadas.
- Time-series: mensajes por segundo por tipo.
- Donut: distribucion CAM/DENM/CPM/SPATEM/MAPEM/IVI.
- Table: rendimiento por estacion.
- Donut/Big Number: PKI firmado/no firmado.
- Map: eventos geolocalizados CAM/DENM/CPM.
- Table: calidad de dataset OK/WARNING/FAIL.

## Parada y limpieza

Parar contenedores:

```powershell
docker compose down
```

Eliminar tambien metadatos locales de Superset:

```powershell
docker compose down -v
```

No elimina datos V2X de PostgreSQL, solo el estado local de Superset.
