-- 09_high_risk_treatment_review_correlation.sql
-- Cross-references dropout patients (never returned after treatment)
-- with negative Treatment reviews — surfaces whether certain treatments
-- generate both patient dropout AND complaint signals simultaneously.
--
-- NOTE: All visits in this dataset have Treatment_Status = 'Completed',
-- so dropout risk is derived from Returned_Patient = 'No' instead.
-- This is the real signal: patients who came, got treated, and never
-- came back — the clinical equivalent of churn.
--
-- This mirrors T&S investigation workflows: correlating behavioural
-- signals (patient dropout) with content signals (negative reviews)
-- to build a unified risk picture per treatment type.

WITH dropout_patients AS (
    -- Patients who never returned, grouped by treatment
    SELECT
        Primary_Treatment,
        COUNT(*)                                                        AS Total_Patients,
        SUM(CASE WHEN Returned_Patient = 'No' THEN 1 ELSE 0 END)       AS Dropout_Count,
        SUM(CASE WHEN Returned_Patient = 'No'
                  AND Total_Visits = 1 THEN 1 ELSE 0 END)              AS Single_Visit_Dropout,
        ROUND(
            100.0 * SUM(CASE WHEN Returned_Patient = 'No' THEN 1 ELSE 0 END)
            / COUNT(*), 1
        )                                                               AS Dropout_Rate_Pct,

        -- Rank treatments by dropout rate
        ROW_NUMBER() OVER (
            ORDER BY
                SUM(CASE WHEN Returned_Patient = 'No' THEN 1 ELSE 0 END) * 1.0
                / COUNT(*) DESC
        ) AS Dropout_Rank
    FROM Patients
    GROUP BY Primary_Treatment
),

treatment_reviews AS (
    -- Negative Treatment reviews aggregated
    SELECT
        COUNT(*)                                        AS Total_Treatment_Reviews,
        SUM(CASE WHEN Rating = 1 THEN 1 ELSE 0 END)    AS Rating_1_Count,
        SUM(CASE WHEN Rating = 2 THEN 1 ELSE 0 END)    AS Rating_2_Count,
        ROUND(AVG(Rating), 2)                           AS Avg_Rating,
        ROUND(
            100.0 * SUM(CASE WHEN Rating <= 2 THEN 1 ELSE 0 END)
            / COUNT(*), 1
        )                                               AS High_Risk_Rate_Pct
    FROM Reviews
    WHERE Label = 'Treatment'
),

overall_reviews AS (
    -- All review categories per label for context
    SELECT
        Label,
        COUNT(*)                AS Review_Count,
        ROUND(AVG(Rating), 2)   AS Avg_Rating
    FROM Reviews
    GROUP BY Label
)

-- Final: dropout signals + review signals combined per treatment
SELECT
    dp.Dropout_Rank,
    dp.Primary_Treatment,
    dp.Total_Patients,
    dp.Dropout_Count,
    dp.Single_Visit_Dropout,
    dp.Dropout_Rate_Pct,

    -- Treatment review signals (apply to all treatment types)
    tr.Total_Treatment_Reviews,
    tr.Rating_1_Count                        AS Critical_Reviews,
    tr.Avg_Rating                            AS Treatment_Avg_Rating,
    tr.High_Risk_Rate_Pct                    AS Treatment_High_Risk_Rate_Pct,

    -- LAG to compare dropout rate against previous treatment
    LAG(dp.Dropout_Rate_Pct) OVER (
        ORDER BY dp.Dropout_Rate_Pct DESC
    )                                        AS Prev_Treatment_Dropout_Rate,

    -- Combined vulnerability signal
    CASE
        WHEN dp.Dropout_Rate_Pct > 30
         AND tr.Avg_Rating < 2.0  THEN 'CRITICAL — High dropout + poor reviews'
        WHEN dp.Dropout_Rate_Pct > 20 THEN 'HIGH — Significant dropout rate'
        WHEN dp.Dropout_Rate_Pct > 10 THEN 'MODERATE — Monitor'
        ELSE                               'STABLE'
    END                                      AS Combined_Risk_Signal

FROM dropout_patients dp
CROSS JOIN treatment_reviews tr   -- single-row aggregate, safe cross join
ORDER BY dp.Dropout_Rank;