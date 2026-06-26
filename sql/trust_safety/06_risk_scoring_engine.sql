-- =============================================================================
-- 06_risk_scoring_engine.sql
-- Composite risk scoring engine for review categories
--
-- PREVIOUS VERSION (rejected): Risk_Score = COUNT(*) * (5 - AVG(Rating))
-- This was too simplistic — it only measured complaint volume and rating gap,
-- ignoring recency, severity distribution, and complaint acceleration.
--
-- CURRENT VERSION uses a composite model:
--   Base_Score     = COUNT(*) x category_severity_weight
--   Rating_Factor  = (5 - AVG(Rating)) / 4    [normalised 0-1]
--   Recency_Factor = weighted by reviews in last 90 days vs total
--   Velocity_Factor= MoM growth rate of complaints (from LAG)
--
--   Final_Risk_Score = Base_Score x Rating_Factor x (1 + Recency_Factor)
--                      x (1 + Velocity_Factor)
-- =============================================================================

WITH category_severity AS (
    SELECT 'Treatment'     AS Label, 5 AS severity_weight UNION ALL
    SELECT 'Communication',          4                    UNION ALL
    SELECT 'Staff',                  3                    UNION ALL
    SELECT 'Waiting Time',           2                    UNION ALL
    SELECT 'Pricing',                2                    UNION ALL
    SELECT 'Neutral',                1
),

monthly_complaints AS (
    SELECT
        Label,
        substr(Review_Date, 1, 7)         AS year_month,
        COUNT(*)                          AS monthly_count
    FROM Reviews
    WHERE Label NOT IN ('Positive')
    GROUP BY Label, year_month
),

velocity AS (
    SELECT Label, current_month_count, prev_month_count
    FROM (
        SELECT
            Label,
            monthly_count                 AS current_month_count,
            LAG(monthly_count, 1) OVER (
                PARTITION BY Label ORDER BY year_month
            )                             AS prev_month_count,
            ROW_NUMBER() OVER (
                PARTITION BY Label ORDER BY year_month DESC
            )                             AS rn
        FROM monthly_complaints
    )
    WHERE rn = 1
),

base_metrics AS (
    SELECT
        r.Label,
        COUNT(*)                                        AS total_complaints,
        ROUND(AVG(r.Rating), 3)                         AS avg_rating,
        COUNT(CASE WHEN r.Rating = 1 THEN 1 END)        AS one_star_count,
        COUNT(CASE WHEN r.Rating = 2 THEN 1 END)        AS two_star_count,
        COUNT(CASE
            WHEN julianday('now') - julianday(r.Review_Date) <= 90
            THEN 1 END)                                 AS recent_90d_count,
        MIN(r.Review_Date)                              AS first_complaint_date,
        MAX(r.Review_Date)                              AS latest_complaint_date
    FROM Reviews r
    WHERE r.Label NOT IN ('Positive')
    GROUP BY r.Label
),

scored AS (
    SELECT
        bm.Label,
        bm.total_complaints,
        bm.avg_rating,
        bm.one_star_count,
        bm.recent_90d_count,
        bm.first_complaint_date,
        bm.latest_complaint_date,
        cs.severity_weight,

        ROUND((5.0 - bm.avg_rating) / 4.0, 3)          AS rating_factor,

        ROUND(
            bm.recent_90d_count * 1.0 / NULLIF(bm.total_complaints, 0),
            3
        )                                               AS recency_factor,

        CASE
            WHEN v.prev_month_count IS NULL OR v.prev_month_count = 0 THEN 0
            ELSE ROUND(
                (v.current_month_count - v.prev_month_count) * 1.0
                / v.prev_month_count, 3
            )
        END                                             AS velocity_factor,

        ROUND(
            bm.total_complaints
            * cs.severity_weight
            * ((5.0 - bm.avg_rating) / 4.0)
            * (1 + bm.recent_90d_count * 1.0 / NULLIF(bm.total_complaints, 0))
            * (1 + CASE
                    WHEN v.prev_month_count IS NULL OR v.prev_month_count = 0 THEN 0
                    ELSE (v.current_month_count - v.prev_month_count) * 1.0 / v.prev_month_count
                   END),
            2
        )                                               AS Composite_Risk_Score

    FROM base_metrics bm
    LEFT JOIN category_severity cs ON bm.Label = cs.Label
    LEFT JOIN velocity v           ON bm.Label = v.Label
)

SELECT
    RANK() OVER (ORDER BY Composite_Risk_Score DESC) AS Risk_Rank,
    Label                    AS Category,
    Composite_Risk_Score,
    total_complaints         AS Total_Complaints,
    avg_rating               AS Avg_Rating,
    one_star_count           AS One_Star_Count,
    recent_90d_count         AS Recent_90d_Complaints,
    severity_weight          AS Category_Severity_Weight,
    rating_factor            AS Rating_Factor_0to1,
    recency_factor           AS Recency_Factor_0to1,
    velocity_factor          AS MoM_Velocity,
    first_complaint_date     AS First_Complaint,
    latest_complaint_date    AS Latest_Complaint,
    CASE
        WHEN Composite_Risk_Score >= 30 THEN 'CRITICAL'
        WHEN Composite_Risk_Score >= 15 THEN 'HIGH'
        WHEN Composite_Risk_Score >= 5  THEN 'MEDIUM'
        ELSE                                 'LOW'
    END                      AS Risk_Level
FROM scored
ORDER BY Composite_Risk_Score DESC;