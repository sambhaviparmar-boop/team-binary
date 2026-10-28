-- FreightIQ Sprint 1: extend existing derived distance proxies to route scenarios
-- Safe to rerun. Does NOT create new distance estimates.
-- Copies a proxy only from an existing lane with the exact same origin/destination port IDs.
-- Result remains distance_status='derived'; not a verified navigational sailing distance.

BEGIN;

INSERT INTO lane_distances
    (lane_id, distance_nm, method, distance_status, source_id, valid_from, notes)
SELECT target.lane_id,
       source_distance.distance_nm,
       source_distance.method,
       source_distance.distance_status,
       source_distance.source_id,
       source_distance.valid_from,
       source_distance.notes || ' Reused for an additional commodity/vessel scenario with the same origin and destination; remains a derived proxy, not a navigationally verified route distance.'
FROM trade_lanes target
JOIN LATERAL (
    SELECT ld.distance_nm, ld.method, ld.distance_status, ld.source_id, ld.valid_from, ld.notes
    FROM trade_lanes existing_lane
    JOIN lane_distances ld ON ld.lane_id = existing_lane.lane_id
    WHERE existing_lane.origin_port_id = target.origin_port_id
      AND existing_lane.destination_port_id = target.destination_port_id
    ORDER BY
      CASE WHEN ld.distance_status = 'observed' THEN 0
           WHEN ld.distance_status = 'derived' THEN 1
           WHEN ld.distance_status = 'assumed' THEN 2
           ELSE 3 END,
      ld.distance_id
    LIMIT 1
) AS source_distance ON TRUE
WHERE target.route_id IN ('AUS-HYD-HLD', 'AUS-HYD-PRD', 'AUS-HYD-VIZ')
  AND NOT EXISTS (
      SELECT 1 FROM lane_distances existing
      WHERE existing.lane_id = target.lane_id
  );

COMMIT;

-- Verify route coverage and preserve visibility of proxy status:
-- SELECT tl.lane_id, tl.route_id, op.port_name AS origin, dp.port_name AS destination,
--        ld.distance_nm, ld.distance_status, ld.method, ld.notes
-- FROM trade_lanes tl
-- JOIN ports op ON op.port_id = tl.origin_port_id
-- JOIN ports dp ON dp.port_id = tl.destination_port_id
-- LEFT JOIN lane_distances ld ON ld.lane_id = tl.lane_id
-- ORDER BY tl.lane_id;
