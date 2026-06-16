# Informe breve del caso de uso: analisis de PCAPs C-ITS/V2X desde el espacio de datos

## Situacion actual

El caso de uso desarrollado plantea un flujo completo para aportar valor sobre capturas PCAP/PCAPNG de comunicaciones C-ITS/V2X compartidas por administraciones publicas u otros agentes a traves de un espacio de datos. El proceso parte de la publicacion de una captura raw en dicho espacio, continua con su descarga automatizada, su transformacion a datos estructurados, su carga en una base de datos y su visualizacion mediante cuadros de mando.

La solucion permite tomar un fichero tecnico dificil de interpretar directamente y convertirlo en informacion explotable. Para ello, el modulo de automatizacion detecta y descarga las capturas disponibles; `pcap2db` transforma los PCAP en tablas estructuradas de paquetes, mensajes ITS y tipos especificos como CAM, DENM, CPM, SPATEM, MAPEM e IVI; `ndjson2pg` carga esos resultados en PostgreSQL; y Superset permite construir dashboards para analizar actividad, volumen de mensajes, comportamiento por estacion, proveedor, direccion TX/RX y calidad general de los datos.

El flujo ya contempla capturas procedentes de diferentes proveedores, como Cohda, Swarco y Kapsch. Tambien se ha avanzado en un modelo de sesion mas coherente con pruebas reales, donde una misma sesion puede agrupar varios ficheros capturados por distintos equipos o proveedores si comparten el mismo timestamp de inicio. La direccion de comunicacion se mantiene a nivel de paquete, permitiendo analizar enviados y recibidos sin dividir artificialmente una misma prueba.

## Lo que falta y oportunidades de mejora

El principal punto pendiente es consolidar la carga incremental en base de datos. Cuando se reciba un nuevo fichero que pertenezca a una sesion ya existente, el sistema deberia incorporar sus datos a la sesion correspondiente en lugar de crear una nueva. Al mismo tiempo, debe evitarse que un mismo fichero raw se cargue dos veces y genere duplicados. Para ello se plantea registrar las capturas asociadas a cada sesion, de forma que el sistema pueda distinguir entre una nueva aportacion valida y una recarga accidental.

Otra mejora relevante es cerrar el ciclo de valor con el espacio de datos. La idea no es solo consumir PCAPs, sino devolver al espacio de datos un resultado enriquecido: informes, indicadores, resumenes de calidad o datasets derivados que faciliten la reutilizacion por parte de administraciones, operadores, investigadores u otros participantes. De esta forma, el proceso convierte una captura tecnica en un activo de informacion mas accesible y util.

Tambien existe margen para mejorar la experiencia operativa. El flujo podria incorporar validaciones previas mas claras, trazabilidad del origen de cada captura, resumenes de procesamiento, avisos de calidad y mensajes orientados a usuario. Esto permitiria que perfiles no especializados pudieran seguir el estado del proceso y entender el resultado sin depender constantemente del equipo tecnico.

## Alcance desarrollado

El alcance actual cubre un prototipo funcional de extremo a extremo: desde la obtencion de capturas del espacio de datos hasta su analisis visual en Superset. Se ha desarrollado la automatizacion local del pipeline, la conversion de capturas a datos estructurados, la carga en base de datos y una capa de visualizacion inicial para explotar la informacion.

El sistema ya permite ejecutar pruebas reales, validar la informacion insertada en PostgreSQL y generar vistas utiles para analizar el comportamiento de las comunicaciones V2X. Aunque todavia quedan aspectos por cerrar, especialmente la gestion fina de sesiones compartidas y duplicados, la viabilidad tecnica del caso de uso esta demostrada.

## Potenciales usuarios

Los usuarios potenciales incluyen administraciones publicas que publiquen o consuman datos de movilidad conectada, responsables de pilotos C-ITS/V2X, operadores de infraestructura, equipos de validacion, laboratorios de interoperabilidad, analistas de datos y equipos tecnicos que necesiten interpretar capturas de comunicaciones.

Tambien puede aportar valor a perfiles de gestion tecnica o coordinacion de proyectos, ya que transforma ficheros raw complejos en indicadores comprensibles: volumen de mensajes, actividad por estacion, distribucion por proveedor, direccion de comunicacion, calidad de dataset, eventos geolocalizados y evolucion temporal. En un entorno de espacio de datos, esto facilita la reutilizacion de la informacion y permite devolver resultados enriquecidos que aumentan el valor del dato original.
