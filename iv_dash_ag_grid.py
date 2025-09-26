#1
import dash
from dash import Dash, html, dcc, Input, Output, State, callback, dash_table
import dash_ag_grid as dag
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
import json
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

# Load a dark-themed template for Plotly figures
load_figure_template("darkly")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Dash app
app = Dash(__name__, title="Implied Volatility Management System", external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
server = app.server

# Sample initial data structure
def initialize_sample_data():
    """Initialize sample data for all currency pairs"""
    base_tenors = ['1M', '2M', '3M', '6M', '1Y']
    strategies = ['ATM', '10RR', '10STR', '25RR', '25STR']
    
    data = {}
    for currency in ['EURUSD', 'USDJPY', 'GBPUSD']:
        # Skew matrix data
        skew_data = []
        for tenor in base_tenors:
            row = {'TENOR': tenor}
            for strategy in strategies:
                # Generate realistic sample data
                if strategy == 'ATM':
                    value = 8.0 + np.random.uniform(-0.5, 0.5)
                elif 'RR' in strategy:
                    value = -0.3 + np.random.uniform(-0.2, 0.2)
                else:
                    value = 7.5 + np.random.uniform(-0.5, 0.5)
                row[strategy] = round(value, 2)
            skew_data.append(row)
        
        # 0D ATM VOL data
        atm_vol_data = {
            'current_value': 8.2,
            'decay_method': 'Exponential',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'applied_vol': 8.2
        }
        
        # Generate smile data and convert to dictionary for JSON serialization
        smile_df = generate_smile_data()
        smile_data = smile_df.to_dict('records')
        
        data[currency] = {
            'skew_matrix': skew_data,
            'atm_vol': atm_vol_data,
            'smile_data': smile_data  # Store as list of dicts instead of DataFrame
        }
    
    return data

def generate_smile_data():
    """Generate sample volatility smile data"""
    strikes = [90, 95, 97.5, 100, 102.5, 105, 110]
    implied_vols = [8.5, 8.2, 8.0, 7.8, 8.1, 8.4, 8.7]
    return pd.DataFrame({'Strike': strikes, 'Implied_Vol': implied_vols})

# Initialize data store
initial_data = initialize_sample_data()

# Skew Matrix Column Definitions
skew_column_defs = [
    {
        "field": "TENOR",
        "headerName": "TENOR",
        "width": 80,
        "cellStyle": {'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
        "pinned": "left"
    },
    {
        "field": "ATM",
        "headerName": "ATM",
        "width": 90,
        "valueFormatter": {"function": "d3.format('.2f')(params.value)"},
        "cellStyle": {'textAlign': 'center'}
    },
    {
        "field": "10RR",
        "headerName": "10Δ RR",
        "width": 90,
        "valueFormatter": {"function": "d3.format('+.2f')(params.value)"},
        "cellStyle": {'textAlign': 'center'}
    },
    {
        "field": "10STR",
        "headerName": "10Δ STR",
        "width": 90,
        "valueFormatter": {"function": "d3.format('.2f')(params.value)"},
        "cellStyle": {'textAlign': 'center'}
    },
    {
        "field": "25RR",
        "headerName": "25Δ RR",
        "width": 90,
        "valueFormatter": {"function": "d3.format('+.2f')(params.value)"},
        "cellStyle": {'textAlign': 'center'}
    },
    {
        "field": "25STR",
        "headerName": "25Δ STR",
        "width": 90,
        "valueFormatter": {"function": "d3.format('.2f')(params.value)"},
        "cellStyle": {'textAlign': 'center'}
    }
]

def create_skew_matrix_section(currency):
    """Create the skew matrix section"""
    return html.Div([
        html.H3(f"{currency} Implied Volatility Skew Matrix", 
                style={'color': '#34495e', 'marginBottom': '15px'}),
        dag.AgGrid(
            id=f"skew-matrix-{currency}",
            columnDefs=skew_column_defs,
            rowData=[],
            defaultColDef={
                "resizable": True,
                "sortable": False,
                "filter": False
            },
            dashGridOptions={
                "animateRows": False,
                "suppressRowHoverHighlight": True
            },
            style={'height': '300px', 'width': '100%', 'marginBottom': '20px'},
            className="ag-theme-alpine-dark"
        )
    ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 
              'marginRight': '2%', 'padding': '15px', 'border': '1px solid #bdc3c7', 
              'borderRadius': '5px'})

def create_atm_vol_section(currency):
    """Create the 0D ATM VOL management section"""
    return html.Div([
        html.H3("0D ATM Volatility Management", 
                style={'color': '#34495e', 'marginBottom': '15px'}),
        
        # Input and controls
        html.Div([
            dcc.Input(
                id=f"vol-input-{currency}",
                type="number",
                placeholder="Enter new vol value",
                step=0.1,
                min=0,
                max=100,
                style={'width': '150px', 'marginRight': '10px', 'padding': '5px'}
            ),
            html.Button(
                "Apply Vol", 
                id=f"apply-vol-{currency}",
                n_clicks=0,
                style={'marginRight': '10px', 'padding': '5px 10px',
                       'backgroundColor': '#0074D9', 'color': 'white', 'border': 'none',
                       'borderRadius': '3px', 'cursor': 'pointer'}
            ),
            html.Button(
                "Get Current", 
                id=f"get-current-{currency}",
                n_clicks=0,
                style={'padding': '5px 10px', 'backgroundColor': '#28a745', 
                       'color': 'white', 'border': 'none', 'borderRadius': '3px',
                       'cursor': 'pointer'}
            )
        ], style={'marginBottom': '15px'}),
        
        # Current status display
        html.Div(id=f"current-vol-display-{currency}", 
                style={'marginBottom': '15px', 'padding': '10px', 
                       'backgroundColor': '#ecf0f1', 'borderRadius': '3px'}),
        
        # Decay methods table
        html.H4("Active Decay Methods", style={'marginBottom': '10px'}),
        dash_table.DataTable(
            id=f"decay-table-{currency}",
            columns=[
                {"name": "Method", "id": "method"},
                {"name": "Parameter", "id": "parameter"},
                {"name": "Status", "id": "status"},
                {"name": "Last Updated", "id": "last_updated"}
            ],
            data=[],
            style_cell={'textAlign': 'left', 'padding': '5px'},
            style_header={'backgroundColor': '#34495e', 'color': 'white', 'fontWeight': 'bold'},
            style_data={'backgroundColor': '#f8f9fa'}
        )
    ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 
              'padding': '15px', 'border': '1px solid #bdc3c7', 'borderRadius': '5px'})

def create_volatility_smile_section(currency):
    """Create the volatility smile graph section"""
    return html.Div([
        html.H3(f"{currency} Volatility Smile", 
                style={'color': '#34495e', 'marginBottom': '15px'}),
        dcc.Graph(id=f"volatility-smile-{currency}")
    ], style={'width': '100%', 'marginTop': '20px', 'padding': '15px', 
              'border': '1px solid #bdc3c7', 'borderRadius': '5px'})

app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Implied Volatility Management System", 
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'})
    ]),
    
    # Data storage
    dcc.Store(id='volatility-data', data=initial_data),
    dcc.Store(id='api-config', data={
        'api_endpoint': os.getenv('VOLATILITY_API_ENDPOINT', 'http://localhost:8000/api'),
        'data_file_path': os.getenv('DATA_FILE_PATH', '/shared/volatility_data.json'),
        'update_interval': 30000  # 30 seconds
    }),
    
    # Main tabs for currency pairs
    dcc.Tabs(id="currency-tabs", value='EURUSD', children=[
        dcc.Tab(label='EUR/USD', value='EURUSD', 
                style={'padding': '10px', 'fontWeight': 'bold'},
                selected_style={'backgroundColor': '#0074D9', 'color': 'white'}),
        dcc.Tab(label='USD/JPY', value='USDJPY',
                style={'padding': '10px', 'fontWeight': 'bold'},
                selected_style={'backgroundColor': '#0074D9', 'color': 'white'}),
        dcc.Tab(label='GBP/USD', value='GBPUSD',
                style={'padding': '10px', 'fontWeight': 'bold'},
                selected_style={'backgroundColor': '#0074D9', 'color': 'white'}),
    ], style={'marginBottom': '20px'}),
    
    # Tab content
    html.Div(id='tab-content', style={'padding': '20px'}),
    
    # Auto-update component
    dcc.Interval(
        id='interval-component',
        interval=30000,  # 30 seconds
        n_intervals=0
    )
])

