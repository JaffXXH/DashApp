# app.py
import dash
from dash import Dash, html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
from dash_ag_grid import AgGrid
import pandas as pd
from datetime import datetime
import json
from typing import List, Dict, Any
import asyncio
from models import Alert, AlertImportance, AlertStatus, AssetClass
from mock_data import generate_mock_alerts, generate_alert

# Initialize the Dash app
# Dark mode => external_stylesheets = [dbc.themes.DARKLY]
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Real-Time Alert Monitor"

# Mock user data - in production this would come from authentication
CURRENT_USER = "analyst@company.com"
AVAILABLE_USERS = [
    "analyst@company.com",
    "trader@company.com",
    "manager@company.com",
    "support@company.com"
]

# Initialize alert data
# initial_alerts = [
#     {
#         "id": "1",
#         "timestamp": datetime.utcnow().isoformat(),
#         "importance": "Critical",
#         "title": "Price Discrepancy Detected",
#         "description": "Significant price difference between source systems",
#         "asset_classes": ["Equities", "FX"],
#         "underliers": [{"id": "AAPL", "name": "Apple Inc.", "asset_class": "Equities"}],
#         "processes": [{"id": "pricing", "name": "Pricing Engine", "description": "Main pricing process"}],
#         "status": "New"
#     },
#     {
#         "id": "2",
#         "timestamp": datetime.utcnow().isoformat(),
#         "importance": "Warning",
#         "title": "Late Data Feed",
#         "description": "Market data feed delayed by 15 seconds",
#         "asset_classes": ["Fixed Income"],
#         "underliers": [{"id": "UST10Y", "name": "10Y US Treasury", "asset_class": "Fixed Income"}],
#         "processes": [{"id": "datafeed", "name": "Data Feed", "description": "Market data ingestion"}],
#         "status": "New"
#     }
# ]

initial_alerts = [alert.dict() for alert in generate_mock_alerts(20)]
initial_df = pd.DataFrame(initial_alerts)

# Convert to DataFrame for AG-Grid#
df = pd.DataFrame(initial_alerts)

# Define AG-Grid column definitions
columnDefs = [
    {
        "field": "id",
        "headerName": "ID",
        "filter": "agTextColumnFilter",
        "width": 100
    },
    {
        "field": "timestamp",
        "headerName": "Timestamp",
        "filter": "agDateColumnFilter",
        "valueFormatter": {"function": "d3.timeFormat('%Y-%m-%d %H:%M:%S')(new Date(params.value))"},
        "width": 180
    },
    {
        "field": "importance",
        "headerName": "Level",
        "cellStyle": {"function": "alertLevelStyle(params)"},
        "width": 120
    },
    {
        "field": "title",
        "headerName": "Title",
        "tooltipField": "title",
        "width": 200
    },
    {
        "field": "description",
        "headerName": "Description",
        "tooltipField": "description",
        "width": 300
    },
    {
        "field": "asset_classes",
        "headerName": "Asset Classes",
        "valueFormatter": {"function": "params.value.join(', ')"},
        "width": 150
    },
    {
        "field": "underliers",
        "headerName": "Underliers",
        "valueFormatter": {"function": "params.value.map(u => u.name).join(', ')"},
        "width": 150
    },
    {
        "field": "status",
        "headerName": "Status",
        "cellStyle": {"function": "alertStatusStyle(params)"},
        "width": 120
    },
    {
        "field": "actions",
        "headerName": "Actions",
        "cellRenderer": "alertActionsRenderer",
        "width": 250,
        "sortable": False,
        "filter": False
    }
]

# Define AG-Grid custom components
alertGrid = AgGrid(
    id="alert-grid",
    columnDefs=columnDefs,
    rowData=initial_df.to_dict("records"),
    dashGridOptions={
        "rowHeight": 40,
        "animateRows": True,
        "pagination": True,
        "paginationPageSize": 20,
        "suppressCellFocus": True,
        "enableCellTextSelection": True,
        "defaultColDef": {
            "filter": True,
            "sortable": True,
            "resizable": True,
            "floatingFilter": True
        }
    },
    columnSize="sizeToFit",
    style={"height": "75vh", "width": "100%"},
    getRowId="params.data.id",
    className="ag-theme-alpine-dark",
    persistence=True,
    persistence_type="memory",
    #update_mode="model_changed",
)

