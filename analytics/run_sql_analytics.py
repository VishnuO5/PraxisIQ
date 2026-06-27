import sqlite3
import pandas as pd

# Connect to SQLite database
conn = sqlite3.connect("PraxisIQ.db")

# All SQL Analytics Queries
queries = {

    # 1. Most Common Treatments
    "common_treatments": """
        SELECT
            Treatment_Type,
            COUNT(*) AS Total_Count
        FROM Visits
        GROUP BY Treatment_Type
        ORDER BY Total_Count DESC;
    """,

    # 2. Treatment Completion Rates
    "completion_rates": """
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
    """,

    # 3. Patient Return Rates
    "return_rates": """
        SELECT
            Returned_Patient,
            COUNT(*) AS Patient_Count
        FROM Patients
        GROUP BY Returned_Patient;
    """,

    # 4. Dropout Compliance by Treatment
    # Note: Follow_Up_Required/Completed columns do not exist in real schema.
    # Rewritten using Returned_Patient and Total_Visits (real columns).
    "followup_compliance": """
        SELECT
            Primary_Treatment,
            COUNT(*) AS Total_Patients,
            SUM(CASE WHEN Returned_Patient = 'No'  THEN 1 ELSE 0 END) AS Never_Returned,
            SUM(CASE WHEN Returned_Patient = 'Yes' THEN 1 ELSE 0 END) AS Returned,
            ROUND(
                100.0 * SUM(CASE WHEN Returned_Patient = 'No' THEN 1 ELSE 0 END)
                / COUNT(*), 2
            ) AS Dropout_Rate_Pct
        FROM Patients
        GROUP BY Primary_Treatment
        ORDER BY Dropout_Rate_Pct DESC;
    """,

    # 5. Average Visits by Treatment
    "average_visits": """
        SELECT
            Primary_Treatment,
            ROUND(AVG(Total_Visits), 2) AS Avg_Visits,
            COUNT(*) AS Patients
        FROM Patients
        GROUP BY Primary_Treatment
        ORDER BY Avg_Visits DESC;
    """,

    # 6. Monthly Treatment Trends
    "treatment_trends": """
        SELECT
            substr(Visit_Date, 1, 7) AS Month,
            Treatment_Type,
            COUNT(*) AS Visit_Count
        FROM Visits
        GROUP BY
            Month,
            Treatment_Type
        ORDER BY Month;
    """,

    # 7. High Risk Patients
    # Note: Follow_Up_Required/Completed columns do not exist in real schema.
    # Rewritten using Returned_Patient, Total_Visits, Primary_Treatment (real columns).
    "high_risk_patients": """
        SELECT
            Patient_Id,
            Age,
            Gender,
            Primary_Treatment,
            Total_Visits,
            Returned_Patient,
            CASE
                WHEN Returned_Patient = 'No'
                     AND Total_Visits = 1
                     AND Primary_Treatment IN (
                         'Root Canal', 'Implant', 'Metal Braces Treatment',
                         'Aligner', 'Gum Treatment', 'Fixed Bridge',
                         'Partial Denture', 'Complete Denture',
                         'Deep Scaling and Root Planing', 'Crown/Cap'
                     ) THEN 'CRITICAL'
                WHEN Returned_Patient = 'No' AND Total_Visits = 1 THEN 'HIGH'
                WHEN Returned_Patient = 'No' THEN 'MEDIUM'
                ELSE 'LOW'
            END AS Risk_Tier
        FROM Patients
        WHERE Returned_Patient = 'No'
        ORDER BY Total_Visits ASC, Age DESC;
    """,

    # 8. Behavioral Insights
    "behavioral_insights": """
        SELECT
            Primary_Treatment,
            AVG(Total_Visits) AS Avg_Visits,
            COUNT(*) AS Patients
        FROM Patients
        GROUP BY Primary_Treatment
        ORDER BY Avg_Visits DESC;
    """
}

# Execute all reports
for report_name, query in queries.items():

    print("\n" + "=" * 60)
    print(f"Generating Report: {report_name}")
    print("=" * 60)

    df = pd.read_sql_query(query, conn)

    print(df.head())

    output_file = f"reports/{report_name}.csv"

    df.to_csv(
        output_file,
        index=False
    )

    print(f"\nSaved: {output_file}")

# Close connection
conn.close()

print("\n" + "=" * 60)
print("ALL ANALYTICS REPORTS GENERATED SUCCESSFULLY")
print("=" * 60)