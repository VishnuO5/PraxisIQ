-- ============================================================
-- 03_return_rates.sql
-- Patient return rate analysis with treatment-level breakdown
-- and churn risk segmentation
-- ============================================================

WITH base AS (
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
        )                               AS Days_Since_First_Visit
    FROM Patients p
),
overall AS (
    SELECT
        Returned_Patient,
        COUNT(*)                        AS Patient_Count,
        ROUND(
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
            2
        )                               AS Pct_Of_Total,
        ROUND(AVG(Total_Visits), 2)     AS Avg_Visits,
        ROUND(AVG(Days_Since_First_Visit), 0)
                                        AS Avg_Days_Active
    FROM base
    GROUP BY Returned_Patient
),
by_treatment AS (
    SELECT
        Primary_Treatment,
        COUNT(*)                        AS Total_Patients,
        SUM(CASE WHEN Returned_Patient = 'Yes' THEN 1 ELSE 0 END)
                                        AS Returned,
        SUM(CASE WHEN Returned_Patient = 'No'  THEN 1 ELSE 0 END)
                                        AS One_Time,
        ROUND(
            SUM(CASE WHEN Returned_Patient = 'No' THEN 1.0 ELSE 0 END)
            / COUNT(*) * 100,
            1
        )                               AS Churn_Rate_Pct,
        RANK() OVER (
            ORDER BY
                SUM(CASE WHEN Returned_Patient = 'No' THEN 1.0 ELSE 0 END)
                / COUNT(*) DESC
        )                               AS Churn_Rank
    FROM base
    GROUP BY Primary_Treatment
    HAVING Total_Patients >= 5
)
-- Overall summary
SELECT
    'OVERALL'                           AS Breakdown,
    Returned_Patient                    AS Segment,
    Patient_Count,
    Pct_Of_Total                        AS Pct,
    Avg_Visits,
    Avg_Days_Active,
    NULL                                AS Churn_Rate_Pct,
    NULL                                AS Churn_Rank
FROM overall

UNION ALL

-- Per-treatment churn rates
SELECT
    'BY_TREATMENT'                      AS Breakdown,
    Primary_Treatment                   AS Segment,
    Total_Patients                      AS Patient_Count,
    ROUND(Returned * 100.0 / Total_Patients, 2)
                                        AS Pct,
    NULL                                AS Avg_Visits,
    NULL                                AS Avg_Days_Active,
    Churn_Rate_Pct,
    Churn_Rank
FROM by_treatment
ORDER BY Breakdown, Churn_Rank NULLS LAST;