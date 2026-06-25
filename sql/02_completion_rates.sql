SELECT
    Treatment_Type,
    COUNT(*) AS Total_Visits,

    SUM(
        CASE
            WHEN Treatment_Status = 'Completed'
            THEN 1
            ELSE 0
        END
    ) AS Completed,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN Treatment_Status = 'Completed'
                THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS Completion_Rate

FROM Visits
GROUP BY Treatment_Type
ORDER BY Completion_Rate DESC;