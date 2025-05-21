import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import re
from dash import dash_table
import os

# Chargement et préparation des données
DATA_PATH = os.path.join(os.path.dirname(__file__), 'Data_Train.xlsx')
data = pd.read_excel("Data_Train.xlsx")

# Transformations (comme dans votre analyse originale)
data['Date_of_Journey'] = pd.to_datetime(data['Date_of_Journey'], dayfirst=True)
data['Journey_day'] = data['Date_of_Journey'].dt.day
data['Journey_month'] = data['Date_of_Journey'].dt.month
data['Dep_hour'] = pd.to_datetime(data['Dep_Time'], format='%H:%M').dt.hour
data['Arrival_hour'] = pd.to_datetime(data['Arrival_Time'], format='%H:%M', errors='coerce').dt.hour


def duration_to_minutes(duration):
    hours = re.search(r'(\d+)h', duration)
    minutes = re.search(r'(\d+)m', duration)
    return (int(hours.group(1)) if hours else 0) * 60 + (int(minutes.group(1)) if minutes else 0)

data['Duration_min'] = data['Duration'].apply(duration_to_minutes)

def part_of_day(hour):
    if 4 <= hour < 12: return "matin"
    elif 12 <= hour < 16: return "après-midi"
    elif 16 <= hour < 20: return "soir"
    else: return "nuit"
    
data["part_of_day"] = data["Dep_hour"].apply(part_of_day)


# Initialisation de l'app Dash
app = dash.Dash(__name__)

# Layout du dashboard amélioré
app.layout = html.Div([
    html.H1("Tableau de Bord des Données de Vols", style={'textAlign': 'center', 'color': "#0c4177"}),
    
    # Section KPI
    html.Div([
        html.Div([
            html.Div(id='kpi-nb-vols', className='kpi-box'),
            html.Div(id='kpi-prix-moyen', className='kpi-box'),
            html.Div(id='kpi-duree-moyenne', className='kpi-box'),
            html.Div(id='kpi-remplissage', className='kpi-box'),
        ], className='kpi-container'),
    ]),
    
    # Filtres
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='airline-selector',
                options=[{'label': airline, 'value': airline} 
                         for airline in sorted(data['Airline'].unique())],
                value=['IndiGo', 'Air India', 'Jet Airways'],
                multi=True,
                placeholder="Sélectionnez des compagnies"
            )
        ], style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.RangeSlider(
                id='price-range',
                min=data['Price'].min(),
                max=data['Price'].max(),
                step=1000,
                value=[data['Price'].min(), data['Price'].max()],
                marks={i: f'{i//1000}k₹' for i in range(0, 80000, 10000)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ], className='filter-container'),
    
    # Première ligne de graphiques
    html.Div([
        dcc.Graph(id='price-distribution', className='graph-box'),
        dcc.Graph(id='duration-distribution', className='graph-box')
    ], className='graph-row'),
    
    # Deuxième ligne de graphiques
    html.Div([
        dcc.Graph(id='price-by-airline', className='graph-box'),
        dcc.Graph(id='price-by-stops', className='graph-box')
    ], className='graph-row'),
    
    # Troisième ligne de graphiques
    html.Div([
        dcc.Graph(id='time-analysis', className='graph-box'),
        dcc.Graph(id='source-dest-heatmap', className='graph-box')
    ], className='graph-row'),
    
    # Quatrième ligne (pleine largeur)
    html.Div([
        dcc.Graph(id='monthly-trends', className='full-width-graph')
    ]),
    
    # Tableau de données (optionnel)
    html.Div([
        dash_table.DataTable(
            id='data-table',
            columns=[{"name": i, "id": i} for i in data.columns],
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={
                'height': 'auto',
                'minWidth': '100px', 'width': '100px', 'maxWidth': '180px',
                'whiteSpace': 'normal'
            }
        )
    ], className='table-container')
], style={'fontFamily': 'Arial, sans-serif'})

# CSS personnalisé
app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

# Callback pour les KPI
@app.callback(
    [Output('kpi-nb-vols', 'children'),
     Output('kpi-prix-moyen', 'children'),
     Output('kpi-duree-moyenne', 'children'),
     Output('kpi-remplissage', 'children')],
    [Input('airline-selector', 'value'),
     Input('price-range', 'value')]
)
def update_kpis(selected_airlines, price_range):
    filtered_data = data[
        (data['Airline'].isin(selected_airlines)) & 
        (data['Price'] >= price_range[0]) & 
        (data['Price'] <= price_range[1])
    ]
    
    nb_vols = len(filtered_data)
    prix_moyen = filtered_data['Price'].mean()
    duree_moyenne = filtered_data['Duration_min'].mean()
    
    # Calcul du taux de remplissage (exemple fictif)
    taux_remplissage = (len(filtered_data) / len(data)) * 100
    
    return (
        html.Div([
            html.H3("Nombre de Vols"),
            html.H2(f"{nb_vols:,}"),
            html.P(f"{taux_remplissage:.1f}% du total")
        ]),
        html.Div([
            html.H3("Prix Moyen"),
            html.H2(f"{prix_moyen:,.0f}"),
            html.P(f"Min: {filtered_data['Price'].min():,.0f} | Max: {filtered_data['Price'].max():,.0f} ")
        ]),
        html.Div([
            html.H3("Durée Moyenne"),
            html.H2(f"{duree_moyenne/60:.1f}h"),
            html.P(f"({duree_moyenne:.0f} minutes)")
        ]),
        html.Div([
            html.H3("Compagnies"),
            html.H2(f"{len(selected_airlines)}"),
            html.P(f"sur {len(data['Airline'].unique())} totales")
        ])
    )

