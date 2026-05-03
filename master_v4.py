import pandas as pd




master = pd.read_csv("master_datasetv1.csv", encoding="utf-8-sig")


# Drop rows with missing target

master = master.dropna(subset=["high_risk_next_day"]).copy()
master["high_risk_next_day"] = master["high_risk_next_day"].astype(int)


# Create missing flags BEFORE imputation

master["rain_missing_flag"] = master["rain_mm"].isna().astype(int)
master["wind_missing_flag"] = master["daily_mean_wspd"].isna().astype(int)
master["temp_missing_flag"] = (
    master[["daily_mean_temp", "daily_max_temp", "daily_min_temp"]]
    .isna()
    .any(axis=1)
    .astype(int)
)


# Rainfall imputation

master["rain_mm"] = master["rain_mm"].fillna(0)
master["rain_trace_flag"] = master["rain_trace_flag"].fillna(0)
master["rain_occurrence_flag"] = master["rain_occurrence_flag"].fillna(0)


# Wind imputation:
# 1) District + month median
# 2) month median
# 3) overall median

master["daily_mean_wspd"] = master["daily_mean_wspd"].fillna(
    master.groupby(["District", "month"])["daily_mean_wspd"].transform("median")
)
master["daily_mean_wspd"] = master["daily_mean_wspd"].fillna(
    master.groupby("month")["daily_mean_wspd"].transform("median")
)
master["daily_mean_wspd"] = master["daily_mean_wspd"].fillna(
    master["daily_mean_wspd"].median()
)


# Temperature imputation:
# 1) District + month median
# 2) month median
# 3) overall median

temp_cols = ["daily_mean_temp", "daily_max_temp", "daily_min_temp"]

for col in temp_cols:
    master[col] = master[col].fillna(
        master.groupby(["District", "month"])[col].transform("median")
    )
    master[col] = master[col].fillna(
        master.groupby("month")[col].transform("median")
    )
    master[col] = master[col].fillna(master[col].median())


# Convert rain flags to int

master["rain_trace_flag"] = master["rain_trace_flag"].astype(int)
master["rain_occurrence_flag"] = master["rain_occurrence_flag"].astype(int)


# Check

print("Shape after cleaning:", master.shape)

print("\nRemaining missing rate:")
print(master.isna().mean().sort_values(ascending=False).head(20))

print("\nTarget distribution:")
print(master["high_risk_next_day"].value_counts())
print(master["high_risk_next_day"].value_counts(normalize=True))

print("\nMissing flag rates:")
print(master[["rain_missing_flag", "wind_missing_flag", "temp_missing_flag"]].mean())

print("\nDistrict-level missing flag means:")
print(master.groupby("District")[["rain_missing_flag", "wind_missing_flag", "temp_missing_flag"]].mean())


# Save

master.to_csv("master_dataset_model_ready_v4.csv", index=False, encoding="utf-8-sig")
print("\nSaved: master_dataset_model_ready_v4.csv")