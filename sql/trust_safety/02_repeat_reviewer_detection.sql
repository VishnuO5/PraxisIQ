-- =============================================================================
-- 02_repeat_reviewer_detection.sql
-- Identify reviewers who submitted multiple reviews — potential manipulation
--
-- Method: Rank reviewers by review count, calculate rating variance,
--         flag suspicious patterns (multiple low-rating reviews, inconsistent
--         ratings from same source). Uses RANK() window function.
-- =============================================================================

WITH reviewer_profile AS (
    SELECT
        Reviewer_Name,
        COUNT(*)                                         AS total_reviews,
        ROUND(AVG(Rating), 2)                            AS avg_rating,
        MIN(Rating)                                      AS min_rating,
        MAX(Rating)                                      AS max_rating,
        MAX(Rating) - MIN(Rating)                        AS rating_spread,
        MIN(Review_Date)                                 AS first_review_date,
        MAX(Review_Date)                                 AS last_review_date,
        COUNT(CASE WHEN Rating <= 2 THEN 1 END)          AS low_rating_count,
        COUNT(CASE WHEN Label = 'Treatment' THEN 1 END)  AS treatment_complaints,
        GROUP_CONCAT(Label, ' | ')                       AS review_labels
    FROM Reviews
    GROUP BY Reviewer_Name
    HAVING COUNT(*) > 1
),

reviewer_ranked AS (
    SELECT
        Reviewer_Name,
        total_reviews,
        avg_rating,
        min_rating,
        max_rating,
        rating_spread,
        first_review_date,
        last_review_date,
        julianday(last_review_date) - julianday(first_review_date) AS days_between_reviews,
        low_rating_count,
        treatment_complaints,
        review_labels,
        RANK() OVER (ORDER BY total_reviews DESC)        AS volume_rank,
        RANK() OVER (ORDER BY avg_rating ASC)            AS lowest_avg_rank,
        CASE
            WHEN total_reviews >= 3 AND avg_rating < 2.5
                THEN 'HIGH RISK — Serial Low Rater'
            WHEN total_reviews >= 2 AND treatment_complaints >= 1 AND avg_rating < 3
                THEN 'MEDIUM RISK — Repeat Treatment Complaint'
            WHEN rating_spread >= 3
                THEN 'REVIEW INCONSISTENCY — Same reviewer, very different ratings'
            ELSE 'MONITOR'
        END AS risk_flag
    FROM reviewer_profile
)

SELECT
    volume_rank                 AS Rank,
    Reviewer_Name,
    total_reviews               AS Total_Reviews,
    avg_rating                  AS Avg_Rating,
    rating_spread               AS Rating_Spread,
    days_between_reviews        AS Days_Between_First_Last,
    low_rating_count            AS Low_Rating_Count,
    treatment_complaints        AS Treatment_Complaints,
    review_labels               AS Labels_Reviewed,
    risk_flag                   AS Risk_Flag
FROM reviewer_ranked
ORDER BY
    CASE risk_flag
        WHEN 'HIGH RISK — Serial Low Rater' THEN 1
        WHEN 'MEDIUM RISK — Repeat Treatment Complaint' THEN 2
        WHEN 'REVIEW INCONSISTENCY — Same reviewer, very different ratings' THEN 3
        ELSE 4
    END,
    total_reviews DESC;