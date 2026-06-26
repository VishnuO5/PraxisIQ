-- =============================================================================
-- 07_emerging_risk_detection.sql
-- Detect new or accelerating complaint patterns before they become crises
--
-- Method:
--   1. Calculate a 3-month rolling average complaint rate per category
--   2. Compare current month volume against that baseline
--   3. Flag categories where volume is 1.5x+ above their own rolling average
--   4. Use NTILE() to rank categories into risk quartiles
--
-- This catches emerging issues (e.g. a new doctor causing Treatment complaints)
-- before they show up in absolute volume rankings.
-- =============================================================================

WITH monthly_counts AS (
    SELECT
        substr(Review_Date, 1, 7)        AS year_month,
        Label,
        COUNT(*)                         AS complaint_count,
        ROUND(AVG(Rating), 2)            AS avg_rating,
        COUNT(CASE WHEN Rating = 1 THEN 1 END) AS critical_complaints
    FROM Reviews
    WHERE Label NOT IN ('Positive')
    GROUP BY year_month, Label
),

rolling_avg AS (
    SELECT
        year_month,
        Label,
        complaint_count,
        avg_rating,
        critical_complaints,
        ROUND(
            AVG(complaint_count) OVER (
                PARTITION BY Label
                ORDER BY year_month
                ROWS BETWEEN 2 PRECEDING AND 1 PRECEDING
            ), 2
        )                                AS rolling_3m_prior_avg,
        LAG(complaint_count, 1) OVER (
            PARTITION BY Label ORDER BY year_month
        )                                AS prev_month_count,
        LAG(avg_rating, 1) OVER (
            PARTITION BY Label ORDER BY year_month
        )                                AS prev_month_avg_rating
    FROM monthly_counts
),

emergence_scored AS (
    SELECT
        year_month,
        Label,
        complaint_count,
        rolling_3m_prior_avg,
        prev_month_count,
        avg_rating,
        prev_month_avg_rating,
        critical_complaints,

        CASE
            WHEN rolling_3m_prior_avg IS NULL OR rolling_3m_prior_avg = 0
            THEN NULL
            ELSE ROUND(complaint_count * 1.0 / rolling_3m_prior_avg, 2)
        END                              AS emergence_ratio,

        CASE
            WHEN prev_month_avg_rating IS NOT NULL
            THEN ROUND(avg_rating - prev_month_avg_rating, 2)
            ELSE NULL
        END                              AS rating_delta,

        CASE
            WHEN rolling_3m_prior_avg IS NULL THEN 'NEW CATEGORY'
            WHEN complaint_count >= 2.0 * rolling_3m_prior_avg THEN 'EMERGING CRISIS'
            WHEN complaint_count >= 1.5 * rolling_3m_prior_avg THEN 'ELEVATED RISK'
            WHEN complaint_count <= 0.5 * rolling_3m_prior_avg THEN 'IMPROVING'
            ELSE 'STABLE'
        END                              AS emergence_status
    FROM rolling_avg
),

quartile_ranked AS (
    SELECT
        *,
        NTILE(4) OVER (
            PARTITION BY year_month
            ORDER BY complaint_count DESC
        )                                AS risk_quartile
    FROM emergence_scored
)

SELECT
    year_month                           AS Month,
    Label                                AS Category,
    complaint_count                      AS Complaints,
    rolling_3m_prior_avg                 AS Prior_3M_Avg,
    emergence_ratio                      AS Emergence_Ratio,
    avg_rating                           AS Avg_Rating,
    rating_delta                         AS Rating_Change_vs_Prior_Month,
    critical_complaints                  AS Critical_1Star_Count,
    risk_quartile                        AS Risk_Quartile,
    emergence_status                     AS Status
FROM quartile_ranked
WHERE emergence_status IN ('EMERGING CRISIS', 'ELEVATED RISK', 'NEW CATEGORY')
ORDER BY year_month DESC, emergence_ratio DESC NULLS LAST;