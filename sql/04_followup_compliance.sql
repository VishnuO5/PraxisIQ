-- 04_dropout_compliance.sql
-- Patients who never returned after their first visit, grouped by treatment.
-- Uses real schema columns: Returned_Patient, Total_Visits, Primary_Treatment.
-- Replaces the original followup_compliance.sql which referenced
-- Follow_Up_Required and Follow_Up_Completed (columns that do not exist).

SELECT
    Primary_Treatment,
    COUNT(*)                                          AS Total_Patients,
    SUM(CASE WHEN Returned_Patient = 'No'  THEN 1 ELSE 0 END) AS Never_Returned,
    SUM(CASE WHEN Returned_Patient = 'Yes' THEN 1 ELSE 0 END) AS Returned,
    ROUND(
        100.0 * SUM(CASE WHEN Returned_Patient = 'No' THEN 1 ELSE 0 END)
        / COUNT(*), 2
    )                                                  AS Dropout_Rate_Pct
FROM Patients
GROUP BY Primary_Treatment
ORDER BY Dropout_Rate_Pct DESC;