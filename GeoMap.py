import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import folium
import branca

# API endpoint that returns GeoJSON data
url = "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/NYC_Census_Tracts_for_2020_US_Census/FeatureServer/0/query?where=1=1&outFields=*&outSR=4326&f=pgeojson"

# Send a GET request to the API and load the GeoJSON data into a GeoDataFrame
tracts = gpd.read_file(url)

# Load your CSV file into a DataFrame
df = pd.read_csv("C:\\Users\\User\\Desktop\\Practice Coding\\PythonProjects\\FedEx Office Project\\CensusYellowPages\\NewMergedYellowPagesData.csv",low_memory=False)

# Create a new DataFrame to hold the latitude and longitude as Points
geometry = [Point(xy) for xy in zip(df['Longitude'], df['Latitude'])]
geo_df = gpd.GeoDataFrame(df, geometry=geometry)
geo_df = geo_df.set_crs("EPSG:4326")

# Perform a spatial join between the two GeoDataFrames
joined = gpd.sjoin(geo_df, tracts, predicate='within')

# Calculate the number of businesses per Census Tract
density = joined['GEOID'].value_counts().reset_index()
density.columns = ['Census Tract', 'Number of Businesses']
density['Number of Businesses'] = density['Number of Businesses'].fillna(0)

# Create a map centered around New York City
nyc_map = folium.Map(location=[40.7128, -74.0060], zoom_start=13, tiles='cartodb positron')

# Add the choropleth map to the map
folium.Choropleth(
    geo_data=url,
    name='choropleth',
    data=density,
    columns=['Census Tract', 'Number of Businesses'],
    key_on='feature.properties.GEOID',
    fill_color='Set3',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Number of Businesses',
    bins=12,
    nan_fill_color='green'
).add_to(nyc_map)

folium.CircleMarker(
    [40.6209374, -74.0256168],  # Your coordinates
    radius=5,  # Defines the radius of the circle marker in pixels. You can adjust this value as needed.
    color='red',
    fill=True,
    fill_color='red'
).add_to(nyc_map)


# Create a string of HTML code for the legend
legend_html = '''
<div style="position: fixed; bottom: 50px; left: 50px; width: 150px; height: 90px; 
            border:2px solid grey; z-index:9999; font-size:14px; background-color:white;
            ">
    <p><strong>Legend:</strong></p>
    <p style="margin-left:10px;"><i class="fa fa-circle fa-1x" style="color:green"></i> Green Area or Forest</p>
</div>
'''

# Create a branca element with the HTML code
legend = branca.element.Element(legend_html)

# Add the legend to the map
nyc_map.get_root().html.add_child(legend)

# Save the map to an HTML file
nyc_map.save("nyc_businesses_choropleth.html")