# Define the app layout
app.layout = dbc.Container(
    fluid=True,
    children=[
        dcc.Store(id="alert-store", data= initial_df.to_dict("records"), storage_type="memory"),
        dcc.Interval(id="update-interval", interval=5000, n_intervals=0),
        dcc.ConfirmDialog(
            id="confirm-action",
            message="Are you sure you want to perform this action?",
        ),
        dbc.Row(
            dbc.Col(
                html.H1("Real-Time Alert Monitor", className="text-center my-4"),
                width=12
            )
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Alert Summary"),
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                html.Div(
                                                    [
                                                        html.Span("0", id="critical-count", className="count-display critical"),
                                                        html.P("Critical Alerts", className="count-label")
                                                    ],
                                                    className="count-container"
                                                ),
                                                width=4
                                            ),
                                            dbc.Col(
                                                html.Div(
                                                    [
                                                        html.Span("0", id="warning-count", className="count-display warning"),
                                                        html.P("Warning Alerts", className="count-label")
                                                    ],
                                                    className="count-container"
                                                ),
                                                width=4
                                            ),
                                            dbc.Col(
                                                html.Div(
                                                    [
                                                        html.Span("0", id="info-count", className="count-display info"),
                                                        html.P("Info Alerts", className="count-label")
                                                    ],
                                                    className="count-container"
                                                ),
                                                width=4
                                            )
                                        ]
                                    )
                                ]
                            )
                        ],
                        className="mb-4"
                    ),
                    width=12
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    "Alerts",
                                    dbc.Button(
                                        "Refresh",
                                        id="refresh-button",
                                        color="primary",
                                        size="sm",
                                        className="float-end"
                                    )
                                ]
                            ),
                            dbc.CardBody([alertGrid])
                        ]
                    ),
                    width=12
                )
            ]
        ),
        dbc.Modal(
            [
                dbc.ModalHeader("Alert Details"),
                dbc.ModalBody(id="alert-details-content"),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Close",
                            id="close-alert-details",
                            className="ms-auto",
                            n_clicks=0
                        )
                    ]
                )
            ],
            id="alert-details-modal",
            size="lg",
            is_open=False,
        ),
        dcc.Store(            id="alert-storeX",
            data=initial_df.to_dict("records"),
            storage_type="memory"),
    ]
)

# Define JavaScript functions for AG-Grid
app.clientside_callback(
    """
    function alertLevelStyle(params) {
        if (params.value === 'Critical') {
            return {color: 'white', backgroundColor: '#dc3545', fontWeight: 'bold'};
        } else if (params.value === 'Warning') {
            return {color: 'black', backgroundColor: '#ffc107', fontWeight: 'bold'};
        } else {
            return {color: 'white', backgroundColor: '#17a2b8'};
        }
    }
    
    function alertStatusStyle(params) {
        if (params.value === 'New') {
            return {color: 'white', backgroundColor: '#6c757d', fontWeight: 'bold'};
        } else if (params.value === 'Acknowledged') {
            return {color: 'white', backgroundColor: '#17a2b8'};
        } else if (params.value === 'Assigned') {
            return {color: 'white', backgroundColor: '#6610f2'};
        } else if (params.value === 'In Progress') {
            return {color: 'black', backgroundColor: '#fd7e14'};
        } else {
            return {color: 'white', backgroundColor: '#28a745'};
        }
    }
    
    function alertActionsRenderer(params) {
        const alertId = params.data.id;
        const status = params.data.status;
        
        let buttons = '';
        
        if (status === 'New') {
            buttons += `
                <button class="btn btn-sm btn-success action-btn" data-action="acknowledge" data-alert-id="${alertId}">
                    Acknowledge
                </button>
                <button class="btn btn-sm btn-primary action-btn" data-action="take-action" data-alert-id="${alertId}">
                    Take Action
                </button>
                <div class="dropdown d-inline-block">
                    <button class="btn btn-sm btn-info dropdown-toggle" type="button" data-bs-toggle="dropdown">
                        Assign
                    </button>
                    <ul class="dropdown-menu">
                        ${['analyst@company.com', 'trader@company.com', 'manager@company.com', 'support@company.com']
                            .map(user => `
                                <li>
                                    <a class="dropdown-item assign-option" href="#" data-alert-id="${alertId}" data-user="${user}">
                                        ${user}
                                    </a>
                                </li>
                            `).join('')}
                    </ul>
                </div>
            `;
        } else if (status === 'Acknowledged') {
            buttons += `
                <button class="btn btn-sm btn-primary action-btn" data-action="take-action" data-alert-id="${alertId}">
                    Take Action
                </button>
                <div class="dropdown d-inline-block">
                    <button class="btn btn-sm btn-info dropdown-toggle" type="button" data-bs-toggle="dropdown">
                        Assign
                    </button>
                    <ul class="dropdown-menu">
                        ${['analyst@company.com', 'trader@company.com', 'manager@company.com', 'support@company.com']
                            .map(user => `
                                <li>
                                    <a class="dropdown-item assign-option" href="#" data-alert-id="${alertId}" data-user="${user}">
                                        ${user}
                                    </a>
                                </li>
                            `).join('')}
                    </ul>
                </div>
            `;
        } else if (status === 'Assigned' || status === 'In Progress') {
            if (params.data.assigned_to === 'analyst@company.com') {
                buttons += `
                    <button class="btn btn-sm btn-primary action-btn" data-action="take-action" data-alert-id="${alertId}">
                        Work On
                    </button>
                    <button class="btn btn-sm btn-success action-btn" data-action="resolve" data-alert-id="${alertId}">
                        Resolve
                    </button>
                `;
            } else {
                buttons += `
                    <span class="badge bg-info">Assigned to ${params.data.assigned_to}</span>
                `;
            }
        }
        
        return buttons;
    }
    """,
    Output("dummy-output", "children"),  # Dummy output
    Input("alert-grid", "cellRendererData")
)

