-- =============================================================================
-- 04_risk_prioritization.sql
-- Build a moderation queue ranked by composite risk priority
--
-- Method: Each review gets a composite Risk_Priority_Score combining:
--   (1) Category severity weight (Treatment > Communication > Staff > others)
--   (2) Star rating (lower = higher risk)
--   (3) Recency (reviews in last 30 days weighted higher)
--   (4) Reviewer history (repeat low-rater flag)
--
-- Uses ROW_NUMBER() to assign a moderation queue position.
-- =============================================================================

WITH reviewer_history AS (
    SELECT
        Reviewer_Name,
        COUNT(*)                                    AS prior_reviews,
        ROUND(AVG(Rating), 2)                       AS historical_avg_rating,
        CASE WHEN COUNT(*) > 1 AND AVG(Rating) < 3
             THEN 1 ELSE 0
        END                                         AS is_repeat_low_rater
    FROM Reviews
    GROUP BY Reviewer_Name
),

review_scored AS (
    SELECT
        r.Review_ID,
        r.Reviewer_Name,
        r.Review_Date,
        r.Rating,
        r.Label,
        r.Review_Text,
        rh.prior_reviews,
        rh.historical_avg_rating,
        rh.is_repeat_low_rater,

        CASE r.Label
            WHEN 'Treatment'     THEN 5
            WHEN 'Communication' THEN 4
            WHEN 'Staff'         THEN 3
            WHEN 'Waiting Time'  THEN 2
            WHEN 'Pricing'       THEN 2
            WHEN 'Neutral'       THEN 1
            ELSE 0
        END AS category_weight,

        CASE
            WHEN julianday('now') - julianday(r.Review_Date) <= 30
            THEN 1.5 ELSE 1.0
        END AS recency_multiplier,

        ROUND(
            (
                CASE r.Label
                    WHEN 'Treatment'     THEN 5
                    WHEN 'Communication' THEN 4
                    WHEN 'Staff'         THEN 3
                    WHEN 'Waiting Time'  THEN 2
                    WHEN 'Pricing'       THEN 2
                    WHEN 'Neutral'       THEN 1
                    ELSE 0
                END
                * (6 - r.Rating)
                * CASE
                    WHEN julianday('now') - julianday(r.Review_Date) <= 30
                    THEN 1.5 ELSE 1.0
                  END
                * (1 + 0.2 * CASE WHEN rh.is_repeat_low_rater = 1 THEN 1 ELSE 0 END)
            ), 2
        ) AS Risk_Priority_Score

    FROM Reviews r
    LEFT JOIN reviewer_history rh ON r.Reviewer_Name = rh.Reviewer_Name
    WHERE r.Label NOT IN ('Positive')
),

queue_ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (ORDER BY Risk_Priority_Score DESC) AS Queue_Position,
        CASE
            WHEN Risk_Priority_Score >= 20 THEN 'TIER 1 — Immediate Review'
            WHEN Risk_Priority_Score >= 10 THEN 'TIER 2 — Review within 24h'
            ELSE                                'TIER 3 — Weekly Batch Review'
        END AS Moderation_Tier
    FROM review_scored
)

SELECT
    Queue_Position,
    Moderation_Tier,
    Review_Date,
    Reviewer_Name,
    Rating,
    Label                    AS Category,
    Risk_Priority_Score,
    prior_reviews            AS Reviewer_Prior_Reviews,
    is_repeat_low_rater      AS Repeat_Low_Rater_Flag,
    substr(Review_Text, 1, 120) AS Review_Preview
FROM queue_ranked
ORDER BY Queue_Position
LIMIT 50;