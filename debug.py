import pandas as pd

master = pd.read_csv("master_dataset.csv", encoding="utf-8-sig")

print("Stations with District == 'nan':")
print(master.loc[master["District"] == "nan", "station"].value_counts())

print("\nMissing weather by District:")
weather_cols = ["rain_mm", "daily_mean_wspd", "daily_mean_temp"]
print(master.groupby("District")[weather_cols].apply(lambda x: x.isna().mean()))