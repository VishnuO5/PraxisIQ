SELECT
    Primary_Treatment,
    AVG(Total_Visits) AS Avg_Visits,
    COUNT(*) AS Patients
FROM Patients
GROUP BY Primary_Treatment
ORDER BY Avg_Visits DESC;