@app.callback(
    Output('tab-content', 'children'),
    Input('currency-tabs', 'value')
)
def render_tab_content(selected_currency):
    """Render content for the selected currency tab"""
    return html.Div([
        # Upper section with skew matrix and ATM vol management
        html.Div([
            create_skew_matrix_section(selected_currency),
            create_atm_vol_section(selected_currency)
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '20px'}),
        
        # Lower section with volatility smile graph
        create_volatility_smile_section(selected_currency)
    ])

# FIXED CALLBACK - This replaces the problematic callback

@app.callback(
    [Output("skew-matrix-EURUSD", "rowData"),
     Output("decay-table-EURUSD", "data"),
     Output("volatility-smile-EURUSD", "figure"),
     Output("current-vol-display-EURUSD", "children")],
    [Input('interval-component', 'n_intervals'),
     Input('currency-tabs', 'value'),
     Input('volatility-data', 'data')]
)
def update_all_components(n_intervals, selected_currency, volatility_data):
    """Update components with current data, but only for the active tab."""
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # Update data from external sources if interval triggered
    if triggered_id == 'interval-component':
        updated_data = fetch_updated_data(volatility_data)
        if updated_data:
            volatility_data = updated_data

    # Initialize outputs with dash.no_update for all components
    # 3 currencies * (1 skew + 1 decay + 1 graph + 1 display) = 12 outputs
    outputs = [dash.no_update] * 12

    # Calculate the index positions for the selected currency's outputs in the list
    currency_index = ['EURUSD', 'USDJPY', 'GBPUSD'].index(selected_currency)
    skew_index = currency_index
    decay_index = 3 + currency_index  # After 3 skew matrices
    graph_index = 6 + currency_index  # After 3 decay tables
    display_index = 9 + currency_index # After 3 graphs

    try:
        # Update only the components for the SELECTED currency
        # 1. Skew matrix data
        skew_data = volatility_data.get(selected_currency, {}).get('skew_matrix', [])
        outputs[skew_index] = skew_data

        # 2. Decay methods table data
        decay_data = [
            {
                'method': 'Exponential Decay',
                'parameter': 'λ=0.05',
                'status': 'Active',
                'last_updated': volatility_data.get(selected_currency, {}).get('atm_vol', {}).get('last_updated', 'N/A')
            }
        ]
        outputs[decay_index] = decay_data

        # 3. Volatility smile graph
        smile_data = volatility_data.get(selected_currency, {}).get('smile_data', [])
        smile_df = pd.DataFrame(smile_data) if smile_data else pd.DataFrame()
        fig = create_volatility_smile_figure(smile_df, selected_currency)
        outputs[graph_index] = fig

        # 4. Current vol display
        current_vol = volatility_data.get(selected_currency, {}).get('atm_vol', {}).get('current_value', 'N/A')
        vol_display = html.Div([
            html.Strong("Current 0D ATM Vol: "),
            html.Span(f"{current_vol}%", 
                    style={'color': '#e74c3c', 'fontWeight': 'bold', 'fontSize': '16px'})
        ])
        outputs[display_index] = vol_display

    except Exception as e:
        logger.error(f"Error updating components for {selected_currency}: {e}")

    return outputs

