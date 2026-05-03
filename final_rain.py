import pandas as pd
import geopandas as gpd
import requests

# 1. SETUP GEOGRAPHIC MAPPING
print("Step 1: Mapping rainfall stations to districts...")
df_meta = pd.read_csv("RF_converted.csv")
df_meta.columns = df_meta.columns.str.strip()

# Convert metadata to GeoDataFrame for spatial join
gdf_stations = gpd.GeoDataFrame(
    df_meta,
    geometry=gpd.points_from_xy(df_meta["GeometryLongitude"], df_meta["GeometryLatitude"]),
    crs="EPSG:4326"
)

# Fetch HKSAR district boundaries
dist_url = "https://www.had.gov.hk/psi/hong-kong-administrative-boundaries/hksar_18_district_boundary.json"
geojson = requests.get(dist_url).json()
districts = gpd.GeoDataFrame.from_features(geojson["features"], crs="EPSG:4326")

# Link stations to districts
mapping_ref = gpd.sjoin(gdf_stations, districts, how="left", predicate="within")

# 2. PROCESS DAILY DATA
print("Step 2: Downloading and cleaning daily records...")
start_date = '2023-01-01'
end_date = '2026-04-30'
all_output = []

for index, row in mapping_ref.iterrows():
    station_name = row['WeatherStationName_en']
    rf_url = row['DailyTotalRainfall_AllYear_url'] 
    
    if pd.isna(rf_url):
        continue
        
    try:
        # Read raw HKO file
        df_rf = pd.read_csv(rf_url, skiprows=3)
        
        # Position-based extraction: 0=Year, 1=Month, 2=Day, 7=Rainfall Value
        subset = df_rf.iloc[:, [0, 1, 2, 7]].copy()
        subset.columns = ['y', 'm', 'd', 'raw_rf']

        # --- PREPROCESSING RULES ---
        # Clean strings and strip whitespace
        subset['raw_rf'] = subset['raw_rf'].astype(str).str.strip()
        
        # Initialize columns
        subset['rain_trace_flag'] = 0
        subset['rain_mm_imputed'] = 0.0
        
        # Rule: Handle Trace (set to 0.025 and flag 1)
        trace_mask = subset['raw_rf'].isin(['Trace', 'Tr', 'Trace '])
        subset.loc[trace_mask, 'rain_mm_imputed'] = 0.025
        subset.loc[trace_mask, 'rain_trace_flag'] = 1
        
        # Rule: Handle Numeric values (measurable >= 0.05 or 0)
        numeric_rf = pd.to_numeric(subset['raw_rf'], errors='coerce')
        measurable_mask = ~trace_mask & numeric_rf.notna()
        subset.loc[measurable_mask, 'rain_mm_imputed'] = numeric_rf[measurable_mask]
        
        # Rule: rain_occurrence_flag (1 if Trace or > 0)
        subset['rain_occurrence_flag'] = (
            (subset['rain_trace_flag'] == 1) | (subset['rain_mm_imputed'] > 0)
        ).astype(int)
        # ---------------------------

        # Numeric cleaning for date components
        for col in ['y', 'm', 'd']:
            subset[col] = pd.to_numeric(subset[col], errors='coerce')
        
        # Drop rows with invalid date numbers
        subset = subset.dropna(subset=['y', 'm', 'd'])
        
        # Create date string for conversion
        subset['date_str'] = (
            subset['y'].astype(int).astype(str) + '-' +
            subset['m'].astype(int).astype(str).str.zfill(2) + '-' +
            subset['d'].astype(int).astype(str).str.zfill(2)
        )
        
        # --- ROBUST DATE CONVERSION ---
        # errors='coerce' handles invalid calendar dates like Feb 30th
        subset['date_dt'] = pd.to_datetime(subset['date_str'], errors='coerce')
        subset = subset.dropna(subset=['date_dt']) # Drop NaT (invalid dates)
        
        # Final formatting and feature extraction
        subset['date'] = subset['date_dt'].dt.strftime('%Y-%m-%d')
        subset['year'] = subset['date_dt'].dt.year
        subset['month'] = subset['date_dt'].dt.month
        subset['day'] = subset['date_dt'].dt.day
        subset['day_of_week'] = subset['date_dt'].dt.day_name()
        subset['is_weekend'] = (subset['date_dt'].dt.dayofweek >= 5).astype(int) 
        # ------------------------------

        # Filter for your specific timeframe
        mask = (subset['date'] >= start_date) & (subset['date'] <= end_date)
        final_subset = subset.loc[mask].copy()
        
        if not final_subset.empty:
            # Attach district context
            final_subset['WeatherStationName_en'] = station_name
            final_subset['index_right'] = row.get('index_right', 'N/A')
            final_subset['地區號碼'] = row.get('地區號碼', 'N/A')
            final_subset['District'] = row.get('District', 'N/A')
            
            # Select final organized columns
            output_cols = [
                'date', 'year', 'month', 'day', 'day_of_week', 'is_weekend',
                'WeatherStationName_en', 'rain_mm_imputed', 'rain_trace_flag', 
                'rain_occurrence_flag', 'index_right', '地區號碼', 'District'
            ]
            all_output.append(final_subset[output_cols])
            print(f" Processed: {station_name}")
            
    except Exception as e:
        print(f" Error at {station_name}: {e}")

# 3. SAVE FINAL OUTPUT
if all_output:
    final_df = pd.concat(all_output, ignore_index=True)
    final_df.to_csv('rainfall_complete_mapped.csv', index=False)
    print("\n Success! File saved as 'rainfall_complete_mapped.csv'")
else:
    print("\n No data was processed. Check your URL columns or date range.")