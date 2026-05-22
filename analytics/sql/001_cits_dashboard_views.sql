-- Common analytics views for Superset and Grafana.
-- Run this in the same schema where ndjson2pg loads the C-ITS tables.

CREATE OR REPLACE VIEW vw_capture_summary AS
SELECT
    ts.id AS session_id,
    ts.name AS capture_name,
    ts.description,
    ts.location,
    ts.start_time,
    ts.end_time,
    COUNT(DISTINCT p.id) AS packets_total,
    COUNT(DISTINCT im.id) AS its_messages_total,
    COUNT(DISTINCT d.id) AS devices_total,
    COUNT(DISTINCT im.station_id) FILTER (WHERE im.station_id IS NOT NULL) AS stations_total,
    COUNT(DISTINCT cam.id) AS cam_total,
    COUNT(DISTINCT denm.id) AS denm_total,
    COUNT(DISTINCT cpm.id) AS cpm_total,
    COUNT(DISTINCT spatem.id) AS spatem_total,
    COUNT(DISTINCT mapem.id) AS mapem_total,
    COUNT(DISTINCT ivi.id) AS ivi_total,
    COUNT(DISTINCT im.id) FILTER (WHERE im.has_pki IS TRUE) AS pki_messages_total,
    MIN(p.packet_timestamp) AS first_packet_timestamp,
    MAX(p.packet_timestamp) AS last_packet_timestamp,
    EXTRACT(EPOCH FROM (MAX(p.packet_timestamp) - MIN(p.packet_timestamp))) AS duration_seconds,
    CASE
        WHEN COUNT(DISTINCT p.id) = 0 THEN 0
        ELSE ROUND((COUNT(DISTINCT im.id)::numeric / COUNT(DISTINCT p.id)::numeric) * 100, 2)
    END AS its_ratio_percent
FROM test_sessions ts
LEFT JOIN packets p ON p.session_id = ts.id
LEFT JOIN devices d ON d.id = p.device_id
LEFT JOIN its_messages im ON im.packet_id = p.id
LEFT JOIN cam_messages_basic_vehicle cam ON cam.id = im.id
LEFT JOIN denm_messages denm ON denm.id = im.id
LEFT JOIN cpm_messages cpm ON cpm.id = im.id
LEFT JOIN spatem_messages spatem ON spatem.id = im.id
LEFT JOIN mapem_messages mapem ON mapem.id = im.id
LEFT JOIN ivi_messages ivi ON ivi.id = im.id
GROUP BY
    ts.id,
    ts.name,
    ts.description,
    ts.location,
    ts.start_time,
    ts.end_time;


CREATE OR REPLACE VIEW vw_message_type_counts AS
SELECT
    ts.id AS session_id,
    ts.name AS capture_name,
    COALESCE(im.message_type::text, 'UNKNOWN') AS message_type,
    COUNT(*) AS messages_total,
    COUNT(*) FILTER (WHERE im.has_pki IS TRUE) AS pki_messages_total,
    MIN(p.packet_timestamp) AS first_seen_at,
    MAX(p.packet_timestamp) AS last_seen_at
FROM its_messages im
JOIN test_sessions ts ON ts.id = im.session_id
LEFT JOIN packets p ON p.id = im.packet_id
GROUP BY
    ts.id,
    ts.name,
    COALESCE(im.message_type::text, 'UNKNOWN');


CREATE OR REPLACE VIEW vw_station_summary AS
SELECT
    ts.id AS session_id,
    ts.name AS capture_name,
    COALESCE(im.station_id, d.station_id) AS station_id,
    d.id AS device_id,
    d.device_type,
    d.vendor,
    d.model,
    d.mac_address,
    d.ip_address,
    COUNT(DISTINCT p.id) AS packets_total,
    COUNT(DISTINCT im.id) AS its_messages_total,
    COUNT(DISTINCT im.id) FILTER (WHERE p.direction = 'TX') AS tx_messages_total,
    COUNT(DISTINCT im.id) FILTER (WHERE p.direction = 'RX') AS rx_messages_total,
    COUNT(DISTINCT cam.id) AS cam_total,
    COUNT(DISTINCT denm.id) AS denm_total,
    COUNT(DISTINCT cpm.id) AS cpm_total,
    COUNT(DISTINCT im.id) FILTER (WHERE im.has_pki IS TRUE) AS pki_messages_total,
    MIN(p.packet_timestamp) AS first_seen_at,
    MAX(p.packet_timestamp) AS last_seen_at
FROM test_sessions ts
LEFT JOIN packets p ON p.session_id = ts.id
LEFT JOIN devices d ON d.id = p.device_id
LEFT JOIN its_messages im ON im.packet_id = p.id
LEFT JOIN cam_messages_basic_vehicle cam ON cam.id = im.id
LEFT JOIN denm_messages denm ON denm.id = im.id
LEFT JOIN cpm_messages cpm ON cpm.id = im.id
GROUP BY
    ts.id,
    ts.name,
    COALESCE(im.station_id, d.station_id),
    d.id,
    d.device_type,
    d.vendor,
    d.model,
    d.mac_address,
    d.ip_address;


