-- High-risk patients cross-referenced with negative Treatment reviews
-- Joins Patients + Visits + Reviews to identify whether patients who
-- did not complete follow-up are also generating Treatment complaints
-- This mirrors T&S investigation workflows: correlating behavioral
-- signals (non-compliance) with content signals (negative reviews)

SELECT
    p.Patient_Id,
    p.Primary_Treatment,
    p.Total_Visits,
    p.Returned_Patient,
    COUNT(v.Visit_ID) AS Incomplete_Visits,
    r.Review_Text,
    r.Rating,
    r.Label

FROM Patients p

JOIN Visits v
    ON p.Patient_Id = v.Patient_ID
    AND v.Treatment_Status != 'Completed'

JOIN Reviews r
    ON r.Label = 'Treatment'
    AND r.Rating <= 2

WHERE
    p.Primary_Treatment = 'Root Canal'

ORDER BY
    p.Total_Visits DESC,
    r.Rating ASC

LIMIT 20;