# Callback pour les graphiques 
@app.callback(
    [Output('price-distribution', 'figure'),
     Output('duration-distribution', 'figure'),
     Output('price-by-airline', 'figure'),
     Output('price-by-stops', 'figure'),
     Output('time-analysis', 'figure'),
     Output('source-dest-heatmap', 'figure'),
     Output('monthly-trends', 'figure')],
    [Input('airline-selector', 'value'),
     Input('price-range', 'value')]
)
def update_dashboard(selected_airlines, price_range):
    filtered_data = data[
        (data['Airline'].isin(selected_airlines)) & 
        (data['Price'] >= price_range[0]) & 
        (data['Price'] <= price_range[1])
    ]
    
    # 1. Distribution des prix
    price_fig = px.histogram(
        filtered_data, 
        x='Price', 
        nbins=50,
        title='Distribution des Prix',
        color_discrete_sequence=['#636EFA']
    )
    price_fig.update_layout(showlegend=False)
    
    # 2. Distribution de la durée
    duration_fig = px.histogram(
        filtered_data, 
        x='Duration_min', 
        nbins=50,
        title='Distribution de la Durée (minutes)',
        color_discrete_sequence=['#EF553B']
    )
    duration_fig.update_layout(showlegend=False)
    
    # 3. Prix par compagnie
    airline_fig = px.box(
        filtered_data, 
        x='Airline', 
        y='Price',
        title='Prix par Compagnie Aérienne',
        color='Airline'
    )
    airline_fig.update_layout(xaxis_tickangle=-45)
    
    # 4. Prix par nombre d'escales
    stops_fig = px.box(
        filtered_data, 
        x='Total_Stops', 
        y='Price',
        title='Prix par Nombre d\'Escales',
        color='Total_Stops'
    )
    
    # 5. Analyse temporelle 
    time_data = filtered_data['part_of_day'].value_counts().reset_index()
    time_data.columns = ['moment', 'count']
    
    time_fig = px.bar(
        time_data,
        x='moment', 
        y='count',
        title='Vols par Moment de la Journée',
        category_orders={'moment': ['matin', 'après-midi', 'soir', 'nuit']},
        color='moment',
        labels={'moment': 'Moment', 'count': 'Nombre de vols'}
    )
    time_fig.update_layout(showlegend=False)
    
    # 6. Heatmap Source-Destination
    heatmap_fig = px.density_heatmap(
        filtered_data,
        x='Source',
        y='Destination',
        z='Price',
        histfunc='avg',
        title='Prix Moyen par Source/Destination',
        color_continuous_scale='Viridis'
    )
    
    # 7. Tendances mensuelles
    monthly_data = filtered_data.groupby('Journey_month')['Price'].mean().reset_index()
    month_names = {
        1: "Jan", 2: "Fév", 3: "Mar", 4: "Avr", 5: "Mai", 6: "Juin",
        7: "Juil", 8: "Août", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Déc"
    }
    monthly_data['Month'] = monthly_data['Journey_month'].map(month_names)
    
    trend_fig = px.line(
        monthly_data,
        x='Month',
        y='Price',
        title='Prix Moyen par Mois',
        markers=True
    )
    trend_fig.update_traces(line_color='#00CC96')
    
    return (price_fig, duration_fig, airline_fig, stops_fig, 
            time_fig, heatmap_fig, trend_fig)

# Style CSS supplémentaire
styles = """
.kpi-container {
    display: flex;
    justify-content: space-between;
    margin: 20px 0;
}
.kpi-box {
    background: white;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    text-align: center;
    width: 23%;
}
.graph-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
}
.graph-box {
    width: 49%;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    padding: 10px;
}
.full-width-graph {
    width: 100%;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    padding: 10px;
}
.filter-container {
    background: white;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
.table-container {
    margin-top: 20px;
    background: white;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
"""

app.index_string = f'''
<!DOCTYPE html>
<html>
    <head>
        <title>Dashboard Vols</title>
        <style>{styles}</style>
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>
'''
if __name__ == '__main__':
    app.run(debug=True, port=8050)

server =app.server

