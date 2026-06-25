SELECT
    Treatment_Type,
    COUNT(*) AS Total_Count
FROM Visits
GROUP BY Treatment_Type
ORDER BY Total_Count DESC;