import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from geopy.distance import geodesic
import dash
from dash import dash_table
from dash import dcc, html
from dash.dependencies import Input, Output
import re
import folium
import time
from urllib.parse import quote_plus
import plotly.express as px
from folium.plugins import MarkerCluster

file_path = "C:\\Users\\User\\Desktop\\Practice Coding\\PythonProjects\\FedEx Office Project\\NewGitProject\\NewMergedYellowPagesData.csv"
dtypes = {'column_19': str, 'column_20': str}
df = pd.read_csv(file_path, dtype=dtypes, low_memory=False)


# Remove the pattern from the 'Name' column
df['Name'] = df['Name'].astype(str)
# Create a new column 'Name_Address' that concatenates 'Name' and 'Address'
df['Name_Address'] = df['Name'] + df['Address']

# Keep only the first occurrence of each 'Name_Address'
df = df.drop_duplicates(subset='Name_Address', keep='first')

# Optionally, you can drop the 'Name_Address' column if it's no longer needed
df = df.drop(columns='Name_Address')

df['Name'] = df['Name'].apply(lambda x: re.sub('[^a-zA-Z ]+', '', x))

# Fill missing values in 'Category' column
df['Category'] = df['Category'].fillna('Unknown')
df['ZipCode'] = df['Address'].str.extract(r'(\d{5})$')


# Define business type based on category
def get_business_type(row):
    shipping_keywords = ['Mail & Shipping Services', 'Air Cargo & Package Express Packing', 'Mailbox Rental']
    printing_keywords = ['Fax Services', 'Copying & Duplicating Service']

    is_shipping = any(keyword in row['Category'] for keyword in shipping_keywords)
    is_printing = any(keyword in row['Category'] for keyword in printing_keywords)

    if is_shipping and is_printing:
        return 'Dual Competition'
    elif is_shipping:
        return 'Shipping Competition'
    elif is_printing:
        return 'Printing Competition'
    else:
        return 'Potential Business'

df['Business Type'] = df.apply(get_business_type, axis=1)

app = dash.Dash(__name__)

# Define the layout of the dashboard
app.layout = html.Div([
    html.Label("Enter Distance:"),
    dcc.Input(id='distance-input', type='text', value='10.0'),
    html.Div(id='output-results')
])

# Define callback to update results based on distance input
@app.callback(
    Output('output-results', 'children'),
    [Input('distance-input', 'value')])
