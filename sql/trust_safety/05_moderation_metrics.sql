-- =============================================================================
-- 05_moderation_metrics.sql
-- Moderation pipeline health dashboard — weekly and cumulative metrics
--
-- Method: Compute weekly review intake, backlog, category distribution,
--         and resolution rate by tier. Uses CTEs and window functions
--         to generate a time-series view of moderation workload.
-- =============================================================================

WITH weekly_intake AS (
    SELECT
        strftime('%Y-W%W', Review_Date)          AS iso_week,
        COUNT(*)                                  AS total_reviews,
        COUNT(CASE WHEN Label != 'Positive' THEN 1 END) AS flagged_reviews,
        COUNT(CASE WHEN Rating <= 2 THEN 1 END)  AS low_rating_reviews,
        COUNT(CASE WHEN Label = 'Treatment' AND Rating <= 2 THEN 1 END) AS tier1_candidates,
        ROUND(AVG(Rating), 2)                     AS avg_rating
    FROM Reviews
    GROUP BY iso_week
),

weekly_with_trends AS (
    SELECT
        iso_week,
        total_reviews,
        flagged_reviews,
        low_rating_reviews,
        tier1_candidates,
        avg_rating,
        LAG(flagged_reviews, 1) OVER (ORDER BY iso_week) AS prev_week_flagged,
        SUM(flagged_reviews) OVER (
            ORDER BY iso_week
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_flagged
    FROM weekly_intake
),

tier_distribution AS (
    SELECT
        CASE
            WHEN Label = 'Treatment' AND Rating <= 2    THEN 'TIER 1 — Immediate'
            WHEN Label IN ('Communication', 'Staff') AND Rating <= 3 THEN 'TIER 2 — 24h'
            WHEN Label = 'Positive'                     THEN 'APPROVED — No Action'
            ELSE                                             'TIER 3 — Batch'
        END                                              AS moderation_tier,
        COUNT(*)                                         AS review_count,
        ROUND(AVG(Rating), 2)                            AS avg_rating,
        ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM Reviews), 1) AS pct_of_total
    FROM Reviews
    GROUP BY moderation_tier
)

SELECT
    iso_week                                          AS Week,
    total_reviews                                     AS Total_Reviews,
    flagged_reviews                                   AS Flagged_For_Review,
    tier1_candidates                                  AS Tier1_Candidates,
    avg_rating                                        AS Avg_Rating,
    CASE
        WHEN prev_week_flagged IS NULL THEN NULL
        ELSE ROUND(
            100.0 * (flagged_reviews - prev_week_flagged) / NULLIF(prev_week_flagged, 0), 1
        )
    END                                               AS WoW_Flagged_Change_Pct,
    cumulative_flagged                                AS Cumulative_Flagged
FROM weekly_with_trends
ORDER BY iso_week;