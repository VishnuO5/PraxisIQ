SELECT
    Label,
    COUNT(*) AS Review_Count,
    ROUND(
        100.0 * COUNT(*) /
        (SELECT COUNT(*) FROM Reviews),
        2
    ) AS Percentage
FROM Reviews
WHERE Label != 'Positive'
GROUP BY Label
ORDER BY Review_Count DESC;