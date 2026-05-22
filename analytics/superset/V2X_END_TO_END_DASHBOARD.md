# V2X End-to-End dashboard blueprint

Este documento aterriza el dashboard de referencia de Figma Make sobre las vistas SQL ya validadas.

## Datasets

Registrar estos datasets desde Superset:

| Vista | Time column | Uso principal |
| --- | --- | --- |
| `vw_capture_summary` | `first_packet_timestamp` | KPIs globales por captura |
| `vw_message_type_counts` | `first_seen_at` | Distribucion de tipos CAM/DENM/CPM/SPATEM/MAPEM/IVI |
| `vw_station_summary` | `first_seen_at` | Tabla y ranking por estacion |
| `vw_v2x_time_series` | `bucket_second` | Frecuencia temporal |
| `vw_dataset_quality` | none | Estado OK/WARNING/FAIL por captura |
| `vw_pki_summary` | none | Ratio PKI firmado/no firmado |
| `vw_geo_events` | `packet_timestamp` | Mapa CAM/DENM/CPM |

## Filtros nativos

Crear filtros de dashboard:

- `capture_name`
- `station_id`
- `message_type`
- `direction`
- `geo_source`
- Time range usando `bucket_second` para series temporales y `packet_timestamp` para mapa.

## Layout recomendado

### 1. Resumen global

- Big Number: `SUM(packets_total)` desde `vw_capture_summary`.
- Big Number: `SUM(its_messages_total)` desde `vw_capture_summary`.
- Big Number: `SUM(stations_total)` desde `vw_capture_summary`.
- Big Number: `AVG(its_ratio_percent)` desde `vw_capture_summary`.
- Table pequena: `capture_name`, `quality_status`, `quality_warnings` desde `vw_dataset_quality`.

### 2. Trafico V2X temporal

- Time-series Bar Chart desde `vw_v2x_time_series`.
- Time column: `bucket_second`.
- Metric: `SUM(messages_total)`.
- Group by: `message_type`.
- Filtros: `capture_name`, `station_id`, `direction`, `message_type`.

### 3. Distribucion de mensajes

- Pie/Donut desde `vw_message_type_counts`.
- Dimension: `message_type`.
- Metric: `SUM(messages_total)`.
- Color consistente por tipo:
  - CAM: azul
  - DENM: rojo/ambar
  - CPM: verde
  - SPATEM/MAPEM/IVI: grises/teal

### 4. Estaciones y Tx/Rx

- Table desde `vw_station_summary`.
- Columnas: `capture_name`, `station_id`, `device_type`, `vendor`, `model`, `packets_total`, `its_messages_total`, `tx_messages_total`, `rx_messages_total`, `cam_total`, `denm_total`, `cpm_total`.
- Orden: `its_messages_total DESC`.
- Bar Chart opcional: `station_id` vs `SUM(its_messages_total)`, group by `device_type`.

### 5. PKI y calidad

- Donut desde `vw_pki_summary` usando `signed_messages_total` y `unsigned_messages_total`.
- Big Number: `AVG(signed_ratio_percent)`.
- Bar Chart: `capture_name` vs `signed_ratio_percent`.

### 6. Geolocalizacion

- Deck.gl Scatterplot o Map chart desde `vw_geo_events`.
- Latitude: `latitude`.
- Longitude: `longitude`.
- Time: `packet_timestamp`.
- Group/color: `geo_source`.
- Tooltip: `capture_name`, `message_type`, `station_id`, `direction`, `event_type`.

## Limitaciones actuales

PDR, latencia end-to-end y jitter requieren correlacion TX/RX fiable. En esta primera version se dejan como bloque futuro o KPI anotado, usando la capa actual para trafico, estaciones, PKI, calidad y geolocalizacion.
