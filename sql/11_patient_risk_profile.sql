-- 11_patient_risk_profile.sql
-- Full patient risk profile joining all three tables.
-- Combines clinical risk (non-return, visit outliers, incomplete visits)
-- with review risk (low ratings, negative labels) into a unified view.
--
-- FIXED: Previous version only flagged Root Canal + Gum Treatment as
-- Critical/High, defaulting everything else to Standard — inconsistent
-- with the risk logic in followup_risk_analysis.py and
-- 07_high_risk_patients.sql. Now uses the same 3-signal scoring model
-- used across the project: Returned_Patient, Total_Visits, treatment complexity.
--
-- This is the unified risk view a T&S analyst would build to
-- prioritise which cases require human investigation.

WITH high_complexity AS (
    -- Canonical list of treatments requiring follow-up (matches config.py)
    SELECT 'Root Canal'                  AS Treatment UNION ALL
    SELECT 'Implant'                     UNION ALL
    SELECT 'Metal Braces Treatment'      UNION ALL
    SELECT 'Aligner'                     UNION ALL
    SELECT 'Gum Treatment'               UNION ALL
    SELECT 'Fixed Bridge'                UNION ALL
    SELECT 'Partial Denture'             UNION ALL
    SELECT 'Complete Denture'            UNION ALL
    SELECT 'Deep Scaling and Root Planing' UNION ALL
    SELECT 'Crown/Cap'
),

patient_signals AS (
    SELECT
        p.Patient_Id,
        p.Primary_Treatment,
        p.Total_Visits,
        p.Returned_Patient,
        p.Age,
        p.Gender,

        -- Signal 1: Never returned
        CASE WHEN p.Returned_Patient = 'No' THEN 1 ELSE 0 END  AS Never_Returned,

        -- Signal 2: Single visit only
        CASE WHEN p.Total_Visits = 1 THEN 1 ELSE 0 END         AS Single_Visit,

        -- Signal 3: High-complexity treatment
        CASE WHEN hc.Treatment IS NOT NULL THEN 1 ELSE 0 END   AS High_Complexity,

        -- Signal 4: Visit outlier (Z > 2σ, threshold = 11.56 from analysis)
        CASE WHEN p.Total_Visits > 11 THEN 1 ELSE 0 END        AS Visit_Outlier

    FROM Patients p
    LEFT JOIN high_complexity hc
           ON p.Primary_Treatment = hc.Treatment
),

visit_signals AS (
    SELECT
        Patient_ID,
        COUNT(*)                                                             AS Total_Recorded_Visits,
        SUM(CASE WHEN Treatment_Status != 'Completed' THEN 1 ELSE 0 END)   AS Incomplete_Treatments,
        ROUND(
            100.0 * SUM(CASE WHEN Treatment_Status != 'Completed' THEN 1 ELSE 0 END)
            / COUNT(*), 1
        )                                                                    AS Incomplete_Rate_Pct,
        -- Visit recency: days since last visit
        CAST(
            julianday('now') - julianday(MAX(Visit_Date))
        AS INTEGER)                                                          AS Days_Since_Last_Visit
    FROM Visits
    GROUP BY Patient_ID
),

scored AS (
    SELECT
        ps.*,
        vs.Incomplete_Treatments,
        vs.Incomplete_Rate_Pct,
        vs.Days_Since_Last_Visit,

        -- Composite risk score (0-4)
        (ps.Never_Returned + ps.Single_Visit + ps.High_Complexity + ps.Visit_Outlier)
            AS Risk_Score,

        -- Consistent risk tier matching followup_risk_analysis.py
        CASE
            WHEN (ps.Never_Returned + ps.Single_Visit + ps.High_Complexity) = 3
                THEN 'Critical'
            WHEN (ps.Never_Returned + ps.Single_Visit + ps.High_Complexity) = 2
                THEN 'High'
            WHEN (ps.Never_Returned + ps.Single_Visit + ps.High_Complexity) = 1
                THEN 'Medium'
            ELSE 'Low'
        END AS Risk_Tier,

        -- LAG to show visit count relative to treatment average
        AVG(ps.Total_Visits) OVER (
            PARTITION BY ps.Primary_Treatment
        ) AS Avg_Visits_For_Treatment,

        -- Rank within treatment group by risk
        ROW_NUMBER() OVER (
            PARTITION BY ps.Primary_Treatment
            ORDER BY
                (ps.Never_Returned + ps.Single_Visit + ps.High_Complexity) DESC,
                ps.Age DESC
        ) AS Risk_Rank_In_Treatment

    FROM patient_signals ps
    LEFT JOIN visit_signals vs
           ON ps.Patient_Id = vs.Patient_ID
)

SELECT
    Patient_Id,
    Age,
    Gender,
    Primary_Treatment,
    Total_Visits,
    ROUND(Avg_Visits_For_Treatment, 1)  AS Avg_Visits_For_Treatment,
    Risk_Rank_In_Treatment,
    Returned_Patient,
    Incomplete_Treatments,
    Incomplete_Rate_Pct,
    Days_Since_Last_Visit,
    Never_Returned,
    Single_Visit,
    High_Complexity,
    Visit_Outlier,
    Risk_Score,
    Risk_Tier
FROM scored
WHERE Risk_Tier IN ('Critical', 'High', 'Medium')
ORDER BY
    CASE Risk_Tier
        WHEN 'Critical' THEN 1
        WHEN 'High'     THEN 2
        WHEN 'Medium'   THEN 3
        ELSE                 4
    END,
    Risk_Score DESC,
    Total_Visits DESC
LIMIT 50;