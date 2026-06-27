-- ============================================================
-- 05_average_visits.sql
-- Visit frequency analysis with statistical spread and
-- high-engagement patient detection per treatment
-- ============================================================

WITH visit_stats AS (
    SELECT
        Primary_Treatment,
        COUNT(*)                            AS Total_Patients,
        ROUND(AVG(Total_Visits), 2)         AS Avg_Visits,
        MIN(Total_Visits)                   AS Min_Visits,
        MAX(Total_Visits)                   AS Max_Visits,
        -- Variance approximation (SQLite has no STDDEV built-in)
        ROUND(
            AVG(Total_Visits * Total_Visits)
            - AVG(Total_Visits) * AVG(Total_Visits),
            2
        )                                   AS Visit_Variance,
        SUM(CASE WHEN Total_Visits >= 5 THEN 1 ELSE 0 END)
                                            AS High_Engagement_Patients,
        SUM(CASE WHEN Total_Visits = 1  THEN 1 ELSE 0 END)
                                            AS Single_Visit_Patients
    FROM Patients
    GROUP BY Primary_Treatment
),
enriched AS (
    SELECT
        Primary_Treatment,
        Total_Patients,
        Avg_Visits,
        Min_Visits,
        Max_Visits,
        Max_Visits - Min_Visits             AS Visit_Range,
        ROUND(SQRT(Visit_Variance), 2)      AS Visit_StdDev,
        High_Engagement_Patients,
        Single_Visit_Patients,
        ROUND(
            High_Engagement_Patients * 100.0 / Total_Patients,
            1
        )                                   AS High_Engagement_Pct,
        ROUND(
            Single_Visit_Patients * 100.0 / Total_Patients,
            1
        )                                   AS Single_Visit_Pct,
        RANK() OVER (ORDER BY Avg_Visits DESC)
                                            AS Engagement_Rank,
        ROUND(
            AVG(Avg_Visits) OVER (),
            2
        )                                   AS Overall_Avg_Visits,
        ROUND(
            Avg_Visits - AVG(Avg_Visits) OVER (),
            2
        )                                   AS Deviation_From_Mean
    FROM visit_stats
    WHERE Total_Patients >= 3
)
SELECT
    Engagement_Rank,
    Primary_Treatment,
    Total_Patients,
    Avg_Visits,
    Overall_Avg_Visits,
    Deviation_From_Mean,
    Min_Visits,
    Max_Visits,
    Visit_Range,
    Visit_StdDev,
    High_Engagement_Pct         AS Pct_High_Engagement,
    Single_Visit_Pct            AS Pct_Single_Visit,
    CASE
        WHEN High_Engagement_Pct >= 30 THEN 'HIGH'
        WHEN High_Engagement_Pct >= 15 THEN 'MEDIUM'
        ELSE                               'LOW'
    END                         AS Engagement_Tier
FROM enriched
ORDER BY Engagement_Rank;