-- =============================================================================
-- 03_negative_review_monitoring.sql
-- Track complaint category trends month-over-month
--
-- Method: Compare each category's volume in the current month vs prior month
--         using LAG(). Highlight categories with >50% month-over-month growth.
--         Provides both absolute and relative complaint distribution.
-- =============================================================================

WITH monthly_category_counts AS (
    SELECT
        substr(Review_Date, 1, 7)        AS year_month,
        Label,
        COUNT(*)                         AS complaint_count,
        ROUND(AVG(Rating), 2)            AS avg_rating,
        COUNT(CASE WHEN Rating = 1 THEN 1 END) AS one_star_count
    FROM Reviews
    WHERE Label NOT IN ('Positive', 'Neutral')
    GROUP BY year_month, Label
),

with_previous_month AS (
    SELECT
        year_month,
        Label,
        complaint_count,
        avg_rating,
        one_star_count,
        LAG(complaint_count, 1) OVER (
            PARTITION BY Label
            ORDER BY year_month
        ) AS prev_month_count
    FROM monthly_category_counts
),

growth_calculated AS (
    SELECT
        year_month,
        Label,
        complaint_count,
        prev_month_count,
        avg_rating,
        one_star_count,
        CASE
            WHEN prev_month_count IS NULL THEN NULL
            WHEN prev_month_count = 0 THEN NULL
            ELSE ROUND(
                100.0 * (complaint_count - prev_month_count) / prev_month_count,
                1
            )
        END AS mom_growth_pct,
        SUM(complaint_count) OVER (PARTITION BY year_month) AS total_complaints_that_month
    FROM with_previous_month
)

SELECT
    year_month                             AS Month,
    Label                                  AS Category,
    complaint_count                        AS Complaint_Count,
    prev_month_count                       AS Prev_Month_Count,
    mom_growth_pct                         AS MoM_Growth_Pct,
    one_star_count                         AS One_Star_Count,
    avg_rating                             AS Avg_Rating,
    ROUND(
        100.0 * complaint_count / total_complaints_that_month, 1
    )                                      AS Share_Of_Monthly_Complaints,
    CASE
        WHEN mom_growth_pct >= 50  THEN 'RAPID GROWTH'
        WHEN mom_growth_pct >= 20  THEN 'INCREASING'
        WHEN mom_growth_pct <= -20 THEN 'DECLINING'
        WHEN mom_growth_pct IS NULL THEN 'FIRST APPEARANCE'
        ELSE 'STABLE'
    END                                    AS Trend_Flag
FROM growth_calculated
ORDER BY year_month DESC, complaint_count DESC;