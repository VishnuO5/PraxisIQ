SELECT
    Label,
    COUNT(*) AS Complaint_Count,
    ROUND(AVG(Rating), 2) AS Avg_Rating,

    ROUND(
        COUNT(*) * (5 - AVG(Rating)),
        2
    ) AS Risk_Score

FROM Reviews

WHERE Label != 'Positive'

GROUP BY Label

ORDER BY Risk_Score DESC;