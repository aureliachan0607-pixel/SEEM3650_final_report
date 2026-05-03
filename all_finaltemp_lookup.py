import pandas as pd


mapping_ref = pd.read_csv('tempoutput_with_districts.csv')

# 2. Load your metadata source containing the URLs
metadata = pd.read_csv('ALLTEMP_converted - ALLTEMP_converted.csv')

start_date = '2023-01-01'
end_date = '2026-04-30'

all_output = []

# Updated helper function with robust cleaning and time features
def get_clean_temp(url, col_name):
    df_temp = pd.read_csv(url, skiprows=3)
    
    # Select Year, Month, Day, and Temperature Value
    subset = df_temp.iloc[:, [0, 1, 2, 7]].copy()
    subset.columns = ['y', 'm', 'd', col_name]
    
    # Robust numeric conversion - handles empty rows at bottom of HKO files
    for col in ['y', 'm', 'd', col_name]:
        subset[col] = pd.to_numeric(subset[col], errors='coerce')
    
    # Drop rows with missing dates or temperature values
    subset = subset.dropna(subset=['y', 'm', 'd', col_name])
    
    # Create standardized date key
    subset['date'] = (
        subset['y'].astype(int).astype(str) + '-' +
        subset['m'].astype(int).astype(str).str.zfill(2) + '-' +
        subset['d'].astype(int).astype(str).str.zfill(2)
    )
    
    # Extract Time Features
    temp_dt = pd.to_datetime(subset['date'])
    subset['year'] = temp_dt.dt.year
    subset['month'] = temp_dt.dt.month
    subset['day'] = temp_dt.dt.day
    subset['day_of_week'] = temp_dt.dt.day_name()
    subset['is_weekend'] = (temp_dt.dt.dayofweek >= 5).astype(int) 
    
    return subset[['date', 'year', 'month', 'day', 'day_of_week', 'is_weekend', col_name]]

for index, row in metadata.iterrows():
    station_name = row['WeatherStationName_en']
    
    mean_url = row['DailyMeanTemperature_AllYear_url']
    max_url = row['DailyMaximumTemperature_AllYear_url']
    min_url = row['DailyMinimumTemperature_AllYear_url']
    
    if pd.isna(mean_url) or pd.isna(max_url) or pd.isna(min_url):
        continue
        
    try:
        # Fetch all three datasets with new cleaning logic
        df_mean = get_clean_temp(mean_url, 'daily_mean_temp')
        df_max = get_clean_temp(max_url, 'daily_max_temp')
        df_min = get_clean_temp(min_url, 'daily_min_temp')

        # Merge them together (include time features in the merge base)
        #  merge on all time columns to keep them consistent
        time_cols = ['date', 'year', 'month', 'day', 'day_of_week', 'is_weekend']
        merged_temp = pd.merge(df_mean, df_max, on=time_cols, how='inner')
        merged_temp = pd.merge(merged_temp, df_min, on=time_cols, how='inner')
        
        # Filter by your specified dates
        mask = (merged_temp['date'] >= start_date) & (merged_temp['date'] <= end_date)
        final_subset = merged_temp.loc[mask].copy()
        
        if not final_subset.empty:
            final_subset['WeatherStationName_en'] = station_name
            
            # Join with district mapping to add HAD IDs
            final_mapped = pd.merge(
                final_subset, 
                mapping_ref[['WeatherStationName_en', 'index_right', '地區號碼', 'District']], 
                on='WeatherStationName_en', 
                how='left'
            )
            
            # Organize columns
            output_cols = [
                'date', 'year', 'month', 'day', 'day_of_week', 'is_weekend',
                'WeatherStationName_en', 'daily_mean_temp', 'daily_max_temp', 
                'daily_min_temp', 'index_right', '地區號碼', 'District'
            ]
            all_output.append(final_mapped[output_cols])
            print(f" Fully Mapped: {station_name}")
            
    except Exception as e:
        print(f" Error at {station_name}: {e}")

# Save the final consolidated file
if all_output:
    pd.concat(all_output, ignore_index=True).to_csv('temperature_complete_mapped.csv', index=False)
    print("\nSaved to 'temperature_complete_mapped.csv' with time features and 0/1 weekend flags.")