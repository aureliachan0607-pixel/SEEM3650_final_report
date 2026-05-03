import pandas as pd

def read_csv_try_encodings(file_path):
    encodings_to_try = ["utf-8", "utf-8-sig", "big5", "cp950", "latin1"]
    
    for enc in encodings_to_try:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            print(f"Successfully read {file_path} with encoding={enc}")
            return df
        except Exception as e:
            print(f"Failed with encoding={enc}: {e}")
    
    raise ValueError(f"Unable to read file: {file_path}")

# =========================
# 1. Read datasets
# =========================
aqhi = read_csv_try_encodings("aqhi_final_combined.csv")
rain = read_csv_try_encodings("rainfall_complete_mapped.csv")
wind = read_csv_try_encodings("wind_mean_mapped.csv")
temp = read_csv_try_encodings("temperature_complete_mapped.csv")

# =========================
# 2. Standardize basic format
# =========================
for df in [aqhi, rain, wind, temp]:
    df.columns = df.columns.str.strip()
    df["date"] = pd.to_datetime(df["date"])
    df["District"] = df["District"].astype(str).str.strip()

# =========================
# 3. Keep only needed columns
# =========================
aqhi_keep = [
    "date", "station", "District", "District_no", "index_right",
    "daily_max_aqhi", "daily_mean_aqhi",
    "hourly_count", "starred_hours",
    "lag1_aqhi", "lag2_aqhi", "lag3_aqhi", "lag7_aqhi",
    "rolling3_mean_aqhi", "rolling7_mean_aqhi", "rolling14_mean_aqhi",
    "target_next_day", "high_risk_next_day",
    "year", "month", "day", "day_of_week", "is_weekend"
]
aqhi = aqhi[aqhi_keep].copy()

rain_keep = [
    "date", "District",
    "rain_mm_imputed", "rain_trace_flag", "rain_occurrence_flag"
]
rain = rain[rain_keep].copy()
rain = rain.rename(columns={"rain_mm_imputed": "rain_mm"})

wind_keep = [
    "date", "District",
    "daily_mean_wspd"
]
wind = wind[wind_keep].copy()

temp_keep = [
    "date", "District",
    "daily_mean_temp", "daily_max_temp", "daily_min_temp"
]
temp = temp[temp_keep].copy()

# =========================
# 4. Duplicate checks before merge
# =========================
print("\n=== Duplicate checks before merge ===")
print("AQHI duplicates by [date, District, station]:",
      aqhi.duplicated(subset=["date", "District", "station"]).sum())

print("Rain duplicates by [date, District]:",
      rain.duplicated(subset=["date", "District"]).sum())

print("Wind duplicates by [date, District]:",
      wind.duplicated(subset=["date", "District"]).sum())

print("Temp duplicates by [date, District]:",
      temp.duplicated(subset=["date", "District"]).sum())

# Drop duplicate rows in weather data if any
rain = rain.drop_duplicates(subset=["date", "District"])
wind = wind.drop_duplicates(subset=["date", "District"])
temp = temp.drop_duplicates(subset=["date", "District"])

# =========================
# 5. Merge
# =========================
master = aqhi.merge(rain, on=["date", "District"], how="left")
master = master.merge(wind, on=["date", "District"], how="left")
master = master.merge(temp, on=["date", "District"], how="left")

# =========================
# 6. Post-merge checks
# =========================
print("\n=== Master dataset summary ===")
print("Shape:", master.shape)

print("\nMissing rate by column:")
print(master.isna().mean().sort_values(ascending=False))

print("\nDuplicated full rows:", master.duplicated().sum())

print("\nDuplicated AQHI keys [date, District, station]:")
print(master.duplicated(subset=["date", "District", "station"]).sum())



print("\nTarget distribution: target_next_day")
print(master["target_next_day"].value_counts(dropna=False))
print(master["target_next_day"].value_counts(normalize=True, dropna=False))

print("\nTarget distribution: high_risk_next_day")
print(master["high_risk_next_day"].value_counts(dropna=False))
print(master["high_risk_next_day"].value_counts(normalize=True, dropna=False))

print("\nDistrict counts:")
print(master["District"].value_counts())

print("\nStation counts:")
print(master["station"].value_counts())

# =========================
# 7. Clean target missing rows
# =========================
master = master.dropna(subset=["target_next_day", "high_risk_next_day"])

master["target_next_day"] = master["target_next_day"].astype(int)
master["high_risk_next_day"] = master["high_risk_next_day"].astype(int)

# =========================
# 8. Save
# =========================
master.to_csv("master_datasetv1.csv", index=False, encoding="utf-8-sig")
print("\nSaved: master_datasetv1.csv")