# Callback for handling alert actions
@app.callback(
    Output("confirm-action", "displayed"),
    Output("action-store", "data"),
    Input("alert-grid", "cellRendererData"),
    State("alert-store", "data"),
    prevent_initial_call=True
)
def handle_alert_actions(data: Dict[str, Any], alert_data: List[Dict[str, Any]]) -> tuple:
    """Handle alert actions from the AG-Grid cell renderer"""
    if not data or "triggered" not in data:
        return no_update, no_update
        
    triggered = data["triggered"]
    if not triggered:
        return no_update, no_update
        
    alert_id = triggered.get("alert-id")
    action = triggered.get("action")
    user = triggered.get("user")
    
    if not alert_id or not action:
        return no_update, no_update
        
    # For assign actions, we need to get the user from the dropdown
    if action == "assign" and not user:
        return no_update, no_update
        
    # Store the action details for confirmation
    action_data = {"alert_id": alert_id, "action": action, "user": user}
    
    # Show confirmation for critical alerts
    alert = next((a for a in alert_data if a["id"] == alert_id), None)
    if alert and alert["importance"] == "Critical":
        return True, action_data
        
    # For non-critical alerts, proceed without confirmation
    return False, action_data

# Callback to update alert status after confirmation
@app.callback(
    Output("alert-store", "data"),
    Input("confirm-action", "submit_n_clicks"),
    State("action-store", "data"),
    State("alert-store", "data"),
    prevent_initial_call=True
)
def update_alert_status(submit_clicks: int, action_data: Dict[str, Any], alert_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Update alert status based on user action"""
    if not submit_clicks or not action_data:
        return no_update
        
    alert_id = action_data["alert_id"]
    action = action_data["action"]
    user = action_data.get("user", CURRENT_USER)
    
    updated_alerts = []
    for alert in alert_data:
        if alert["id"] == alert_id:
            updated_alert = alert.copy()
            
            if action == "acknowledge":
                updated_alert["status"] = "Acknowledged"
                updated_alert["acknowledged_by"] = user
                updated_alert["acknowledged_at"] = datetime.utcnow().isoformat()
            elif action == "take-action":
                updated_alert["status"] = "In Progress"
                updated_alert["assigned_to"] = user
            elif action == "assign":
                updated_alert["status"] = "Assigned"
                updated_alert["assigned_to"] = user
            elif action == "resolve":
                updated_alert["status"] = "Resolved"
                
            updated_alerts.append(updated_alert)
        else:
            updated_alerts.append(alert)
            
    return updated_alerts

# Callback to update summary counts
@app.callback(
    [
        Output("critical-count", "children"),
        Output("warning-count", "children"),
        Output("info-count", "children")
    ],
    Input("alert-store", "data")
)
def update_summary_counts(alert_data: List[Dict[str, Any]]) -> tuple:
    """Update the alert summary counts"""
    critical = sum(1 for alert in alert_data if alert["importance"] == "Critical" and alert["status"] != "Resolved")
    warning = sum(1 for alert in alert_data if alert["importance"] == "Warning" and alert["status"] != "Resolved")
    info = sum(1 for alert in alert_data if alert["importance"] == "Information" and alert["status"] != "Resolved")
    
    return critical, warning, info

# Callback to refresh data
# @app.callback(
#     Output("alert-store", "data", allow_duplicate=True),
#     Input("refresh-button", "n_clicks"),
#     prevent_initial_call=True
# )

# @app.callback(
#     Output("alert-store", "data", allow_duplicate=True),
#     Input("update-interval", "n_intervals"),
#     State("alert-store", "data"),
#     prevent_initial_call=True
# )
# def add_new_alerts(n):
#     if n % 5 == 0:  # Every 5 intervals (25 seconds)
#         new_alert = generate_alert().dict()
#         return [new_alert] + alertGrid.get.rowData()  # Add new alert to existing data
#     return no_update
# @app.callback(
#     Output("alert-grid", "rowData"),
#     Input("alert-store", "data"),
#     prevent_initial_call=True
# )
# def update_grid_data(alert_data):
#     if not alert_data:
#         return no_update
#     return alert_data

# def refresh_data(n_clicks: int) -> List[Dict[str, Any]]:
#     """Refresh alert data"""
#     # In a real application, this would fetch new data from the server
#     return no_update

app.clientside_callback(
    """
    function(params) {
        if (!window.agGridInitialized) {
            window.agGridInitialized = true;
            return dash_clientside.no_update;
        }
        return dash_clientside.no_update;
    }
    """,
    Output("alert-grid", "cellRendererData"),
    Input("alert-grid", "virtualRowData")
)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)