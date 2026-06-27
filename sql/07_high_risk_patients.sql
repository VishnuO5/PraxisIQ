-- 07_high_risk_patients.sql
-- Identifies high-risk patients using three real signals:
--   1. Never returned (Returned_Patient = 'No')
--   2. Single visit only (Total_Visits = 1)
--   3. High-complexity treatment (Root Canal, Implant, Braces, etc.)
-- Uses real schema columns only. Replaces the original query which
-- referenced Follow_Up_Required and Follow_Up_Completed (do not exist).

SELECT
    Patient_Id,
    Age,
    Gender,
    Primary_Treatment,
    Total_Visits,
    Returned_Patient,
    CASE
        WHEN Returned_Patient = 'No'
             AND Total_Visits = 1
             AND Primary_Treatment IN (
                 'Root Canal', 'Implant', 'Metal Braces Treatment',
                 'Aligner', 'Gum Treatment', 'Fixed Bridge',
                 'Partial Denture', 'Complete Denture',
                 'Deep Scaling and Root Planing', 'Crown/Cap'
             ) THEN 'CRITICAL'
        WHEN Returned_Patient = 'No' AND Total_Visits = 1 THEN 'HIGH'
        WHEN Returned_Patient = 'No' THEN 'MEDIUM'
        ELSE 'LOW'
    END AS Risk_Tier
FROM Patients
WHERE Returned_Patient = 'No'
ORDER BY
    CASE
        WHEN Returned_Patient = 'No' AND Total_Visits = 1
             AND Primary_Treatment IN (
                 'Root Canal', 'Implant', 'Metal Braces Treatment',
                 'Aligner', 'Gum Treatment', 'Fixed Bridge',
                 'Partial Denture', 'Complete Denture',
                 'Deep Scaling and Root Planing', 'Crown/Cap'
             ) THEN 1
        WHEN Returned_Patient = 'No' AND Total_Visits = 1 THEN 2
        WHEN Returned_Patient = 'No' THEN 3
        ELSE 4
    END,
    Age DESC;