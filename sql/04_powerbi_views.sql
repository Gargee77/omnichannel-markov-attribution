-- Dashboard Views
-- Purpose: Provide stable, simple views for dashboarding.

-- KPI cards 
CREATE OR REPLACE VIEW v_kpi_topline AS
SELECT
  (SELECT COUNT(DISTINCT user_id) FROM message_events) AS users_touched,
  (SELECT COUNT(*) FROM message_events) AS total_events,
  (SELECT COUNT(*) FROM conversions) AS total_conversions,
  (SELECT COALESCE(SUM(value), 0) FROM conversions) AS total_revenue;

-- Channel engagement summary
DROP VIEW IF EXISTS v_channel_event_summary;

CREATE VIEW v_channel_event_summary AS
SELECT
  channel,
  COUNT(*) AS events,
  SUM(CASE WHEN event_type = 'opened' THEN 1 ELSE 0 END) AS opens,
  SUM(CASE WHEN event_type = 'clicked' THEN 1 ELSE 0 END) AS clicks,
  ROUND(
    (SUM(CASE WHEN event_type = 'clicked' THEN 1 ELSE 0 END)::numeric
     / NULLIF(COUNT(*), 0)) * 100,
    2
  ) AS click_rate_pct
FROM message_events
GROUP BY channel
ORDER BY events DESC;

-- Latest attribution result per (model, channel)
CREATE OR REPLACE VIEW v_attribution_latest AS
WITH ranked AS (
  SELECT
    model_name,
    channel,
    contribution,
    created_at,
    ROW_NUMBER() OVER (
      PARTITION BY model_name, channel
      ORDER BY created_at DESC
    ) AS rn
  FROM attribution_results
)
SELECT
  model_name,
  channel,
  contribution
FROM ranked
WHERE rn = 1;