# Define business type based on category
def update_results(selected_distance_input):
    try:
        selected_distance = float(selected_distance_input)
        filtered_df = df[df['Distance'] <= selected_distance]
        filtered_df.loc[:, 'Distance'] = filtered_df['Distance'].apply(lambda x: f'{x:.4f}')
        result_table = filtered_df[['Name', 'Distance', 'Website', 'Address',
                                    'Phone', 'Rating', 'Reviews','Category']].copy()  # Create a copy of the DataFrame

        # Sort the results by 'Distance' in ascending order
        result_table = result_table.sort_values('Distance')

        # Count the total number of businesses
        total_businesses = len(result_table)

        # Count the number of businesses by category
        category_counts = result_table['Category'].value_counts().reset_index()
        category_counts.columns = ['Category', 'Count']

        # Create a map with the filtered data
        m = folium.Map(location=[40.6209374, -74.0256168], zoom_start=15, tiles='cartodb positron')

        # Add a red marker for the reference point
        folium.CircleMarker(
            location=[40.6209374, -74.0256168],
            radius=5,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.6,
        ).add_to(m)

        # Create a MarkerCluster object
        marker_cluster = MarkerCluster().add_to(m)

        # Add a marker for each potential business
        for idx, row in filtered_df[filtered_df['Business Type'] == 'Potential Business'].iterrows():
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=f"Name: {row['Name']}<br>Competition Type: {row['Business Type']}"
            ).add_to(marker_cluster)

        # Convert the map to HTML
        m = m._repr_html_()

        # Filter the DataFrame to include only the competitors
        competitors_df = filtered_df[filtered_df['Business Type'].isin(['Shipping Competition', 'Printing Competition', 'Dual Competition'])]
        # Get the index of the row with the specific address
        index_to_drop = competitors_df[competitors_df['Phone'] == '(718) 745-1006'].index

        # Drop the row from the DataFrame
        competitors_df = competitors_df.drop(index_to_drop)


        # Create a second map with only the competitors
        m2 = folium.Map(location=[40.6209374, -74.0256168], zoom_start=15, tiles='cartodb positron')

        # Add a red marker for the reference point
        folium.CircleMarker(
            location=[40.6209374, -74.0256168],
            radius=5,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.6,
        ).add_to(m2)

        # Add a marker for each competitor
        for idx, row in competitors_df.iterrows():

                folium.Marker(
                    location=[row['Latitude'], row['Longitude']],
                    popup=f"Name: {row['Name']}<br>Competition Type: {row['Business Type']}"
                ).add_to(m2)

        # Convert the second map to HTML
        m2 = m2._repr_html_()



        return [html.H3(f"Total number of businesses within the selected distance: {total_businesses}"),
                html.H3("Number of businesses by category:"),
                dash_table.DataTable(
                    data=category_counts.to_dict('records'),
                    columns=[{'name': i, 'id': i} for i in category_counts.columns],
                    style_cell_conditional=[
                        {'if': {'column_id': 'Category'},
                         'width': '100px'}  # Set the width of the 'Category' column
                    ],
                    tooltip_data=[
                        {
                            column: {'value': str(value), 'type': 'markdown'}
                            for column, value in row.items()
                        } for row in category_counts.to_dict('records')
                    ],
                    tooltip_duration=None,
                    page_size=20  # Only show 20 rows at a time
                ),
                html.Div(style={"height": "50px"}),  # Add some space
                html.H3("Details of businesses:"),
                dash_table.DataTable(
                    data=result_table.to_dict('records'),
                    columns=[{'name': i, 'id': i} for i in result_table.columns],
                    style_cell_conditional=[
                        {'if': {'column_id': 'Name'},
                         'width': '100px'}  # Set the width of the 'Name' column
                    ],
                    style_data_conditional=[
                        {
                            'if': {'column_id': 'Website'},
                            'textDecoration': 'underline',
                            'color': 'blue',
                            'cursor': 'pointer'
                        }
                    ],
                    tooltip_data=[
                        {
                            column: {'value': str(value), 'type': 'markdown'}
                            for column, value in row.items()
                        } for row in result_table.to_dict('records')
                    ],
                    tooltip_duration=None,
                    page_size=20  # Only show 20 rows at a time
                ),
                html.Div(style={"height": "50px"}),  # Add some space
                html.Iframe(srcDoc=m, style={"width": "100%", "height": "600px"}),
                html.Div(style={"height": "50px"}),  # Add some space
                html.H3("Details of competitors:"),
                dash_table.DataTable(
                    data=competitors_df[['Name', 'Address', 'Phone', 'Website', 'Category', 'Business Type']].to_dict('records'),
                    columns=[{'name': i, 'id': i} for i in ['Name', 'Address', 'Phone', 'Website', 'Category', 'Business Type']],
                    style_cell_conditional=[
                        {'if': {'column_id': 'Name'},
                         'width': '100px'}  # Set the width of the 'Name' column
                    ],
                    style_data_conditional=[
                        {
                            'if': {'column_id': 'Website'},
                            'textDecoration': 'underline',
                            'color': 'blue',
                            'cursor': 'pointer'
                        }
                    ],
                    tooltip_data=[
                        {
                            column: {'value': str(value), 'type': 'markdown'}
                            for column, value in row.items()
                        } for row in competitors_df[['Name', 'Address', 'Phone', 'Website', 'Category', 'Business Type']].to_dict('records')
                    ],
                    tooltip_duration=None,
                    page_size=20  # Only show 20 rows at a time
                ),
                html.Div(style={"height": "50px"}),  # Add some space
                html.Iframe(srcDoc=m2, style={"width": "100%", "height": "600px"})]  # This is the line you should replace
    except ValueError:
        return html.Div("Please enter a valid numeric distance.")

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
