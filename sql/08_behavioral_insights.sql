-- ============================================================
-- 08_behavioral_insights.sql
-- Patient behavioral segmentation — visit frequency, recency,
-- and engagement patterns with RFM-style scoring
-- ============================================================

WITH patient_metrics AS (
    SELECT
        p.Patient_Id,
        p.Primary_Treatment,
        p.Returned_Patient,
        p.Total_Visits,
        p.First_Visit_Date,
        p.Last_Visit_Date,
        CAST(
            julianday(p.Last_Visit_Date) - julianday(p.First_Visit_Date)
            AS INTEGER
        )                                   AS Tenure_Days,
        -- Recency: days since last visit relative to latest date in dataset
        CAST(
            julianday((SELECT MAX(Last_Visit_Date) FROM Patients))
            - julianday(p.Last_Visit_Date)
            AS INTEGER
        )                                   AS Days_Since_Last_Visit
    FROM Patients p
),
scored AS (
    SELECT
        Patient_Id,
        Primary_Treatment,
        Returned_Patient,
        Total_Visits,
        Tenure_Days,
        Days_Since_Last_Visit,
        -- Recency score: lower days since last visit = higher score
        NTILE(4) OVER (ORDER BY Days_Since_Last_Visit ASC)
                                            AS Recency_Quartile,
        -- Frequency score: higher visits = higher score
        NTILE(4) OVER (ORDER BY Total_Visits DESC)
                                            AS Frequency_Quartile,
        -- Engagement tier based on visit count
        CASE
            WHEN Total_Visits >= 8  THEN 'Power User'
            WHEN Total_Visits >= 4  THEN 'Engaged'
            WHEN Total_Visits >= 2  THEN 'Returning'
            ELSE                         'One-Time'
        END                                 AS Engagement_Tier,
        -- Recency classification
        CASE
            WHEN Days_Since_Last_Visit <=  90 THEN 'Active'
            WHEN Days_Since_Last_Visit <= 365 THEN 'Lapsing'
            ELSE                                   'Churned'
        END                                 AS Recency_Status
    FROM patient_metrics
),
summary AS (
    SELECT
        Engagement_Tier,
        Recency_Status,
        COUNT(*)                            AS Patient_Count,
        ROUND(
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
            1
        )                                   AS Pct_Of_Total,
        ROUND(AVG(Total_Visits), 2)         AS Avg_Visits,
        ROUND(AVG(Days_Since_Last_Visit), 0)
                                            AS Avg_Days_Since_Last_Visit,
        ROUND(AVG(Tenure_Days), 0)          AS Avg_Tenure_Days,
        -- Churn rate within this segment
        ROUND(
            SUM(CASE WHEN Returned_Patient = 'No' THEN 1.0 ELSE 0 END)
            / COUNT(*) * 100,
            1
        )                                   AS Churn_Rate_Pct
    FROM scored
    GROUP BY
        Engagement_Tier,
        Recency_Status
)
SELECT
    Engagement_Tier,
    Recency_Status,
    Patient_Count,
    Pct_Of_Total,
    Avg_Visits,
    Avg_Days_Since_Last_Visit,
    Avg_Tenure_Days,
    Churn_Rate_Pct,
    CASE
        WHEN Engagement_Tier = 'One-Time'   AND Recency_Status = 'Churned'  THEN 'LOST'
        WHEN Engagement_Tier = 'One-Time'   AND Recency_Status = 'Lapsing'  THEN 'AT RISK'
        WHEN Engagement_Tier = 'Returning'  AND Recency_Status = 'Lapsing'  THEN 'NEEDS ATTENTION'
        WHEN Engagement_Tier = 'Power User' AND Recency_Status = 'Active'   THEN 'CHAMPION'
        WHEN Engagement_Tier = 'Engaged'    AND Recency_Status = 'Active'   THEN 'LOYAL'
        ELSE                                                                      'MONITOR'
    END                                     AS Action_Tag
FROM summary
ORDER BY
    CASE Engagement_Tier
        WHEN 'Power User' THEN 1
        WHEN 'Engaged'    THEN 2
        WHEN 'Returning'  THEN 3
        ELSE                   4
    END,
    CASE Recency_Status
        WHEN 'Active'   THEN 1
        WHEN 'Lapsing'  THEN 2
        ELSE                 3
    END;