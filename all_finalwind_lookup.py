import pandas as pd


mapping_ref = pd.read_csv('windoutput_with_districts.csv')


metadata = pd.read_csv('WSPD_converted.csv')

start_date = '2023-01-01'
end_date = '2026-04-30'

all_output = []

for index, row in metadata.iterrows():
    station_name = row['WeatherStationName_en']
    mean_wspd_url = row['DailyMeanWindSpeed_AllYear_url']
    
    if pd.isna(mean_wspd_url):
        continue
        
    try:
        # Fetch data
        df_wind = pd.read_csv(mean_wspd_url, skiprows=3)
        
        # Robust Cleaning: Select columns and strip whitespace to avoid "Invalid value" errors
        subset = df_wind.iloc[:, [0, 1, 2, 7]].copy()
        subset.columns = ['y', 'm', 'd', 'daily_mean_wspd']
        
        # Convert columns to numeric, forcing errors (like 'Trace' or empty strings) to NaN
        for col in ['y', 'm', 'd', 'daily_mean_wspd']:
            subset[col] = pd.to_numeric(subset[col], errors='coerce')
        
        # Drop rows with missing dates or wind speed (cleans up the bottom of the CSV)
        subset = subset.dropna(subset=['y', 'm', 'd', 'daily_mean_wspd'])
        
        # Create standardized date key
        subset['date'] = (
            subset['y'].astype(int).astype(str) + '-' +
            subset['m'].astype(int).astype(str).str.zfill(2) + '-' +
            subset['d'].astype(int).astype(str).str.zfill(2)
        )
        
        
        temp_dt = pd.to_datetime(subset['date'])
        subset['year'] = temp_dt.dt.year
        subset['month'] = temp_dt.dt.month
        subset['day'] = temp_dt.dt.day
        subset['day_of_week'] = temp_dt.dt.day_name()
        subset['is_weekend'] = (temp_dt.dt.dayofweek >= 5).astype(int) 
        
        
        
        mask = (subset['date'] >= start_date) & (subset['date'] <= end_date)
        final_subset = subset.loc[mask].copy()
        
        if not final_subset.empty:
            final_subset['WeatherStationName_en'] = station_name
            
            # Join with district mapping to add HAD IDs
            final_mapped = pd.merge(
                final_subset, 
                mapping_ref[['WeatherStationName_en', 'index_right', '地區號碼', 'District']], 
                on='WeatherStationName_en', 
                how='left'
            )
            
            # Select final columns including new features
            output_cols = [
                'date', 'year', 'month', 'day', 'day_of_week', 'is_weekend',
                'WeatherStationName_en', 'daily_mean_wspd', 
                'index_right', '地區號碼', 'District'
            ]
            all_output.append(final_mapped[output_cols])
            print(f" Mapped Mean Wind: {station_name}")
            
    except Exception as e:
        print(f" Error at {station_name}: {e}")

# Save the final consolidated file
if all_output:
    pd.concat(all_output, ignore_index=True).to_csv('wind_mean_mapped.csv', index=False)
    print("\nSaved to 'wind_mean_mapped.csv' with time features and 0/1 weekend flags.")