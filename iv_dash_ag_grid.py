import dash
from dash import html, dcc, Input, Output, State, MATCH
import dash_ag_grid as dag
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from scipy.interpolate import interp1d

# -----------------------------
# ⚙️ Sample Data
# -----------------------------
currency_data = {
    'EURUSD': {
        'TENOR': ['1M', '2M', '3M', '6M', '1Y'],
        'OFFSET': [0.0]*5,
        'ATM_RAW': [8.2, 8.0, 8.0, 8.1, 8.2],
        '10RR': [-0.4, -0.3, -0.2, -0.7, -0.1],
        '10STR': [7.6, 7.7, 7.8, 7.9, 8.2],
        '25RR': [-0.8, -0.7, -0.5, -0.6, -7.8],
        '25STR': [6.9, 7.0, 7.1, 7.6, 7.9]
    },
    'USDJPY': {
        'TENOR': ['1M', '2M', '3M', '6M', '1Y'],
        'OFFSET': [0.0]*5,
        'ATM_RAW': [7.8, 7.6, 7.5, 7.7, 7.9],
        '10RR': [-0.3, -0.2, -0.1, -0.5, -0.2],
        '10STR': [7.3, 7.4, 7.4, 7.2, 7.7],
        '25RR': [-0.6, -0.5, -0.4, -0.5, -6.5],
        '25STR': [6.5, 6.6, 6.7, 7.1, 7.2]
    }
}

# -----------------------------
# 🔁 Compute ATM
# -----------------------------
def initialize_data():
    dfs = {}
    for pair, data in currency_data.items():
        df = pd.DataFrame(data)
        df['ATM'] = df['ATM_RAW'] + df['OFFSET']
        df['CONFIDENCE'] = 1.0
        df['EXTRAPOLATED'] = False
        dfs[pair] = df
    return dfs

dfs = initialize_data()

# -----------------------------
# 🎨 Grid Styling
# -----------------------------
columnDefs = [
    {"field": "TENOR", "headerName": "TENOR", "width": 90},
    {"field": "OFFSET", "headerName": "OFFSET", "width": 90, "editable": True},
    {"field": "ATM", "headerName": "ATM", "width": 90},
    {"field": "ATM_RAW", "headerName": "ATM_RAW", "width": 90},
    {"field": "10RR", "headerName": "10RR", "width": 90, "editable": True},
    {"field": "10STR", "headerName": "10STR", "width": 90, "editable": True},
    {"field": "25RR", "headerName": "25RR", "width": 90, "editable": True},
    {"field": "25STR", "headerName": "25STR", "width": 90, "editable": True},
    {"field": "CONFIDENCE", "headerName": "CONF", "width": 80},
    {"field": "EXTRAPOLATED", "headerName": "EXTRA", "width": 80}
]

defaultColDef = {
    "resizable": True,
    "sortable": False,
    "filter": False,
    "headerClass": "header-class",
    "autoSize": True
}

# -----------------------------
# 🧠 Interpolation Utilities
# -----------------------------
def tenor_to_months(tenor):
    if tenor.endswith('M'):
        return int(tenor[:-1])
    elif tenor.endswith('Y'):
        return int(tenor[:-1]) * 12
    else:
        raise ValueError(f"Unsupported tenor format: {tenor}")

def compute_confidence(month, known_months):
    known_months = np.array(sorted(known_months))
    if month in known_months:
        return 1.0
    min_m, max_m = known_months[0], known_months[-1]
    if month < min_m or month > max_m:
        return 0.2
    diffs = np.abs(known_months - month)
    nearest = np.sort(diffs)[:2]
    avg_dist = np.mean(nearest)
    spread = max_m - min_m
    score = 1.0 - (avg_dist / spread)
    return max(0.3, round(score, 2))

def interpolate_row(df, tenor, method='cubic'):
    month = tenor_to_months(tenor)
    df['MONTHS'] = df['TENOR'].apply(tenor_to_months)
    df = df.sort_values('MONTHS')
    existing_months = df['MONTHS'].values
    if month in existing_months:
        return None

    row = {'TENOR': tenor, 'MONTHS': month}
    row['EXTRAPOLATED'] = month < min(existing_months) or month > max(existing_months)
    row['CONFIDENCE'] = compute_confidence(month, existing_months)

    for col in ['ATM_RAW', '10RR', '10STR', '25RR', '25STR']:
        x, y = df['MONTHS'].values, df[col].values
        try:
            f = interp1d(x, y, kind=method, fill_value="extrapolate")
            row[col] = float(f(month))
        except Exception:
            f = interp1d(x, y, kind='linear', fill_value="extrapolate")
            row[col] = float(f(month))

    row['OFFSET'] = 0.0
    row['ATM'] = row['ATM_RAW'] + row['OFFSET']
    return row

