SELECT
    CASE
        WHEN Label = 'Positive'
        THEN 'Safe'
        ELSE 'Needs Review'
    END AS Moderation_Status,
    COUNT(*) AS Total_Reviews
FROM Reviews
GROUP BY Moderation_Status;