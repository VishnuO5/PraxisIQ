-- ============================================================
-- 06_treatment_trends.sql
-- Monthly treatment volume trends with MoM growth,
-- rolling averages, and peak detection
-- ============================================================

WITH monthly_counts AS (
    SELECT
        substr(Visit_Date, 1, 7)        AS Month,
        Treatment_Type,
        COUNT(*)                        AS Visit_Count
    FROM Visits
    GROUP BY
        substr(Visit_Date, 1, 7),
        Treatment_Type
),
with_lag AS (
    SELECT
        Month,
        Treatment_Type,
        Visit_Count,
        LAG(Visit_Count, 1) OVER (
            PARTITION BY Treatment_Type
            ORDER BY Month
        )                               AS Prev_Month_Count,
        LAG(Visit_Count, 3) OVER (
            PARTITION BY Treatment_Type
            ORDER BY Month
        )                               AS Count_3M_Ago,
        AVG(Visit_Count) OVER (
            PARTITION BY Treatment_Type
            ORDER BY Month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        )                               AS Rolling_3M_Avg,
        SUM(Visit_Count) OVER (
            PARTITION BY Treatment_Type
            ORDER BY Month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )                               AS Cumulative_Visits,
        RANK() OVER (
            PARTITION BY Treatment_Type
            ORDER BY Visit_Count DESC
        )                               AS Peak_Rank
    FROM monthly_counts
),
with_growth AS (
    SELECT
        Month,
        Treatment_Type,
        Visit_Count,
        Prev_Month_Count,
        Rolling_3M_Avg,
        Cumulative_Visits,
        Peak_Rank,
        CASE
            WHEN Prev_Month_Count IS NULL OR Prev_Month_Count = 0 THEN NULL
            ELSE ROUND(
                (Visit_Count - Prev_Month_Count) * 100.0 / Prev_Month_Count,
                1
            )
        END                             AS MoM_Growth_Pct,
        CASE
            WHEN Count_3M_Ago IS NULL OR Count_3M_Ago = 0 THEN NULL
            ELSE ROUND(
                (Visit_Count - Count_3M_Ago) * 100.0 / Count_3M_Ago,
                1
            )
        END                             AS QoQ_Growth_Pct
    FROM with_lag
)
SELECT
    Month,
    Treatment_Type,
    Visit_Count,
    Prev_Month_Count,
    MoM_Growth_Pct,
    QoQ_Growth_Pct,
    ROUND(Rolling_3M_Avg, 1)            AS Rolling_3M_Avg,
    Cumulative_Visits,
    CASE WHEN Peak_Rank = 1 THEN 'PEAK' ELSE '' END
                                        AS Is_Peak_Month,
    CASE
        WHEN MoM_Growth_Pct >=  20 THEN 'SURGE'
        WHEN MoM_Growth_Pct >=   5 THEN 'GROWING'
        WHEN MoM_Growth_Pct BETWEEN -5 AND 5 THEN 'STABLE'
        WHEN MoM_Growth_Pct <   -5 THEN 'DECLINING'
        ELSE 'INSUFFICIENT_DATA'
    END                                 AS Trend_Signal
FROM with_growth
ORDER BY
    Treatment_Type,
    Month;