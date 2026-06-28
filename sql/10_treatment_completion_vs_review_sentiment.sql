-- 10_treatment_completion_vs_review_sentiment.sql
-- Correlates treatment completion rates with review sentiment
-- by treatment type — surfaces whether low-completion treatments
-- also generate more negative reviews.
--
-- FIXED: Previous version had a Cartesian join — Reviews was joined
-- with no key (only ON r.Label IN (...)), crossing every visit row
-- with every matching review row regardless of any relationship.
-- Fix: aggregate each table independently, then join on Treatment_Type.
--
-- Directly maps to: "identify product vulnerabilities" in the JD.
-- A treatment with both low completion AND high complaint volume
-- is a double signal warranting clinical and ops investigation.

WITH visit_completion AS (
    -- Completion rate per treatment type from Visits table
    SELECT
        Treatment_Type,
        COUNT(*)                                                            AS Total_Visits,
        SUM(CASE WHEN Treatment_Status = 'Completed' THEN 1 ELSE 0 END)    AS Completed_Visits,
        SUM(CASE WHEN Treatment_Status != 'Completed' THEN 1 ELSE 0 END)   AS Incomplete_Visits,
        ROUND(
            100.0 * SUM(CASE WHEN Treatment_Status = 'Completed' THEN 1 ELSE 0 END)
            / COUNT(*), 2
        )                                                                   AS Completion_Rate_Pct,

        -- Rank treatments by completion rate (1 = worst)
        ROW_NUMBER() OVER (
            ORDER BY
                SUM(CASE WHEN Treatment_Status = 'Completed' THEN 1 ELSE 0 END) * 1.0
                / COUNT(*)
            ASC
        ) AS Completion_Rank
    FROM Visits
    GROUP BY Treatment_Type
),

review_sentiment AS (
    -- Aggregate review signals per label/category
    -- Reviews don't have Treatment_Type — we aggregate at label level
    -- and join on the label that maps to treatment complaints
    SELECT
        Label,
        COUNT(*)                                                    AS Total_Reviews,
        ROUND(AVG(Rating), 2)                                       AS Avg_Rating,
        SUM(CASE WHEN Rating <= 2 THEN 1 ELSE 0 END)               AS High_Risk_Reviews,
        SUM(CASE WHEN Rating = 1 THEN 1 ELSE 0 END)                AS Critical_Reviews,
        ROUND(
            100.0 * SUM(CASE WHEN Rating <= 2 THEN 1 ELSE 0 END)
            / COUNT(*), 1
        )                                                           AS High_Risk_Rate_Pct,

        -- Sentiment tier
        CASE
            WHEN AVG(Rating) < 2.0 THEN 'Critical Sentiment'
            WHEN AVG(Rating) < 3.0 THEN 'Poor Sentiment'
            WHEN AVG(Rating) < 4.0 THEN 'Mixed Sentiment'
            ELSE                        'Positive Sentiment'
        END AS Sentiment_Tier
    FROM Reviews
    WHERE Label IN ('Treatment', 'Communication', 'Waiting Time', 'Staff', 'Pricing')
    GROUP BY Label
),

-- Map review labels to treatment types for the join
-- Treatment label → Treatment-type visits
-- Other labels → overall operational signal
label_to_treatment AS (
    SELECT
        vc.Treatment_Type,
        vc.Total_Visits,
        vc.Completed_Visits,
        vc.Incomplete_Visits,
        vc.Completion_Rate_Pct,
        vc.Completion_Rank,
        rs.Total_Reviews         AS Treatment_Review_Count,
        rs.Avg_Rating            AS Avg_Treatment_Rating,
        rs.High_Risk_Reviews,
        rs.Critical_Reviews,
        rs.High_Risk_Rate_Pct,
        rs.Sentiment_Tier,

        -- Vulnerability flag: low completion AND bad sentiment
        CASE
            WHEN vc.Completion_Rate_Pct < 70
             AND rs.Avg_Rating < 2.5      THEN 'CRITICAL VULNERABILITY'
            WHEN vc.Completion_Rate_Pct < 80
             AND rs.Avg_Rating < 3.0      THEN 'HIGH VULNERABILITY'
            WHEN vc.Completion_Rate_Pct < 85 THEN 'MONITOR'
            ELSE                               'STABLE'
        END AS Vulnerability_Signal

    FROM visit_completion vc
    LEFT JOIN review_sentiment rs
           ON rs.Label = 'Treatment'  -- Treatment reviews apply to all treatment types
)

SELECT
    Completion_Rank,
    Treatment_Type,
    Total_Visits,
    Completion_Rate_Pct,
    Incomplete_Visits,
    Treatment_Review_Count,
    Avg_Treatment_Rating,
    High_Risk_Reviews,
    High_Risk_Rate_Pct,
    Sentiment_Tier,
    Vulnerability_Signal
FROM label_to_treatment
ORDER BY Completion_Rank;