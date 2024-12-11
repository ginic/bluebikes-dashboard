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

station_names_to_ids = {d["station_name"]: d["id"] for d in bbdq.query_stations(database).to_dict("records")}
station_names = list(station_names_to_ids.keys())


TITLE = "🚲 Bluebikes Trips Analysis Dashboard 🚲"
INTRO_TEXT = "Bluebikes bike share riders took over 4.5 million trips in the past year, riding for a collective 1.2 million hours or 50,000 days! That's a lot of cycling."
DASHBOARD_INSTRUCTIONS = "Where were they all going? Take a look below to see! You can see how many trips started or ended at certain bike share station locations and when e-bikes were introduced. By viewing average trip duration, you can even see where users take long, leisurely rides from and which stations are used for quick trips. Once you've picked your options, click the big blue button to show results."
TOP_DIV = html.Div(
    children=[
        html.H1(children=TITLE),
        html.Br(),
        html.Div(children=[html.P(INTRO_TEXT), html.P(DASHBOARD_INSTRUCTIONS)], style={"width": "80vw"}),
    ],
    style={"textAlign": "center"},
)

DATE_PICKER = [
    dbc.Label("Date range for trips: ", html_for="date-picker-range", width="auto"),
    dbc.Col(
        dcc.DatePickerRange(
            id="date-picker-range",
            min_date_allowed=date(2023, 4, 1),
            max_date_allowed=datetime.today(),
            initial_visible_month=date(2024, 1, 1),
            start_date=date(2023, 4, 1),
            end_date=date(2024, 12, 1),
        ),
        className="me-3",
    ),
]

E_BIKES_LABEL = "Electric Bike"
CLASSIC_BIKES_LABEL = "Classic Bike"
TYPE_CHECKLIST = [
    dbc.Label("Trips by: ", html_for="ride-type-checklist", width="auto"),
    dbc.Col(
        dcc.Checklist(
            id="ride-type-checklist",
            options=[E_BIKES_LABEL, CLASSIC_BIKES_LABEL],
            value=[E_BIKES_LABEL, CLASSIC_BIKES_LABEL],
        ),
        className="me-3",
    ),
]

START_STATIONS_SELECTOR = [
    dbc.Label("Trips starting at: ", html_for="start-stations-dropdown", width="auto"),
    dbc.Col(
        dcc.Dropdown(station_names, multi=True, placeholder="Choose starting stations", id="start-stations-dropdown"),
        className="me-3",
    ),
]


END_STATIONS_SELECTOR = [
    dbc.Label("Trips ending at: ", html_for="end-stations-dropdown", width="auto"),
    dbc.Col(
        dcc.Dropdown(station_names, multi=True, placeholder="Choose end stations", id="end-stations-dropdown"),
        className="me-3",
    ),
]


TRIPS_START_OR_END_RADIO = [
    dbc.Label("Display statistics for trips that: ", html_for="trips-start-or-end-radio", width="auto"),
    dbc.Col(
        dcc.RadioItems(
            [{"label": "Start at stations", "value": "start"}, {"label": "End at stations", "value": "end"}],
            "start",
            id="trips-start-or-end-radio",
        ),
        className="me-3",
    ),
]

NUM_TRIPS_METRIC_LABEL = "Total number of trips"
AVG_DURATION_METRIC_LABEL = "Average trip duration"
METRIC_CHOICE_RADIO = [
    dbc.Label("Compute and display: ", html_for="metric-radio", width="auto"),
    dbc.Col(
        dcc.RadioItems(
            [NUM_TRIPS_METRIC_LABEL, AVG_DURATION_METRIC_LABEL],
            NUM_TRIPS_METRIC_LABEL,
            id="metric-radio",
        ),
        className="me-3",
    ),
]


QUERY_BUTTON = dbc.Button("Plot Results!", id="button-plot", n_clicks=0)

TRIPS_BY_MONTH_PLOT = dcc.Loading(
    [dcc.Graph(id="output-plot-trips-by-month", style={"height": "50vh"})],
    overlay_style={"visibility": "visible", "opacity": 0.5, "backgroundColor": "white"},
    custom_spinner=html.H2([dbc.Spinner(color="warning")]),
)

STATION_MAP_PLOT = dcc.Loading(
    [dcc.Graph(id="output-plot-station-map", style={"width": "90vw", "height": "90vh"})],
    overlay_style={"visibility": "visible", "opacity": 0.5, "backgroundColor": "white"},
    custom_spinner=html.H2([dbc.Spinner(color="warning")]),
)

