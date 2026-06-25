SELECT
    Label,
    substr(Review_Date, 1, 7) AS Month,
    COUNT(*) AS Review_Count

FROM Reviews

WHERE Label != 'Positive'

GROUP BY
    Label,
    Month

ORDER BY
    Month,
    Review_Count DESC;