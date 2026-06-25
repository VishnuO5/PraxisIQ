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

    # 4. Follow-Up Compliance
    "followup_compliance": """
        SELECT
            Follow_Up_Required,
            Follow_Up_Completed,
            COUNT(*) AS Patient_Count
        FROM Patients
        GROUP BY
            Follow_Up_Required,
            Follow_Up_Completed;
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
    "high_risk_patients": """
        SELECT
            Patient_Id,
            Primary_Treatment,
            Follow_Up_Required,
            Follow_Up_Completed
        FROM Patients
        WHERE
            Follow_Up_Required = 'Y'
            AND
            Follow_Up_Completed = 'N';
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