import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import fsspec
import os

# Load data
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
df = pd.read_csv("spy3.csv")

regime_type_mapping = {
    'LD': 'Liberal Democracy',
    'ED': 'Electoral Democracy',
    'EA': 'Electoral Autocracy',
    'CA': 'Closed Autocracy'
}

df['V-Dem Regime Type 2021'] = df['V-Dem Regime Type 2021'].map(regime_type_mapping)
world = world.rename(columns={'name': 'Country of deployment'})
merged = world.merge(df[['Country of deployment', 'Digital Repression Index 2021', 'V-Dem Electoral Democracy Index 2021', 'V-Dem Regime Type 2021']],
                     on='Country of deployment',
                     how='left')

cmap = plt.cm.Reds
norm = mcolors.Normalize(vmin=merged['Digital Repression Index 2021'].min(),
                         vmax=merged['Digital Repression Index 2021'].max())

columns_of_interest = ['Country of deployment', 'Category of technology', 'Period of use',
                       'Year of disclosure', 'Commercial Entity', 'Country of origin',
                       'Description']
df_selected = df[columns_of_interest]

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # This line is important for Gunicorn to find the server

color_scale = px.colors.sequential.YlOrRd
app.layout = html.Div([
    # ... (rest of your layout code remains the same)
])

@app.callback(
    [Output('main-graph', 'figure'),
     Output('bar-chart', 'figure'),
     Output('details-table', 'figure')],
    [Input('country-dropdown', 'value')]
)
def update_graphs(selected_country):
    # ... (rest of your callback function remains the same)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run_server(debug=False, host='0.0.0.0', port=port)
