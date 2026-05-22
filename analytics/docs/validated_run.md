# Validated analytics run

Fecha de validacion: 2026-05-21

Las vistas de `analytics/sql/001_cits_dashboard_views.sql` se han aplicado correctamente en PostgreSQL usando la configuracion de `ndjson2pg/.env`.

Resultado de conteos:

```text
vw_capture_summary: 10 rows
vw_message_type_counts: 24 rows
vw_station_summary: 17 rows
vw_v2x_time_series: 8643 rows
vw_dataset_quality: 10 rows
vw_pki_summary: 10 rows
vw_geo_events: 25327 rows
```

Estas vistas ya pueden registrarse como datasets en Superset o usarse como tablas de consulta en Grafana.

## Siguiente paso recomendado

1. Levantar Superset local con Docker.
2. Conectarlo al PostgreSQL de la VPN.
3. Crear datasets desde las vistas.
4. Construir el dashboard `V2X End-to-End` primero.
5. Replicar version operacional en Grafana.

