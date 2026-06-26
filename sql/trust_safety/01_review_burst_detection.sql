-- =============================================================================
-- 01_review_burst_detection.sql
-- Detect abnormal spikes in daily review volume (potential coordinated activity)
--
-- Method: Calculate rolling 7-day average and flag days exceeding 3x baseline.
--         Uses LAG() to compute day-over-day volume change for trend context.
-- =============================================================================

WITH daily_volume AS (
    SELECT
        Review_Date,
        COUNT(*)                                        AS review_count,
        COUNT(CASE WHEN Rating <= 2 THEN 1 END)         AS low_rating_count,
        ROUND(AVG(Rating), 2)                           AS avg_rating
    FROM Reviews
    GROUP BY Review_Date
),

rolling_baseline AS (
    SELECT
        Review_Date,
        review_count,
        low_rating_count,
        avg_rating,
        ROUND(
            AVG(review_count) OVER (
                ORDER BY Review_Date
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ), 2
        )                                               AS rolling_7day_avg,
        LAG(review_count, 1) OVER (ORDER BY Review_Date) AS prev_day_count
    FROM daily_volume
),

burst_flags AS (
    SELECT
        Review_Date,
        review_count,
        low_rating_count,
        avg_rating,
        rolling_7day_avg,
        prev_day_count,
        ROUND(review_count * 1.0 / NULLIF(rolling_7day_avg, 0), 2) AS burst_ratio,
        CASE
            WHEN review_count >= 3 * rolling_7day_avg THEN 'BURST DETECTED'
            WHEN review_count >= 2 * rolling_7day_avg THEN 'ELEVATED'
            ELSE 'NORMAL'
        END AS burst_status,
        CASE
            WHEN prev_day_count IS NOT NULL
            THEN review_count - prev_day_count
            ELSE NULL
        END AS day_over_day_change
    FROM rolling_baseline
)

SELECT
    Review_Date,
    review_count                               AS Reviews_On_Day,
    low_rating_count                           AS Low_Rating_Reviews,
    avg_rating                                 AS Avg_Rating,
    rolling_7day_avg                           AS Rolling_7Day_Avg,
    burst_ratio                                AS Burst_Ratio_vs_Baseline,
    day_over_day_change                        AS Day_Over_Day_Change,
    burst_status                               AS Burst_Status
FROM burst_flags
WHERE burst_status != 'NORMAL'
ORDER BY burst_ratio DESC;