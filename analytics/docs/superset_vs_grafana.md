# Superset vs Grafana para C-ITS

## Enfoque recomendado

Usar la misma capa SQL comun para ambos:

```text
PostgreSQL tables -> analytics views -> Superset
                                  -> Grafana
```

## Superset

Mejor para:

- analisis BI;
- exploracion SQL;
- dashboards de negocio/datos;
- filtros ricos;
- tablas y mapas;
- usuarios no tecnicos.

## Grafana

Mejor para:

- observabilidad;
- series temporales;
- operacion;
- alertas;
- integracion futura con Prometheus/Kafka/Airflow;
- dashboards tecnicos.

## Reparto sugerido

Superset:

- Dashboard Estacion.
- Dashboard V2X End-to-End.
- Calidad de dataset.
- Analisis de mensajes y geolocalizacion.

Grafana:

- Estado del pipeline.
- Throughput de mensajes.
- Alertas de fallos.
- Disponibilidad API/Postgres.
- Monitorizacion operacional.

