import pandas as pd
import geopandas as gpd
import folium
import branca

# Load your data
df = pd.read_csv('https://media.githubusercontent.com/media/dcruzrui/dashboard/main/NewMergedYellowPagesData.csv',low_memory=False)

# Extract the last 5 characters from the 'Address' column to create a new 'ZIP' column
df['ZIP'] = df['Address'].str[-5:]

# Count the number of businesses by ZIP code
business_counts = df['ZIP'].value_counts().reset_index()
business_counts.columns = ['ZIP', 'Count']
business_counts['ZIP'] = business_counts['ZIP'].astype(str)



# Load NYC geospatial data
nyc = gpd.read_file("C:\\Users\\User\\Downloads\\Modified Zip Code Tabulation Areas (MODZCTA).geojson")

# Merge the geospatial data with the business counts
merged = nyc.set_index('modzcta').join(business_counts.set_index('ZIP'))
merged.index = merged.index.astype(str)


# Create a map centered on NYC
m = folium.Map(location=[40.7128, -74.0060], zoom_start=10, tiles='cartodb positron')

# Create a choropleth layer
choropleth = folium.Choropleth(
    geo_data=merged.__geo_interface__,
    data=business_counts,
    columns=['ZIP', 'Count'],
    key_on='feature.id',
    fill_color='Set3',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Number of Businesses by ZIP Code',
    bins=12,
    nan_fill_color='green'
).add_to(m)

folium.CircleMarker(
    [40.6209374, -74.0256168],  # Your coordinates
    radius=5,  # Defines the radius of the circle marker in pixels. You can adjust this value as needed.
    color='red',
    fill=True,
    fill_color='red'
).add_to(m)

# Add a layer control and display the map
folium.LayerControl().add_to(m)


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
m.get_root().html.add_child(legend)

# Save the map to an HTML file
m.save("mapzipcode.html")