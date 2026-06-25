import pandas as pd

print("\nTrust & Safety Intelligence Report")
print("=" * 70)

risk_metrics = pd.read_csv(
    "reports/trust_safety_metrics.csv"
)

severity = pd.read_csv(
    "reports/severity_distribution.csv"
)

bursts = pd.read_csv(
    "reports/review_burst_detection.csv"
)

repeat_reviewers = pd.read_csv(
    "reports/suspicious_reviewer_detection.csv"
)

print("\nKEY FINDINGS")
print("-" * 70)

safe_pct = risk_metrics.loc[
    risk_metrics["Metric"] == "Safe %",
    "Value"
].iloc[0]

needs_review_pct = risk_metrics.loc[
    risk_metrics["Metric"] == "Needs Review %",
    "Value"
].iloc[0]

high_risk_pct = risk_metrics.loc[
    risk_metrics["Metric"] == "High Risk %",
    "Value"
].iloc[0]

print(f"Safe Content: {safe_pct}%")
print(f"Needs Review: {needs_review_pct}%")
print(f"High Risk: {high_risk_pct}%")

print("\nSeverity Distribution")
print(severity)

print("\nBurst Events Detected")
print(len(bursts))

print("\nRepeat Reviewers Detected")
print(len(repeat_reviewers))

print("\nOVERALL ASSESSMENT")
print("-" * 70)

if high_risk_pct >= 10:
    print("Elevated risk environment detected.")
else:
    print("Low risk environment detected.")