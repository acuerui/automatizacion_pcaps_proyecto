# Avance Superset local para dashboard V2X

Fecha: 2026-05-21

## Resumen ejecutivo

Se ha dejado preparado un entorno local de Apache Superset con Docker para construir dashboards sobre los datos V2X ya cargados en PostgreSQL.

El flujo validado queda asi:

```text
PCAP/PCAPNG -> pcap2db -> NDJSON -> ndjson2pg -> PostgreSQL VPN -> analytics views -> Superset
```

Estado actual:

- Superset arranca correctamente en local con Docker Desktop.
- Se ha conectado Superset al PostgreSQL V2X accesible por VPN.
- Se ha creado el primer chart de validacion.
- Las vistas SQL de analytics ya estaban aplicadas y validadas previamente.
- Queda pendiente registrar todos los datasets y montar el dashboard `V2X End-to-End`.

## Objetivo

Construir un primer dashboard `V2X End-to-End` para analizar comunicaciones C-ITS/V2X a partir de capturas PCAP procesadas por la herramienta local.

El dashboard debe permitir:

- visualizar volumen total de paquetes y mensajes ITS;
- comparar capturas;
- analizar distribucion de tipos de mensaje;
- revisar actividad temporal;
- comparar estaciones;
- ver estado PKI firmado/no firmado;
- revisar calidad de datasets;
- visualizar eventos geolocalizados CAM/DENM/CPM.

## Componentes preparados

### Superset local

Se ha creado la carpeta:

```text
analytics/superset/
```

Archivos principales:

- `docker-compose.yml`: levanta Superset, PostgreSQL interno de metadatos y Redis.
- `Dockerfile`: extiende la imagen de Superset e instala el driver PostgreSQL.
- `.env.example`: plantilla de configuracion local.
- `superset_config.py`: configuracion de Superset para entorno local.
- `README.md`: pasos de instalacion, arranque y conexion.
- `V2X_END_TO_END_DASHBOARD.md`: blueprint del dashboard objetivo.

### Base de datos de negocio

Superset no almacena los datos V2X. Solo se conecta al PostgreSQL existente de la VPN:

```text
Host: 10.210.0.62
Port: 5432
Database: V2X
Schema: public
```

La URI SQLAlchemy usada en Superset es:

```text
postgresql+psycopg2://postgres:postgresql-password@10.210.0.62:5432/V2X
```

## Vistas analytics disponibles

Las vistas validadas en PostgreSQL son:

| Vista | Filas validadas | Uso |
| --- | ---: | --- |
| `vw_capture_summary` | 10 | Resumen por captura |
| `vw_message_type_counts` | 24 | Distribucion de tipos de mensaje |
| `vw_station_summary` | 17 | Resumen por estacion/equipo |
| `vw_v2x_time_series` | 8643 | Series temporales por segundo |
| `vw_dataset_quality` | 10 | Estado de calidad por captura |
| `vw_pki_summary` | 10 | Mensajes firmados/no firmados |
| `vw_geo_events` | 25327 | Eventos geolocalizados |

## Trabajo realizado hoy

1. Instalacion de Docker Desktop en Windows.
2. Activacion de WSL 2 como backend de Docker Desktop.
3. Creacion de configuracion Docker Compose para Superset.
4. Resolucion de problemas de arranque:
   - instalacion del driver `psycopg2-binary`;
   - correccion del comando de creacion del usuario administrador.
5. Arranque correcto de Superset en:

```text
http://localhost:8088
```

6. Acceso con usuario administrador local.
7. Conexion de Superset al PostgreSQL V2X de la VPN.
8. Creacion del primer chart de prueba.

## Pasos reproducibles

Desde PowerShell:

```powershell
cd "C:\Users\AlexCue\OneDrive - Cluster MLC ITS Euskadi\Escritorio\automatizacion_pcaps_proyecto\analytics\superset"
copy .env.example .env
docker compose up --build
```

Abrir:

```text
http://localhost:8088
```

Credenciales locales por defecto:

```text
admin / admin
```

Comprobar acceso a PostgreSQL con VPN activa:

```powershell
Test-NetConnection 10.210.0.62 -Port 5432
```

## Siguiente trabajo

### Paso 1: registrar datasets

Crear en Superset un dataset para cada vista:

- `public.vw_capture_summary`
- `public.vw_message_type_counts`
- `public.vw_station_summary`
- `public.vw_v2x_time_series`
- `public.vw_dataset_quality`
- `public.vw_pki_summary`
- `public.vw_geo_events`

### Paso 2: crear charts base

Charts iniciales recomendados:

- Big Number: mensajes ITS totales.
- Big Number: paquetes totales.
- Big Number: estaciones detectadas.
- Time-series: mensajes por segundo por tipo.
- Donut: distribucion CAM/DENM/CPM/SPATEM/MAPEM/IVI.
- Table: rendimiento por estacion.
- Donut/Big Number: PKI firmado/no firmado.
- Map: eventos geolocalizados.
- Table: calidad OK/WARNING/FAIL.

### Paso 3: montar dashboard

Crear dashboard:

```text
V2X End-to-End
```

Usar como referencia funcional:

```text
figma_make_extract/V2X_Communication_Analysis_Dashboard_make_ai_chat.json
figma_make_extract/Dashboard_Estacion_make_ai_chat.json
```

## Limitaciones identificadas

Las metricas avanzadas de latencia end-to-end, jitter y Packet Delivery Ratio requieren correlacion fiable entre mensajes TX y RX.

Actualmente la capa analytics permite visualizar trafico, estaciones, tipos de mensaje, PKI, calidad y eventos geolocalizados. Para calcular PDR/latencia/jitter con rigor se necesitara una clave de correlacion, por ejemplo:

- `station_id` origen/destino;
- `generation_time`;
- numero de secuencia cuando exista;
- hash/payload normalizado;
- identificador de evento DENM;
- ventana temporal de matching.

## Entregables actuales

- Entorno Superset local funcional.
- Conexion a PostgreSQL V2X realizada.
- Primer chart creado.
- Documentacion tecnica en `analytics/superset/README.md`.
- Blueprint de dashboard en `analytics/superset/V2X_END_TO_END_DASHBOARD.md`.
- Esta nota de avance para seguimiento.
