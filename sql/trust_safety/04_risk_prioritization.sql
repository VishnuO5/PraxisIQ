SELECT
    Label,
    COUNT(*) AS Complaint_Count,
    ROUND(AVG(Rating), 2) AS Average_Rating
FROM Reviews
WHERE Label != 'Positive'
GROUP BY Label
ORDER BY Average_Rating ASC;