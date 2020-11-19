# Import Dash dependencies to build app
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

# Import Plotly and it's graph_objects to plot
import plotly
import plotly.graph_objects as go

# Import pyproj and dms2dec to handle coordinate systems and conversions
import pyproj
from dms2dec.dms_convert import dms2dec

# Import Rasterio and it's from_bounds function to deal with tiff file
import rasterio as rio
from rasterio.windows import Window, from_bounds

# Import Numpy and Pandas to deal with dataframes and data
import numpy as np
import pandas as pd

# Open dataset with rasterio, initiate transformer to transform coordinate systems
dataset = rio.open("Data/TIFFiles/DHMVIIDSMRAS1m_k13.tif")
transformer = pyproj.Transformer.from_crs('epsg:4326', 'epsg:31370')
# Create app variable
app = dash.Dash(__name__, title="Lidar Plot App")
# Create server variable to deploy
server = app.server
# Create lay-out of the app
app.layout = html.Div(className="body", children=[
    html.Br(),
    html.H1("Lidar Plot App"),
    html.Div(id="inputs", children=[
        html.H3("Latitude: Degrees-Minutes-Seconds"),
        html.Div(className="coordinate_input", children=[
            dcc.Input(id="degrees_lat", value="51", size="5", placeholder="degrees"),
            dcc.Input(id="minutes_lat", value="12", size="5", placeholder="minutes"),
            dcc.Input(id="seconds_lat", value="31", size="5", placeholder="seconds")
        ]),
        html.H3("Longitude: Degrees-Minutes-Seconds"),
        html.Div(className="coordinate_input", children=[
            dcc.Input(id="degrees_lon", value="3", size="5", placeholder="degrees"),
            dcc.Input(id="minutes_lon", value="13", size="5", placeholder="minutes"),
            dcc.Input(id="seconds_lon", value="28", size="5", placeholder="seconds")
        ]),
        html.Br(), html.Br(),
        html.Button('Plot', id='button'),
        html.Br(), html.Br(), html.Br(),
        dcc.Slider(id='zoom_slider', value=300, min=10, max=400, marks={i: str(i) for i in range(0, 400, 50)}),
        html.H3("The estimated height of this point is: "),
        html.P(id="height_output", children=["0.00m"])

    ]),
    html.Div(id="ouputs", children=[
        dcc.Graph(id="plot", style={'horizontal-align': 'center'},
                  config={"modeBarButtons": False, "displaylogo": False})
    ])
])


# Function that uses the inputs as variables and outputs the graph in to the graph element in the lay-out
@app.callback(
    Output('plot', 'figure'),
    [Input('button', 'n_clicks'),
     Input('zoom_slider', 'value')
     ],
    state=[State('degrees_lat', 'value'),
           State('minutes_lat', 'value'),
           State('seconds_lat', 'value'),
           State('degrees_lon', 'value'),
           State('minutes_lon', 'value'),
           State('seconds_lon', 'value'),
           ])
def update_graph(button, zoom_slider, degrees_lat, minutes_lat, seconds_lat, degrees_lon, minutes_lon, seconds_lon):
    # Convert dms to dd
    latitude_4326 = dms2dec(f'''{degrees_lat}°{minutes_lat}'{seconds_lat}"N''')
    longitude_4326 = dms2dec(f'''{degrees_lon}°{minutes_lon}'{seconds_lon}"E''')
    # Read value of slider
    plot_radius = int(zoom_slider)
    # Transform epsg4326 (International) coordinates to 31370 Lambert system (Belgium)
    latitude_be, longitude_be = transformer.transform(latitude_4326, longitude_4326)
    # Set bounds of window
    left = latitude_be - plot_radius
    bottom = longitude_be - plot_radius
    right = latitude_be + plot_radius
    top = longitude_be + plot_radius

    # Make window and convert it to a dataframe
    brugge = dataset.read(1, window=from_bounds(left, bottom, right, top, dataset.transform))
    dataset_df = pd.DataFrame(data=brugge)
    # Reverse dataframe to have the right to avoid mirrored plots
    dataset_df = dataset_df[::-1]

    # Generate Figure object - Surface plot with Plotly
    fig_3D = go.Figure(data=[go.Surface(z=dataset_df.values)])
    fig_3D.update_layout(
        height=800,
        hovermode=False,
        scene=dict(
            aspectmode="data",
            xaxis=dict(
                showbackground=False,
                visible=False
            ),
            yaxis=dict(
                showbackground=False,
                visible=False
            ),
            zaxis=dict(
                showbackground=False,
                visible=False
            )
        )
    )

    return fig_3D


# Function that updates the total area of the window based on the slider
@app.callback(Output('height_output', 'children'),
              [Input('plot', 'hoverData')])
def return_height(hover_data):
    # Select 'z' data
    height = float(hover_data["points"][0]["z"])
    # Subtract 8m (estimate height of Bruges above sealevel)
    height = round(height - 8.0, 1)
    # Generate string to print in height_output element in the lay-out
    output_string = f"{height}m"
    return output_string


# Run app with Flask
if __name__ == '__main__':
    app.run_server(debug=False)
