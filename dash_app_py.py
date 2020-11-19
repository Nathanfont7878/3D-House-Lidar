import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import plotly
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

import json

import pyproj
from pyproj import Proj, transform
from dms2dec.dms_convert import dms2dec

import rasterio as rio
from rasterio.plot import show
from rasterio.windows import Window, from_bounds
from IPython.core.display import display

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import seaborn as sns
import pandas as pd

dataset = rio.open("Data/TIFFiles/DHMVIIDSMRAS1m_k13.tif")
transformer = pyproj.Transformer.from_crs('epsg:4326', 'epsg:31370')

app = dash.Dash(__name__, title="Lidar Plot App")

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
        dcc.Slider(id='zoom_slider', value=100, min=10, max=400, marks={i: str(i) for i in range(0, 400, 50)}),
        html.H3("The height of this point is: "),
        html.P(id="height_output", children=["0m"])

    ]),
    html.Div(id="ouputs", children=[
        dcc.Graph(id="plot", style={'horizontal-align': 'center'},
                  config={"modeBarButtons": False, "displaylogo": False})
    ])
])


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
    latitude_4326 = dms2dec(f'''{degrees_lat}°{minutes_lat}'{seconds_lat}"N''')
    longitude_4326 = dms2dec(f'''{degrees_lon}°{minutes_lon}'{seconds_lon}"E''')
    plot_radius = int(zoom_slider)
    print(type(plot_radius))
    latitude_be, longitude_be = transformer.transform(latitude_4326, longitude_4326)
    left = latitude_be - plot_radius
    bottom = longitude_be - plot_radius
    right = latitude_be + plot_radius
    top = longitude_be + plot_radius

    brugge = dataset.read(1, window=from_bounds(left, bottom, right, top, dataset.transform))
    dataset_df = pd.DataFrame(data=brugge)
    dataset_df = dataset_df[::-1]
    # try and remove peaks
    # min_height = dataset_df.values.min()
    # max_height = (dataset_df.values.max() * 1.1) #give some headroom

    fig_3D = go.Figure(data=[go.Surface(z=dataset_df.values, )])
    fig_3D.update_layout(
        height=1000,
        margin=dict(pad=200),
        scene=dict(
            aspectmode="data",
            # aspectratio=dict(x=1, y=1, z=0.2),
            xaxis=dict(
                showbackground=False,
                visible=False
            ),
            yaxis=dict(
                showbackground=False,
                visible=False
            ),
            zaxis=dict(
                # range=[min_height, max_height],
                showbackground=False,
                visible=False
            )
        )
    )

    return fig_3D


@app.callback(Output('height_output', 'children'),
              [Input('plot', 'hoverData')])
def return_height(hoverData):
    height = float(hoverData["points"][0]["z"])
    height = round(height, 1)
    output_string = f"{height}m"
    return output_string


if __name__ == '__main__':
    app.run_server(debug=True)
