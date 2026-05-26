# PCAP automation local

Simulador local del flujo:

```text
DS4MoveUS API -> descargar PCAP -> pcap2db -> ndjson2pg -> PostgreSQL
```

Incluye una interfaz web local para ver estados, errores y logs.

## 1. Configuracion

Copia el ejemplo:

```powershell
Copy-Item automation_pcaps\config.example.json automation_pcaps\config.local.json
```

Edita `automation_pcaps\config.local.json` si necesitas cambiar rutas.

Variables necesarias para login:

```powershell
$env:DS4MOVEUS_USER="tu_usuario"
$env:DS4MOVEUS_PASSWORD="tu_password"
```

No guardes credenciales reales dentro del JSON.

## 2. Requisitos

- Python.
- `tshark` instalado y disponible en PATH, o configurar `tshark_path`.
- Submodulos `pcap2db` y `ndjson2pg` inicializados.
- Dependencias de `pcap2db`.
- Dependencias de `ndjson2pg`.
- Variables `.env` de PostgreSQL dentro de `ndjson2pg` si `ingest_to_postgres` esta en `true`.

Si has clonado el repo sin submodulos:

```powershell
git submodule update --init --recursive
```

## 3. Arranque

Desde este repo:

```powershell
python automation_pcaps\runner.py --config automation_pcaps\config.local.json
```

Abre:

```text
http://127.0.0.1:8088
```

Si no has definido `DS4MOVEUS_USER` y `DS4MOVEUS_PASSWORD`, la web mostrara un formulario para introducir credenciales. Se guardan solo en memoria mientras el proceso este abierto.

El worker arranca automaticamente. Para abrir la web con el worker parado:

```powershell
python automation_pcaps\runner.py --config automation_pcaps\config.local.json --no-start
```

## 4. Como funciona

1. Hace login en `POST /auth/login`.
2. Lista datasets en `GET /datasets/available`.
3. Registra datasets nuevos en SQLite.
4. Descarga cada PCAP con `GET /datasets/download?url_artifact=...`.
5. Guarda el PCAP en `<workspace>/pcaps/raw`.
6. Ejecuta:

```powershell
python -m pcap2db run --workspace <workspace> --in <pcap>
```

7. Si `ingest_to_postgres` es `true`, ejecuta:

```powershell
python ndjson2pg.py --session-dir <workspace>/out/<vendor>/sessions/<capture>
```

## 5. Estado

El estado queda en `state_db_path`, por defecto:

```text
C:/pcap_workspace/automation_state.sqlite3
```

Estados principales:

```text
detected -> downloading -> downloaded -> transforming -> transformed -> loading_pg -> loaded
```

Si algo falla, pasa a `failed` y el panel permite reintentar.

## 6. Interfaz

El panel muestra:

- resumen de capturas totales, en ejecucion, cargadas, fallidas y pendientes;
- health checks de rutas, `tshark`, credenciales API y Postgres;
- pipeline visual por captura;
- detalle de dataset, ruta PCAP, ruta NDJSON, SHA256 y error;
- logs globales o filtrados por captura;
- reintento completo o solo de carga Postgres cuando ya existe la salida NDJSON.

## 7. Estructura del proyecto

```text
automation_pcaps/
  runner.py          # entrypoint compatible con el comando actual
  app.py             # arranque del servidor y worker
  config.py          # carga de config y creacion de carpetas
  api_client.py      # cliente DS4MoveUS
  state.py           # SQLite: jobs y logs
  pipeline.py        # worker y orquestacion
  commands.py        # llamadas a pcap2db y ndjson2pg
  naming.py          # nombres PCAP, vendor, direction
  health.py          # checks de entorno
  web_server.py      # endpoints HTTP
  web/
    index.html
    static/
      app.js
      styles.css
```

## 8. Nota sobre nombres de PCAP

`pcap2db` exige nombres estandarizados:

```text
YYYYMMDDThhmmssZ_cohda_rsu_1001_tx.pcap
YYYYMMDDThhmmssZ_swarco_rsu_1001_rx.pcap
YYYYMMDDThhmmssZ_kapsch_rsu_3003.pcap
```

Si la API devuelve otro nombre, el job fallara en transformacion y se vera en logs.
