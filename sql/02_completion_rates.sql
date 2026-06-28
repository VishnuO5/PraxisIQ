-- 02_completion_rates.sql
-- Treatment completion rates with ranking and visit-level breakdown.
--
-- Upgraded from a bare GROUP BY to include:
--   - CTE for base aggregation (readable, reusable)
--   - ROW_NUMBER() to rank treatments by completion rate
--   - NTILE(4) to bucket treatments into performance quartiles
--   - Completion gap (distance from 100%) for prioritisation
--
-- Use case: identify which treatments have the highest drop-off
-- so clinical ops can target follow-up interventions.

WITH base AS (
    SELECT
        Treatment_Type,
        COUNT(*)                                                          AS Total_Visits,
        SUM(CASE WHEN Treatment_Status = 'Completed' THEN 1 ELSE 0 END)  AS Completed,
        SUM(CASE WHEN Treatment_Status != 'Completed' THEN 1 ELSE 0 END) AS Incomplete
    FROM Visits
    GROUP BY Treatment_Type
),

ranked AS (
    SELECT
        Treatment_Type,
        Total_Visits,
        Completed,
        Incomplete,
        ROUND(100.0 * Completed / Total_Visits, 2)          AS Completion_Rate_Pct,
        ROUND(100.0 - (100.0 * Completed / Total_Visits), 2) AS Completion_Gap_Pct,

        -- Rank 1 = highest completion rate
        ROW_NUMBER() OVER (ORDER BY Completed * 1.0 / Total_Visits DESC) AS Rank,

        -- Quartile: 1 = top performers, 4 = lowest completion
        NTILE(4) OVER (ORDER BY Completed * 1.0 / Total_Visits DESC)     AS Quartile
    FROM base
)

SELECT
    Rank,
    Treatment_Type,
    Total_Visits,
    Completed,
    Incomplete,
    Completion_Rate_Pct,
    Completion_Gap_Pct,
    CASE Quartile
        WHEN 1 THEN 'Top Performer'
        WHEN 2 THEN 'Above Average'
        WHEN 3 THEN 'Below Average'
        WHEN 4 THEN 'Needs Intervention'
    END AS Performance_Tier
FROM ranked
ORDER BY Rank;