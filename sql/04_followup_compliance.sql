SELECT
    Follow_Up_Required,
    Follow_Up_Completed,
    COUNT(*) AS Patient_Count
FROM Patients
GROUP BY
    Follow_Up_Required,
    Follow_Up_Completed;