app.layout = dbc.Container(
    html.Div(
        children=[
            html.Br(),
            TOP_DIV,
            html.Hr(),
            dbc.Row([dbc.Col(html.H3("Trip selection options"))]),
            dbc.Row(DATE_PICKER + TYPE_CHECKLIST, className="g-3"),
            html.Br(),
            dbc.Row(START_STATIONS_SELECTOR + END_STATIONS_SELECTOR, className="g-3"),
            html.Br(),
            dbc.Row([dbc.Col(html.H3("Map display options"))]),
            dbc.Row(METRIC_CHOICE_RADIO + TRIPS_START_OR_END_RADIO, className="g-3"),
            html.Br(),
            dbc.Row([QUERY_BUTTON]),
            html.Br(),
            TRIPS_BY_MONTH_PLOT,
            html.Br(),
            STATION_MAP_PLOT,
        ]
    )
)


def get_ride_type_as_boolean(ride_types):
    use_ebikes = E_BIKES_LABEL in ride_types
    use_classic_bikes = CLASSIC_BIKES_LABEL in ride_types
    return use_ebikes, use_classic_bikes


def get_station_ids(station_names):
    if station_names:
        station_ids = [station_names_to_ids[n] for n in station_names]
        logger.debug("User selection stations: %s; Corresponding ids: %s", station_names, station_ids)
        return station_ids

    return None


@callback(
    Output("output-plot-trips-by-month", "figure"),
    State("date-picker-range", "start_date"),
    State("date-picker-range", "end_date"),
    State("ride-type-checklist", "value"),
    State("start-stations-dropdown", "value"),
    State("end-stations-dropdown", "value"),
    Input("button-plot", "n_clicks"),
)
def update_trips_by_month_plot(start_date, end_date, ride_types, start_stations, end_stations, n_clicks):
    use_ebikes, use_classic_bikes = get_ride_type_as_boolean(ride_types)
    start_station_ids = get_station_ids(start_stations)
    end_station_ids = get_station_ids(end_stations)

    df = bbdq.query_trips_by_date_range(
        database, start_date, end_date, use_ebikes, use_classic_bikes, start_station_ids, end_station_ids
    )
    fig = px.line(df, x="month", y="num_trips", color="rideable_type")

    fig.update_layout(
        title=dict(text="Monthly Bluebikes Trips"),
        xaxis=dict(title=dict(text="Month")),
        yaxis=dict(title=dict(text="Number of Trips")),
        legend_title="Bike Type",
    )

    return fig


@callback(
    Output("output-plot-station-map", "figure"),
    State("date-picker-range", "start_date"),
    State("date-picker-range", "end_date"),
    State("ride-type-checklist", "value"),
    State("start-stations-dropdown", "value"),
    State("end-stations-dropdown", "value"),
    State("trips-start-or-end-radio", "value"),
    State("metric-radio", "value"),
    Input("button-plot", "n_clicks"),
)
def update_station_map_plot(
    start_date, end_date, ride_types, start_stations, end_stations, trips_start_or_end, metric, n_clicks
):
    use_ebikes, use_classic_bikes = get_ride_type_as_boolean(ride_types)
    start_station_ids = get_station_ids(start_stations)
    end_station_ids = get_station_ids(end_stations)

    dataframe = bbdq.get_trip_statistics_by_station(
        database,
        start_date,
        end_date,
        start_station_ids=start_station_ids,
        end_station_ids=end_station_ids,
        is_include_ebikes=use_ebikes,
        is_include_classic_bikes=use_classic_bikes,
        stats_by_station_at=trips_start_or_end,
    )

    display_name_map = {
        "avg_tripduration": "Average trip duration (minutes)",
        "num_trips": "Total number of trips",
    }

    dataframe = dataframe.rename(columns=display_name_map)

    title = f"Trip Counts by {trips_start_or_end.title()} Station".title()
    label = "Total trips"
    metric_label = "Total number of trips"
    if metric == AVG_DURATION_METRIC_LABEL:
        title = f"Average Duration of Trips {trips_start_or_end.title()}ing at Station"
        label = "Average trip duration<br>in minutes"
        metric_label = "Average trip duration (minutes)"

    fig = px.scatter_map(
        dataframe,
        lat="latitude",
        lon="longitude",
        color=metric_label,
        color_continuous_scale=px.colors.sequential.Jet,
        hover_name="station_name",
        hover_data=display_name_map.values(),
    )
    fig.update_layout(
        title=dict(text=title),
        coloraxis_colorbar_title_text=label,
    )
    fig.update_traces(
        marker=dict(
            size=12,
        )
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
