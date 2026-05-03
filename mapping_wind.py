import pandas as pd
import geopandas as gpd
import requests


df = pd.read_csv("WSPD_converted.csv")


df.columns = df.columns.str.strip()

print("Columns:", df.columns.tolist())  


lon_col = "GeometryLongitude"  
lat_col = "GeometryLatitude"   


gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
    crs="EPSG:4326"
)


url = "https://www.had.gov.hk/psi/hong-kong-administrative-boundaries/hksar_18_district_boundary.json"
geojson = requests.get(url).json()

districts = gpd.GeoDataFrame.from_features(geojson["features"], crs="EPSG:4326")


result = gpd.sjoin(gdf, districts, how="left", predicate="within")


result.to_csv("windoutput_with_districts.csv", index=False)

print(" Done: windoutput_with_districts.csv")