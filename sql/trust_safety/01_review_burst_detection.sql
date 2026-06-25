SELECT
    Review_Date,
    COUNT(*) AS Review_Count
FROM Reviews
GROUP BY Review_Date
HAVING COUNT(*) > 3
ORDER BY Review_Count DESC;