CREATE OR REPLACE VIEW vw_v2x_time_series AS
SELECT
    date_trunc('second', p.packet_timestamp) AS bucket_second,
    ts.id AS session_id,
    ts.name AS capture_name,
    p.direction,
    COALESCE(im.message_type::text, 'UNKNOWN') AS message_type,
    im.station_id,
    COUNT(*) AS messages_total,
    COUNT(*) FILTER (WHERE im.has_pki IS TRUE) AS pki_messages_total
FROM its_messages im
JOIN packets p ON p.id = im.packet_id
JOIN test_sessions ts ON ts.id = im.session_id
GROUP BY
    date_trunc('second', p.packet_timestamp),
    ts.id,
    ts.name,
    p.direction,
    COALESCE(im.message_type::text, 'UNKNOWN'),
    im.station_id;


CREATE OR REPLACE VIEW vw_dataset_quality AS
SELECT
    cs.session_id,
    cs.capture_name,
    cs.packets_total,
    cs.its_messages_total,
    cs.devices_total,
    cs.stations_total,
    cs.cam_total,
    cs.denm_total,
    cs.cpm_total,
    cs.pki_messages_total,
    cs.duration_seconds,
    cs.its_ratio_percent,
    CASE
        WHEN cs.packets_total = 0 THEN 'FAIL'
        WHEN cs.its_messages_total = 0 THEN 'FAIL'
        WHEN cs.duration_seconds IS NULL THEN 'WARNING'
        WHEN cs.cam_total = 0 AND cs.denm_total = 0 AND cs.cpm_total = 0 THEN 'WARNING'
        ELSE 'OK'
    END AS quality_status,
    ARRAY_REMOVE(ARRAY[
        CASE WHEN cs.packets_total = 0 THEN 'no_packets' END,
        CASE WHEN cs.its_messages_total = 0 THEN 'no_its_messages' END,
        CASE WHEN cs.cam_total = 0 THEN 'no_cam' END,
        CASE WHEN cs.denm_total = 0 THEN 'no_denm' END,
        CASE WHEN cs.cpm_total = 0 THEN 'no_cpm' END,
        CASE WHEN cs.pki_messages_total = 0 THEN 'no_pki' END,
        CASE WHEN cs.duration_seconds IS NULL THEN 'no_duration' END
    ], NULL) AS quality_warnings
FROM vw_capture_summary cs;


CREATE OR REPLACE VIEW vw_pki_summary AS
SELECT
    ts.id AS session_id,
    ts.name AS capture_name,
    COUNT(im.id) AS messages_total,
    COUNT(im.id) FILTER (WHERE im.has_pki IS TRUE) AS signed_messages_total,
    COUNT(im.id) FILTER (WHERE im.has_pki IS NOT TRUE) AS unsigned_messages_total,
    CASE
        WHEN COUNT(im.id) = 0 THEN 0
        ELSE ROUND((COUNT(im.id) FILTER (WHERE im.has_pki IS TRUE)::numeric / COUNT(im.id)::numeric) * 100, 2)
    END AS signed_ratio_percent
FROM test_sessions ts
LEFT JOIN its_messages im ON im.session_id = ts.id
GROUP BY
    ts.id,
    ts.name;


CREATE OR REPLACE VIEW vw_geo_events AS
SELECT
    ts.id AS session_id,
    ts.name AS capture_name,
    p.packet_timestamp,
    im.id AS its_message_id,
    im.message_type,
    im.station_id,
    p.direction,
    cam.latitude,
    cam.longitude,
    cam.speed,
    cam.heading,
    NULL::text AS event_type,
    'CAM' AS geo_source
FROM cam_messages_basic_vehicle cam
JOIN its_messages im ON im.id = cam.id
JOIN packets p ON p.id = im.packet_id
JOIN test_sessions ts ON ts.id = im.session_id
WHERE cam.latitude IS NOT NULL
  AND cam.longitude IS NOT NULL

UNION ALL

SELECT
    ts.id AS session_id,
    ts.name AS capture_name,
    p.packet_timestamp,
    im.id AS its_message_id,
    im.message_type,
    im.station_id,
    p.direction,
    denm.event_latitude AS latitude,
    denm.event_longitude AS longitude,
    NULL::numeric AS speed,
    NULL::numeric AS heading,
    denm.event_type::text AS event_type,
    'DENM' AS geo_source
FROM denm_messages denm
JOIN its_messages im ON im.id = denm.id
JOIN packets p ON p.id = im.packet_id
JOIN test_sessions ts ON ts.id = im.session_id
WHERE denm.event_latitude IS NOT NULL
  AND denm.event_longitude IS NOT NULL

UNION ALL

SELECT
    ts.id AS session_id,
    ts.name AS capture_name,
    p.packet_timestamp,
    im.id AS its_message_id,
    im.message_type,
    im.station_id,
    p.direction,
    cpm.latitude,
    cpm.longitude,
    NULL::numeric AS speed,
    NULL::numeric AS heading,
    NULL::text AS event_type,
    'CPM' AS geo_source
FROM cpm_messages cpm
JOIN its_messages im ON im.id = cpm.id
JOIN packets p ON p.id = im.packet_id
JOIN test_sessions ts ON ts.id = im.session_id
WHERE cpm.latitude IS NOT NULL
  AND cpm.longitude IS NOT NULL;
