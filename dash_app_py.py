import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import plotly
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

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

app = dash.Dash(__name__)

app.layout = html.Div(className="body", children=[
    html.Br(),
    html.H1(className="no_margin", children="3D House Lidar"),
    html.Div(id="inputs", children=[
        html.P("lat:"),
        html.Div(className="coordinate_input", children=[
            dcc.Input(value="51", id="degrees_lat", size="5", placeholder="degrees"),
            dcc.Input(value="12", id="minutes_lat", size="5", placeholder="minutes"),
            dcc.Input(value="34.412", id="seconds_lat", size="5", placeholder="seconds")
        ]),
        html.P("lon:"),
        html.Div(className="coordinate_input", children=[
            dcc.Input(value="3", id="degrees_lon", size="5", placeholder="degrees"),
            dcc.Input(value="13", id="minutes_lon", size="5", placeholder="minutes"),
            dcc.Input(value="33.949", id="seconds_lon", size="5", placeholder="seconds")
        ]),
        dcc.Slider()
    ]),
    html.Div(id="ouputs", children=[
        dcc.Graph(id="3Dplot", style={'horizontal-align': 'center'})
    ])
])


@app.callback(
    Output('3Dplot', 'figure'),
    [Input('degrees_lat', 'value'),
     Input('minutes_lat', 'value'),
     Input('seconds_lat', 'value'),
     Input('degrees_lon', 'value'),
     Input('minutes_lon', 'value'),
     Input('seconds_lon', 'value')])
def update_graph(degrees_lat, minutes_lat, seconds_lat, degrees_lon, minutes_lon, seconds_lon):
    latitude_4326 = dms2dec(f'''{degrees_lat}°{minutes_lat}'{seconds_lat}"N''')
    longitude_4326 = dms2dec(f'''{degrees_lon}°{minutes_lon}'{seconds_lon}"E''')

    latitude_be, longitude_be = transformer.transform(latitude_4326, longitude_4326)
    left = latitude_be - 20.0
    bottom = longitude_be - 20.0
    right = latitude_be + 20.0
    top = longitude_be + 20.0

    brugge = dataset.read(1, window=from_bounds(left, bottom, right, top, dataset.transform))
    dataset_df = pd.DataFrame(data=brugge)
    fig_3D = go.Figure(data=[go.Surface(z=dataset_df.values)])
    fig_3D.update_layout(
        height=1000,
        margin=dict(pad=200),
        scene=dict(
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
            )
        )
    )

    return fig_3D


if __name__ == '__main__':
    app.run_server(debug=False)
