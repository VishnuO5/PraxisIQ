-- ============================================================
-- 01_common_treatments.sql
-- Treatment volume analysis with market share and ranking
-- ============================================================

WITH treatment_counts AS (
    SELECT
        Treatment_Type,
        COUNT(*)                          AS Total_Visits,
        COUNT(DISTINCT Patient_ID)        AS Unique_Patients,
        ROUND(AVG(Visit_Number), 2)       AS Avg_Visit_Number
    FROM Visits
    GROUP BY Treatment_Type
),
ranked AS (
    SELECT
        Treatment_Type,
        Total_Visits,
        Unique_Patients,
        Avg_Visit_Number,
        ROUND(
            Total_Visits * 100.0 / SUM(Total_Visits) OVER (),
            2
        )                                 AS Volume_Share_Pct,
        RANK() OVER (ORDER BY Total_Visits DESC)
                                          AS Volume_Rank,
        SUM(Total_Visits) OVER (
            ORDER BY Total_Visits DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )                                 AS Cumulative_Visits
    FROM treatment_counts
)
SELECT
    Volume_Rank,
    Treatment_Type,
    Total_Visits,
    Unique_Patients,
    Volume_Share_Pct,
    Cumulative_Visits,
    Avg_Visit_Number,
    CASE
        WHEN Volume_Share_Pct >= 10 THEN 'Core'
        WHEN Volume_Share_Pct >= 5  THEN 'Standard'
        ELSE                             'Specialist'
    END                                   AS Service_Tier
FROM ranked
ORDER BY Volume_Rank;