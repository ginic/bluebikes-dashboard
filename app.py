from datetime import datetime, date
import logging
import logging.config
import sys

from dash import Dash, html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

import bluebikesdashboard.utils as bbdutils
import bluebikesdashboard.query_builder as bbdq

# Configure logging and the database path for the whole app
logger = logging.getLogger(__name__)
database, logging_config = bbdutils.load_config("config.json")
logging.config.dictConfig(logging_config)
logger.info("Using database %s", database)

app = Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN])
server = app.server


TITLE = "🚲 Bluebikes Trips Analysis Dashboard 🚲"
INTRO_TEXT = "Explore Bluebikes trip data."
TOP_DIV = html.Div(
    children=[html.H1(children=TITLE), html.Div(children=INTRO_TEXT)],
    style={"textAlign": "center"},
)

DATE_PICKER = html.Div(
    children=[
        dbc.Label("Date range for trips: "),
        dcc.DatePickerRange(
            id="date-picker-range",
            min_date_allowed=date(2023, 4, 1),
            max_date_allowed=datetime.today(),
            initial_visible_month=date(2024, 1, 1),
            start_date=date(2023, 4, 1),
            end_date=date(2024, 12, 1),
        ),
    ]
)

TYPE_CHECKLIST = html.Div(
    children=[
        dbc.Label("Include trips with: "),
        dcc.Checklist(
            id="ride-type-checklist",
            options=["Electric Bikes", "Classic Bikes"],
            value=["Electric Bikes", "Classic Bikes"],
        ),
    ]
)

QUERY_BUTTON = dbc.Button("Plot Results!", id="button-plot", n_clicks=0)

TRIPS_BY_MONTH_PLOT = dcc.Graph(id="output-plot-trips-by-month")

app.layout = dbc.Container(
    html.Div(
        children=[
            html.Br(),
            TOP_DIV,
            html.Br(),
            dbc.Row([dbc.Col(DATE_PICKER), dbc.Col(TYPE_CHECKLIST)]),
            html.Br(),
            dbc.Row([QUERY_BUTTON]),
            html.Br(),
            TRIPS_BY_MONTH_PLOT,
            html.Br(),
        ]
    )
)


@callback(
    Output("output-plot-trips-by-month", "figure"),
    State("date-picker-range", "start_date"),
    State("date-picker-range", "end_date"),
    State("ride-type-checklist", "value"),
    Input("button-plot", "n_clicks"),
)
def update_trips_by_month_plot(start_date, end_date, ride_types, n_clicks):
    use_ebikes = "Electric Bikes" in ride_types
    use_classic_bikes = "Classic Bikes" in ride_types
    df = bbdq.query_trips_by_date_range(database, start_date, end_date, use_ebikes, use_classic_bikes)
    fig = px.line(df, x="month", y="num_trips", color="rideable_type")

    fig.update_layout(
        title=dict(text="Monthly Bluebikes Trips"),
        xaxis=dict(title=dict(text="Month")),
        yaxis=dict(title=dict(text="Number of Trips")),
    )

    return fig


if __name__ == "__main__":
    logger.info("Starting app")
    try:
        # python app.py debug (or similar)
        if len(sys.argv) > 1:
            app.run(debug=True)
        # python app.py
        else:
            app.run_server()
    except Exception as e:
        logger.error(e)