def create_volatility_smile_figure(smile_df, currency):
    """Create volatility smile plot"""
    if smile_df.empty or 'Strike' not in smile_df.columns or 'Implied_Vol' not in smile_df.columns:
        # Create empty figure with proper layout
        fig = go.Figure()
        fig.update_layout(
            title=f"{currency} Volatility Smile - No Data Available",
            template ="plotly_dark",
            xaxis_title="Strike Price",
            yaxis_title="Implied Volatility (%)",
            height=400
        )
        return fig
    
    fig = px.line(smile_df, x='Strike', y='Implied_Vol', template="plotly_dark",
                  title=f"{currency} Volatility Smile",
                  markers=True)
    
    fig.update_layout(
        xaxis_title="Strike Price",
        yaxis_title="Implied Volatility (%)",
        showlegend=False,
        template="plotly_white",
        height=400
    )
    
    return fig

def fetch_updated_data(current_data):
    """
    Fetch updated data from API and file system
    This function handles both API calls and file reading
    """
    try:
        updated_data = current_data.copy()
        
        # Try API first
        try:
            api_config = current_data.get('api_config', {})
            api_endpoint = api_config.get('api_endpoint', '')
            if api_endpoint:
                response = requests.get(api_endpoint, timeout=10)
                if response.status_code == 200:
                    api_data = response.json()
                    updated_data.update(api_data)
                    logger.info("Successfully updated data from API")
        except Exception as e:
            logger.warning(f"API update failed: {e}")
        
        # Try file system
        try:
            file_path = current_data.get('api_config', {}).get('data_file_path', '')
            if file_path and os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    file_data = json.load(f)
                updated_data.update(file_data)
                logger.info("Successfully updated data from file")
        except Exception as e:
            logger.warning(f"File update failed: {e}")
        
        return updated_data
        
    except Exception as e:
        logger.error(f"Data update failed: {e}")
        return current_data
