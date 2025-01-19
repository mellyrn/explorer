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
server = app.server  # Add this line to expose the server object

color_scale = px.colors.sequential.YlOrRd
app.layout = html.Div([
    html.H1("Digital Repression Explorer", className="text-center mb-4"),

    html.Div([
        html.P("This interactive tool visualizes global trends in digital technologies that can potentially impact civil liberties and privacy. It shows how different countries use various digital tools and their relationship with democratic indicators. By exploring this data, we can better understand the complex interplay between technology, governance, and individual freedoms in the digital age.",
               className="lead"
        )
    ], style={'background-color': '#f8f9fa', 'padding': '20px', 'border-radius': '5px', 'margin-bottom': '20px'}),

    dcc.Graph(id='main-graph'),
    html.Div([
        html.Label("Select a country:", className="mr-2"),
        dcc.Dropdown(
            id='country-dropdown',
            options=[{'label': 'All', 'value': 'All'}] +
                    [{'label': c, 'value': c} for c in df_selected['Country of deployment'].unique()],
            value='All',
            style={'width': '50%'}
        )
    ], style={'margin': '20px 0'}),
    dbc.Row([
        dbc.Col(dcc.Graph(id='bar-chart'), width=4),
        dbc.Col(dcc.Graph(id='details-table'), width=8),
    ]),

    html.Footer([
        html.Hr(),
        html.P([
            "Source: Feldstein, Steven; Kot, Brian (2023), ",
            html.Q("Global Inventory of Commercial Spyware & Digital Forensics"),
            ", Mendeley Data, V10, doi: 10.17632/csvhpkt8tm.10"
        ], className="text-muted text-center")
    ], className="mt-4")
])

@app.callback(
    [Output('main-graph', 'figure'),
     Output('bar-chart', 'figure'),
     Output('details-table', 'figure')],
    [Input('country-dropdown', 'value')]
)
def update_graphs(selected_country):
    # Choropleth map
    fig_map = px.choropleth(merged,
        geojson=merged.geometry,
        locations=merged.index,
        color='Digital Repression Index 2021',
        color_continuous_scale=color_scale,
        range_color=(merged['Digital Repression Index 2021'].min(), merged['Digital Repression Index 2021'].max()),
        hover_name='Country of deployment',
        hover_data={
            'Digital Repression Index 2021': ':.2f',
            'V-Dem Electoral Democracy Index 2021': ':.2f',
            'V-Dem Regime Type 2021': True
        },
        labels={
            'Digital Repression Index 2021': 'Digital Repression Index',
            'V-Dem Electoral Democracy Index 2021': 'Electoral Democracy Index',
            'V-Dem Regime Type 2021': 'Regime Type'
        },
        projection='equirectangular'
    )

    fig_map.update_traces(
        hovertemplate="<b>%{hovertext}</b><br><br>" +
        "Digital Repression Index: %{customdata[0]}<br>" +
        "Electoral Democracy Index: %{customdata[1]}<br>" +
        "Regime Type: %{customdata[2]}<extra></extra>"
    )

    fig_map.update_geos(showcoastlines=False,
                        showland=True,
                        landcolor="lightgrey",
                        showcountries=False,
                        showframe=False,
                        projection_type='equirectangular',
                        lataxis_range=[-90, 90],
                        lonaxis_range=[-180, 180])

    fig_map.update_traces(marker_line_width=0)

    fig_map.update_layout(
        height=600,
        margin={"r":0,"t":30,"l":0,"b":0},
        geo=dict(projection_scale=1),
        font=dict(family="Helvetica")
    )

    # Bar chart
    if selected_country == 'All':
        df_filtered = df_selected
    else:
        df_filtered = df_selected[df_selected['Country of deployment'] == selected_country]

    top_tech = df_filtered['Category of technology'].value_counts().head(10)
    fig_bar = go.Figure(go.Bar(
        x=top_tech.values,
        y=top_tech.index,
        orientation='h',
        marker_color='#FFA15A'  
    ))
    fig_bar.update_layout(
        title='Top Technologies',
        height=400,
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis=dict(autorange="reversed"),
        font=dict(family="Helvetica"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    # Table
    fig_table = go.Figure(go.Table(
        header=dict(
            values=columns_of_interest,
            fill_color='#FFA15A',
            align='left',
            font=dict(color='white', size=12, family="Helvetica")
        ),
        cells=dict(
            values=[df_filtered[col] for col in columns_of_interest],
            fill_color='rgba(255, 255, 255, 0.7)',
            align='left',
            font=dict(color='black', size=11, family="Helvetica"),
            height=30  
        )
    ))

    column_widths = [100, 100, 80, 80, 100, 100, 300] 
    fig_table.update_layout(
        title='Details',
        height=None,
        margin=dict(l=0, r=0, t=30, b=0),
        font=dict(family="Helvetica"),
        autosize=True,
        width=None,
    )
    fig_table.update_traces(
        cells=dict(
            align=['left'] * len(columns_of_interest),
            font=dict(color='black', size=11, family="Helvetica"),
            height=30
        ),
        columnwidth=column_widths
    )

    return fig_map, fig_bar, fig_table

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run_server(debug=False, host='0.0.0.0', port=port)
