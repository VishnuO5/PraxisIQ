-- Treatment completion rate compared against review sentiment by treatment type
-- Joins Visits + Reviews to surface whether low completion rates
-- correlate with negative review categories
-- Directly maps to: "identify product vulnerabilities" in the JD

SELECT
    v.Treatment_Type,
    COUNT(v.Visit_ID) AS Total_Visits,

    ROUND(
        100.0 * SUM(
            CASE WHEN v.Treatment_Status = 'Completed' THEN 1 ELSE 0 END
        ) / COUNT(v.Visit_ID),
        2
    ) AS Completion_Rate_Pct,

    COUNT(r.Review_ID) AS Total_Reviews,

    ROUND(AVG(r.Rating), 2) AS Avg_Review_Rating,

    SUM(
        CASE WHEN r.Label = 'Treatment' AND r.Rating <= 2
        THEN 1 ELSE 0 END
    ) AS High_Risk_Reviews

FROM Visits v

LEFT JOIN Reviews r
    ON r.Label IN ('Treatment', 'Communication', 'Waiting Time', 'Staff', 'Pricing')

GROUP BY
    v.Treatment_Type

ORDER BY
    Completion_Rate_Pct ASC;