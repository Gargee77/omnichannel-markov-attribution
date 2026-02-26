-- 05_checks.sql
-- Purpose: Data quality and sanity checks to confirm each step produced valid outputs.

-- Raw table row counts
SELECT COUNT(*) AS message_events_rows FROM message_events;
SELECT COUNT(*) AS conversions_rows FROM conversions;

-- Validate channel distribution
SELECT channel, COUNT(*) AS events
FROM message_events
GROUP BY 1
ORDER BY events DESC;

-- Journey view health: should not be empty
SELECT COUNT(*) AS journey_rows FROM v_conversion_journeys;

-- How many conversions have at least 1 journey touch?
SELECT COUNT(DISTINCT conversion_id) AS conversions_with_journeys
FROM v_conversion_journeys;

-- Paths health: should show non-empty strings
SELECT COUNT(*) AS paths_rows
FROM v_paths_per_conversion
WHERE path IS NOT NULL AND path <> '';

SELECT * FROM v_paths_per_conversion
ORDER BY conversion_ts DESC
LIMIT 10;

-- Last-touch should return rows (usually close to #conversions)
SELECT COUNT(*) AS last_touch_rows FROM v_last_touch_attribution;

SELECT * FROM v_last_touch_channel_summary;

-- Attribution results should contain both models after Markov runs
SELECT model_name, COUNT(*) AS rows
FROM attribution_results
GROUP BY 1
ORDER BY 1;

-- What Power BI reads
SELECT * FROM v_kpi_topline;
SELECT * FROM v_channel_event_summary;
SELECT * FROM v_attribution_latest ORDER BY model_name, channel;