SELECT
    Primary_Treatment,
    ROUND(AVG(Total_Visits), 2) AS Avg_Visits,
    COUNT(*) AS Patients
FROM Patients
GROUP BY Primary_Treatment
ORDER BY Avg_Visits DESC;