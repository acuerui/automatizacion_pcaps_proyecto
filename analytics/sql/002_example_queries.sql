-- Example queries for Superset/Grafana panels.

-- KPI: captures loaded and quality status.
SELECT
    quality_status,
    COUNT(*) AS captures
FROM vw_dataset_quality
GROUP BY quality_status
ORDER BY captures DESC;

-- KPI cards for one capture.
SELECT
    capture_name,
    packets_total,
    its_messages_total,
    stations_total,
    cam_total,
    denm_total,
    cpm_total,
    its_ratio_percent
FROM vw_capture_summary
ORDER BY session_id DESC;

-- Message distribution.
SELECT
    capture_name,
    message_type,
    messages_total
FROM vw_message_type_counts
ORDER BY capture_name, messages_total DESC;

-- Time series: messages per second.
SELECT
    bucket_second AS time,
    capture_name,
    message_type,
    SUM(messages_total) AS messages_total
FROM vw_v2x_time_series
GROUP BY bucket_second, capture_name, message_type
ORDER BY time;

-- Station comparison.
SELECT
    capture_name,
    station_id,
    device_type,
    vendor,
    packets_total,
    its_messages_total,
    tx_messages_total,
    rx_messages_total,
    cam_total,
    denm_total,
    cpm_total
FROM vw_station_summary
ORDER BY capture_name, its_messages_total DESC;

-- PKI signed ratio.
SELECT
    capture_name,
    messages_total,
    signed_messages_total,
    unsigned_messages_total,
    signed_ratio_percent
FROM vw_pki_summary
ORDER BY capture_name;

-- Map events.
SELECT
    capture_name,
    packet_timestamp,
    message_type,
    station_id,
    direction,
    latitude,
    longitude,
    geo_source,
    event_type
FROM vw_geo_events
ORDER BY packet_timestamp;

