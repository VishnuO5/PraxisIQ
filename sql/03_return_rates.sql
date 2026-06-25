SELECT
    Returned_Patient,
    COUNT(*) AS Patient_Count
FROM Patients
GROUP BY Returned_Patient;