SELECT
    Reviewer_Name,
    COUNT(*) AS Review_Count,
    ROUND(AVG(Rating), 2) AS Average_Rating
FROM Reviews
GROUP BY Reviewer_Name
HAVING COUNT(*) > 1
ORDER BY Review_Count DESC;