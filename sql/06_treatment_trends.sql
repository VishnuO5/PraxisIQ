SELECT
    substr(Visit_Date, 1, 7) AS Month,
    Treatment_Type,
    COUNT(*) AS Visit_Count
FROM Visits
GROUP BY
    Month,
    Treatment_Type
ORDER BY Month;