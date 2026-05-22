# Grafana plan

## Instalacion local rapida

```powershell
docker run -d `
  --name grafana `
  -p 3000:3000 `
  -v grafana-storage:/var/lib/grafana `
  grafana/grafana
```

Abrir:

```text
http://localhost:3000
```

Usuario inicial habitual:

```text
admin / admin
```

## Datasource

Crear datasource PostgreSQL apuntando a la misma base donde se han creado las vistas analytics.

## Dashboard operacional

Grafana encaja especialmente bien para:

- mensajes por segundo;
- errores por captura;
- estado de calidad OK/WARNING/FAIL;
- capturas procesadas en el tiempo;
- disponibilidad de Postgres/API;
- alertas.

## Variables

- `$capture_name`
- `$station_id`
- `$message_type`
- `$direction`

Ejemplo de variable `capture_name`:

```sql
SELECT DISTINCT capture_name FROM vw_capture_summary ORDER BY capture_name
```