# -----------------------------
# 🚀 App Layout
# -----------------------------
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H2("IMPLIED VOLATILITY SKEW MATRIX", style={'textAlign': 'center', 'color': '#00cc99'}),
    dcc.Tabs(id="currency-tabs", value='EURUSD', children=[
        dcc.Tab(label=pair, value=pair) for pair in dfs.keys()
    ]),
    html.Div(id='tab-content')
], style={'backgroundColor': '#111', 'color': '#fff', 'padding': '20px'})

# -----------------------------
# 🔁 Tab Renderer
# -----------------------------
@app.callback(
    Output('tab-content', 'children'),
    Input('currency-tabs', 'value')
)
def render_tab(tab):
    df = dfs[tab]
    tenor_options = [{'label': t, 'value': t} for t in df['TENOR']]
    return html.Div([
        html.H4(tab, style={'textAlign': 'center', 'color': '#ecf0f1'}),
        dag.AgGrid(
            id={'type': 'matrix', 'index': tab},
            columnDefs=columnDefs,
            rowData=df.to_dict('records'),
            defaultColDef=defaultColDef,
            dashGridOptions={"domLayout": "autoHeight", "singleClickEdit": True},
            className="ag-theme-alpine-dark"
        ),
        html.Br(),
        html.Div([
            html.Label("Add Interpolated Tenor", style={'color': '#fff'}),
            dcc.Input(id={'type': 'tenor-input', 'index': tab}, type='text', placeholder='e.g. 4M'),
            html.Button("Add Tenor", id={'type': 'add-tenor-btn', 'index': tab}, n_clicks=0)
        ]),
        html.Br(),
        html.Label("Select Tenor for Smile Plot", style={'color': '#fff'}),
        dcc.Dropdown(id={'type': 'tenor-dropdown', 'index': tab},
                     options=tenor_options,
                     value=tenor_options[0]['value'],
                     style={'width': '200px'}),
        dcc.Graph(id={'type': 'smile-plot', 'index': tab})
    ])

# -----------------------------
# 🔁 Unified Callback
# -----------------------------
@app.callback(
    Output({'type': 'matrix', 'index': MATCH}, 'rowData'),
    Output({'type': 'tenor-dropdown', 'index': MATCH}, 'options'),
    Input({'type': 'matrix', 'index': MATCH}, 'cellValueChanged'),
    Input({'type': 'add-tenor-btn', 'index': MATCH}, 'n_clicks'),
    State({'type': 'tenor-input', 'index': MATCH}, 'value'),
    State({'type': 'matrix', 'index': MATCH}, 'rowData'),
    prevent_initial_call=True
)
def update_matrix_and_tenors(_, n_clicks, new_tenor, rowData):
    df = pd.DataFrame(rowData)

    # 🔁 ATM recalculation
    df['ATM'] = df['ATM_RAW'] + df['OFFSET']

    # ➕ Tenor interpolation
    if new_tenor:
        new_row = interpolate_row(df, new_tenor)
        if new_row:
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df['ATM'] = df['ATM_RAW'] + df['OFFSET']
            df = df.sort_values(by='TENOR', key=lambda x: [tenor_to_months(t) for t in x])

    options = [{'label': t, 'value': t} for t in df['TENOR']]
    return df.to_dict('records'), options

@app.callback(
    Output({'type': 'smile-plot', 'index': MATCH}, 'figure'),
    Input({'type': 'tenor-dropdown', 'index': MATCH}, 'value'),
    Input({'type': 'matrix', 'index': MATCH}, 'rowData'),
    prevent_initial_call=True
)
def update_smile_plot(selected_tenor, rowData):
    df = pd.DataFrame(rowData)
    match = df[df['TENOR'] == selected_tenor]

    if match.empty:
        fig = go.Figure()
        fig.update_layout(
            title="No data available for selected tenor",
            template="plotly_dark",
            height=400
        )
        return fig

    row = match.iloc[0]
    strikes = ['25STR', '10STR', 'ATM', '10RR', '25RR']
    vols = [row['25STR'], row['10STR'], row['ATM'], row['10RR'] + row['ATM'], row['25RR'] + row['ATM']]
    labels = ['25D Put', '10D Put', 'ATM', '10D Call', '25D Call']

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=labels, y=vols, mode='lines+markers', line=dict(color='#00cc99')))
    fig.update_layout(
        title=f"Smile for {selected_tenor}",
        xaxis_title="Strike",
        yaxis_title="Volatility",
        template="plotly_dark",
        height=400
    )
    return fig
if __name__ == '__main__':
    app.run(debug=True)