for currency in ['EURUSD', 'USDJPY', 'GBPUSD']:
    @app.callback(
        Output('volatility-data', 'data', allow_duplicate=True),
        [Input(f"apply-vol-{currency}", "n_clicks")],
        [State(f"vol-input-{currency}", "value") ],
        [State('volatility-data', 'data')],
        prevent_initial_call=True
    )
    def update_volatility_value(clicks, vol, volatility_data):
        """Update volatility value when Apply button is clicked"""
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update
        #usd_clicks, gbp_clicks, eur_vol, usd_vol, gbp_
        # Get the triggered button
        triggered_id = ctx.triggered[0]['prop_id']
        
        # Determine which currency was triggered
        if 'EURUSD' in triggered_id:
            currency = 'EURUSD'
            new_vol_value = vol
        elif 'USDJPY' in triggered_id:
            currency = 'USDJPY'
            new_vol_value = vol
        elif 'GBPUSD' in triggered_id:
            currency = 'GBPUSD'
            new_vol_value = vol
        else:
            return dash.no_update
        
        if new_vol_value is not None:
            # Update the data
            if currency in volatility_data:
                volatility_data[currency]['atm_vol']['current_value'] = float(new_vol_value)
                volatility_data[currency]['atm_vol']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                volatility_data[currency]['atm_vol']['applied_vol'] = float(new_vol_value)
                logger.info(f"Updated {currency} vol to {new_vol_value}")
        
        return volatility_data

    @app.callback(
        Output('volatility-data', 'data', allow_duplicate=True),
        Input(f"get-current-{currency}", "n_clicks"),
        [State('volatility-data', 'data')],
        prevent_initial_call=True
    )
    def refresh_current_vol(eur_clicks, volatility_data):
        """Refresh current volatility data when Get Current button is clicked"""
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update
        #  usd_clicks, gbp_clicks,
        # This would typically fetch from an external source
        # For now, we'll just update the timestamp to show it's refreshed
        triggered_id = ctx.triggered[0]['prop_id']
        
        if 'EURUSD' in triggered_id:
            currency = 'EURUSD'
        elif 'USDJPY' in triggered_id:
            currency = 'USDJPY'
        elif 'GBPUSD' in triggered_id:
            currency = 'GBPUSD'
        else:
            return dash.no_update
        
        if currency in volatility_data:
            volatility_data[currency]['atm_vol']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"Refreshed current vol for {currency}")
        
        return volatility_data

# Deployment configuration
def configure_deployment():
    """Configure deployment settings"""
    # Production configuration
    if os.getenv('DASH_ENV') == 'production':
        app.config.update({
            'suppress_callback_exceptions': True,
            'routes_pathname_prefix': '/volatility-management/',
            'requests_pathname_prefix': '/volatility-management/'
        })

if __name__ == '__main__':
    configure_deployment()
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DASH_DEBUG', 'False').lower() == 'true'
    debug = True  # Force debug mode for development
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        dev_tools_hot_reload=debug
    )


#2############################################################
import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_ag_grid as dag
import dash_table
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import threading
import time
import json
import os

# ---------------------- CONFIG ----------------------
CURRENCY_PAIRS = {
    "EURUSD": "EUR/USD",
    "GBPUSD": "GBP/USD",
    "USDJPY": "USD/JPY"
}
DATA_FILE = "iv_data.json"
API_REFRESH_INTERVAL = 30  # seconds

# ---------------------- DATA ----------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {cp: {"skew": [], "atm": 0.0, "decay": []} for cp in CURRENCY_PAIRS}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data_store = load_data()

