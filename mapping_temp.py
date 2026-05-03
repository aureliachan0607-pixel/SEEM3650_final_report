import pandas as pd
import geopandas as gpd
import requests


df = pd.read_csv("ALLTEMP_converted - ALLTEMP_converted.csv")


df.columns = df.columns.str.strip()

print("Columns:", df.columns.tolist())  # check names

#  Use correct column names (adjust if needed) ===
lon_col = "GeometryLongitude"   # <-- change if different
lat_col = "GeometryLatitude"    # <-- change if different


gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
    crs="EPSG:4326"
)


url = "https://www.had.gov.hk/psi/hong-kong-administrative-boundaries/hksar_18_district_boundary.json"
geojson = requests.get(url).json()

districts = gpd.GeoDataFrame.from_features(geojson["features"], crs="EPSG:4326")


result = gpd.sjoin(gdf, districts, how="left", predicate="within")


result.to_csv("tempoutput_with_districts.csv", index=False)

print(" Done: tempoutput_with_districts.csv")