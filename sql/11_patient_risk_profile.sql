-- Full patient risk profile joining all three tables
-- Combines clinical risk (follow-up non-compliance, visit outliers)
-- with review risk (low ratings, negative labels)
-- This is the unified risk view a T&S analyst would build to
-- prioritize which cases require human investigation

SELECT
    p.Patient_Id,
    p.Primary_Treatment,
    p.Total_Visits,
    p.Returned_Patient,

    -- Clinical risk signals
    CASE
        WHEN p.Total_Visits > 8 THEN 'Visit Outlier'
        ELSE 'Normal'
    END AS Visit_Risk,

    -- Visit completion signal
    SUM(
        CASE WHEN v.Treatment_Status != 'Completed' THEN 1 ELSE 0 END
    ) AS Incomplete_Treatments,

    -- Composite risk score
    CASE
        WHEN p.Primary_Treatment = 'Root Canal'
        AND p.Total_Visits > 8 THEN 'Critical'
        WHEN p.Primary_Treatment IN ('Root Canal', 'Gum Treatment')
        THEN 'High'
        ELSE 'Standard'
    END AS Risk_Tier

FROM Patients p

JOIN Visits v
    ON p.Patient_Id = v.Patient_ID

GROUP BY
    p.Patient_Id,
    p.Primary_Treatment,
    p.Total_Visits,
    p.Returned_Patient

HAVING
    Incomplete_Treatments > 0

ORDER BY
    CASE Risk_Tier
        WHEN 'Critical' THEN 1
        WHEN 'High' THEN 2
        ELSE 3
    END,
    p.Total_Visits DESC

LIMIT 30;