def simulate_api_updates():
    while True:
        for cp in CURRENCY_PAIRS:
            # Simulate skew matrix update
            tenors = ["1W", "1M", "3M", "6M"]
            strikes = ["25P", "ATM", "25C"]
            skew = [
                {"tenor": t, **{k: round(np.random.uniform(5, 15), 2) for k in strikes}}
                for t in tenors
            ]
            data_store[cp]["skew"] = skew
            data_store[cp]["atm"] = round(np.random.uniform(7, 13), 2)
        save_data(data_store)
        time.sleep(API_REFRESH_INTERVAL)

threading.Thread(target=simulate_api_updates, daemon=True).start()

# ---------------------- APP ----------------------
app = dash.Dash(__name__)
app.title = "Implied Volatility Manager"

app.layout = html.Div([
    dcc.Tabs(
        id="tabs",
        value="EURUSD",
        children=[
            dcc.Tab(label=label, value=cp)
            for cp, label in CURRENCY_PAIRS.items()
        ]
    ),
    html.Div(id="tab-content"),
    dcc.Interval(id="refresh-interval", interval=API_REFRESH_INTERVAL * 1000)
])

# ---------------------- TAB RENDER ----------------------
def render_tab(cp):
    skew = data_store[cp]["skew"]
    atm = data_store[cp]["atm"]
    decay = data_store[cp]["decay"]

    skew_columns = [{"field": "tenor"}] + [
        {"field": strike} for strike in ["25P", "ATM", "25C"]
    ]

    return html.Div([
        html.Div([
            html.Div([
                html.H4("Skew Matrix"),
                dag.AgGrid(
                    id=f"{cp}-skew-matrix",
                    columnDefs=skew_columns,
                    rowData=skew,
                    className="ag-theme-alpine",
                    style={"height": "300px"}
                )
            ], style={"width": "48%", "display": "inline-block"}),

            html.Div([
                html.H4("0d ATM Vol Manager"),
                dcc.Input(id=f"{cp}-atm-input", type="number", value=atm),
                html.Button("Apply", id=f"{cp}-atm-apply"),
                html.Button("Fetch", id=f"{cp}-atm-fetch"),
                dash_table.DataTable(
                    id=f"{cp}-atm-decay-table",
                    columns=[{"name": "Method", "id": "method"}],
                    data=[{"method": m} for m in decay],
                    style_table={"marginTop": "10px"}
                )
            ], style={"width": "48%", "display": "inline-block", "marginLeft": "4%"})
        ]),
        html.Div([
            dcc.Graph(id=f"{cp}-vol-smile")
        ], style={"marginTop": "30px"})
    ])

@app.callback(Output("tab-content", "children"), Input("tabs", "value"))
def update_tab(cp):
    return render_tab(cp)

# ---------------------- CALLBACKS ----------------------
for cp in CURRENCY_PAIRS:
    @app.callback(
        Output(f"{cp}-vol-smile", "figure"),
        Input(f"{cp}-skew-matrix", "rowData"),
        prevent_initial_call=True
    )
    def update_smile(row_data):
        if not row_data:
            return go.Figure()
        tenors = [row["tenor"] for row in row_data]
        fig = go.Figure()
        for strike in ["25P", "ATM", "25C"]:
            vols = [row[strike] for row in row_data]
            fig.add_trace(go.Scatter(x=tenors, y=vols, mode="lines+markers", name=strike))
        fig.update_layout(title="Implied Volatility Smile", xaxis_title="Tenor", yaxis_title="Volatility")
        return fig

    @app.callback(
        Output(f"{cp}-atm-input", "value"),
        Input(f"{cp}-atm-fetch", "n_clicks"),
        prevent_initial_call=True
    )
    def fetch_atm(n):
        return data_store[cp]["atm"]

    @app.callback(
        Output(f"{cp}-atm-decay-table", "data"),
        Input(f"{cp}-atm-apply", "n_clicks"),
        State(f"{cp}-atm-input", "value"),
        prevent_initial_call=True
    )
    def apply_atm(n, new_value):
        data_store[cp]["atm"] = new_value
        data_store[cp]["decay"].append(f"Manual override to {new_value}")
        save_data(data_store)
        return [{"method": m} for m in data_store[cp]["decay"]]

    @app.callback(
        Output(f"{cp}-skew-matrix", "rowData"),
        Input("refresh-interval", "n_intervals")
    )
    def refresh_skew(n):
        return data_store[cp]["skew"]

# ---------------------- RUN ----------------------
if __name__ == "__main__":
    app.run(debug=True)
