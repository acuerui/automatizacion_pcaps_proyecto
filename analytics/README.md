# Analytics layer for C-ITS dashboards

Esta carpeta contiene la capa comun de datos para probar Superset y Grafana sobre la misma base PostgreSQL.

```text
PCAP -> automation_pcaps -> pcap2db -> ndjson2pg -> PostgreSQL -> analytics views -> Superset/Grafana
```

## Objetivo

Evitar duplicar logica en cada herramienta. Superset y Grafana deberian leer datasets/vistas ya preparados:

- `vw_capture_summary`
- `vw_message_type_counts`
- `vw_station_summary`
- `vw_v2x_time_series`
- `vw_dataset_quality`
- `vw_pki_summary`
- `vw_geo_events`

## Aplicar vistas

Con `psql`:

```powershell
psql "host=<host> port=5432 dbname=<db> user=<user>" -f analytics/sql/001_cits_dashboard_views.sql
```

O desde DBeaver/pgAdmin, abrir el fichero SQL y ejecutarlo en el schema objetivo.

Si usas un schema distinto a `public`, ejecuta primero:

```sql
SET search_path TO tu_schema;
```

## Uso recomendado

1. Crear las vistas en PostgreSQL.
2. Conectar Superset al mismo PostgreSQL.
3. Crear datasets de Superset a partir de las vistas.
4. Conectar Grafana al mismo PostgreSQL.
5. Replicar paneles usando las mismas vistas.

## Dashboards objetivo

### Dashboard Estacion

- Selector de captura/equipo.
- KPIs por estacion.
- Distribucion CAM/DENM/CPM/SPATEM/MAPEM/IVI.
- PKI firmado/no firmado.
- Eventos DENM y geolocalizacion CAM/CPM.

### Dashboard V2X End-to-End

- Estaciones detectadas.
- Mensajes totales.
- Validacion de mensajes.
- Frecuencia temporal.
- Latencia/jitter/PDR cuando haya correlacion TX/RX disponible.
- Matriz de comunicacion OBU/RSU.
- Incidencias.

## Nota sobre metricas avanzadas

PDR, latencia end-to-end y jitter requieren correlacion entre mensajes TX y RX. Con el esquema actual se puede preparar la base, pero para calcularlos con rigor necesitaremos una clave de correlacion fiable entre mensajes, por ejemplo:

- station_id origen/destino;
- generation_time;
- sequence_number cuando aplique;
- hash/payload normalizado;
- identificador de evento DENM;
- ventana temporal de matching.

