import pandas as pd
import geopandas as gpd
import requests

# 1. Load data using relative paths
aqhi_df = pd.read_csv('aqhi_daily_202301_202604.csv')
pollutant_meta = pd.read_csv('PollutantConcentration.csv')

# Clean column names
aqhi_df.columns = aqhi_df.columns.str.strip()
pollutant_meta.columns = pollutant_meta.columns.str.strip()

# 2. Convert coordinates (DMS to Decimal)
def dms_to_decimal(dms_str):
    try:
        parts = [float(p) for p in str(dms_str).split('-')]
        return parts[0] + parts[1]/60 + parts[2]/3600
    except:
        return None

pollutant_meta['LAT_DECIMAL'] = pollutant_meta['LATITUDE'].apply(dms_to_decimal)
pollutant_meta['LON_DECIMAL'] = pollutant_meta['LONGITUDE'].apply(dms_to_decimal)

# 3. Spatial Join for Districts
gdf_stations = gpd.GeoDataFrame(
    pollutant_meta,
    geometry=gpd.points_from_xy(pollutant_meta["LON_DECIMAL"], pollutant_meta["LAT_DECIMAL"]),
    crs="EPSG:4326"
)

dist_url = "https://www.had.gov.hk/psi/hong-kong-administrative-boundaries/hksar_18_district_boundary.json"
districts = gpd.GeoDataFrame.from_features(requests.get(dist_url).json()["features"], crs="EPSG:4326")
pollutant_mapped = gpd.sjoin(gdf_stations, districts, how="left", predicate="within")

# 4. Filter AQHI Columns
keep_columns = [
    'date', 'station', 'daily_max_aqhi', 'daily_mean_aqhi', 'hourly_count', 
    'starred_hours', 'lag1_aqhi', 'lag2_aqhi', 'lag3_aqhi', 'lag7_aqhi', 
    'rolling3_mean_aqhi', 'rolling7_mean_aqhi', 'rolling14_mean_aqhi', 
    'target_next_day', 'high_risk_next_day', 'year', 'month', 'day', 
    'day_of_week', 'is_weekend'
]
existing_aqhi_cols = [col for col in keep_columns if col in aqhi_df.columns]
aqhi_df = aqhi_df[existing_aqhi_cols]

# 5. Merge and Remove the redundant column
mapping_ref = pollutant_mapped[['StationName', 'index_right', '地區號碼', 'District']].drop_duplicates()

merged_aqhi = pd.merge(
    aqhi_df, 
    mapping_ref, 
    left_on='station', 
    right_on='StationName', 
    how='left'
).drop(columns=['StationName']) # <--- This line removes StationName

# 6. Save output
merged_aqhi.to_csv('aqhi_final_combined.csv', index=False)
print(" Done! File saved without 'StationName'.")