from datetime import datetime, date
import logging
import os
import sqlite3

import pandas as pd

logger = logging.getLogger(__name__)


def run_sqlite_query_with_pandas(database, base_query, params=None):
    logger.debug("Database %s exists: %s", database, os.path.exists(database))
    logger.debug("Querying database %s", database)
    with sqlite3.connect(database) as conn:
        dataframe = pd.read_sql_query(base_query, conn, params=params)
        logger.debug("Query completed")
        return dataframe


def validate_start_end_dates(start_date=None, end_date=None):
    if start_date is None:
        start_date = date(2015, 1, 1).isoformat()
    if end_date is None:
        end_date = datetime.today().isoformat()

    logger.debug("Query range %s to %s", start_date, end_date)

    return start_date, end_date


def get_rideable_type_restriction(is_include_ebikes=True, is_include_classic_bikes=True):
    restriction = "AND TRUE"
    if is_include_ebikes and not is_include_classic_bikes:
        restriction = "AND rideable_type = 'electric_bike'"
    elif is_include_classic_bikes and not is_include_ebikes:
        restriction = "AND rideable_type = 'classic_bike'"
    return restriction


def query_stations(database):
    q = "SELECT id, station_name FROM normalized_stations;"
    logger.debug("Querying for station list")
    stations = run_sqlite_query_with_pandas(database, q)
    logger.debug("%s stations found", len(stations))
    return stations


def query_trips_by_date_range(
    database, start_date=None, end_date=None, is_include_ebikes=True, is_include_classic_bikes=True
):
    base_query = (
        "SELECT "
        "STRFTIME('%Y-%m', started_at) AS month, "
        "rideable_type AS rideable_type, "
        "count(id) AS num_trips "
        "FROM normalized_bluebikes "
        "WHERE (date(started_at) >= date(:start_date) AND date(started_at) < date(:end_date))"
    )

    start_date, end_date = validate_start_end_dates(start_date, end_date)

    restriction = get_rideable_type_restriction(is_include_ebikes, is_include_classic_bikes)
    logger.debug("Further query restriction: '%s'", restriction)
    params = {
        "start_date": start_date,
        "end_date": end_date,
    }
    full_query = " ".join([base_query, restriction, "GROUP BY 1, 2 ORDER BY 1;"])

    logger.debug("Querying trips grouped by month with params: %s", params)
    dataframe = run_sqlite_query_with_pandas(database, full_query, params)
    logger.debug("Data snippet: %s", dataframe)
    # TODO Fill missing months with zeros
    return dataframe


def get_trip_statistics_by_station(
    database,
    start_date,
    end_date,
    start_station=None,
    end_station=None,
    is_stats_by_end_stations=False,
    is_include_ebikes=True,
    is_include_classic_bikes=True,
):
    start_date, end_date = validate_start_end_dates(start_date, end_date)
    params = {"start_date": start_date, "end_date": end_date}
    station_id = "start_id"
    station_name = "start_station_name"
    lat = "start_lat"
    lng = "start_lng"
    if is_stats_by_end_stations:
        logger.debug("Querying with stats by end station")
        station_id = "end_id"
        station_name = "end_station_name"
        lat = "start_lat"
        lng = "start_lng"
    base_query = f"SELECT {station_id} AS station_id, {station_name} AS station_name, {lat} AS latitude, {lng} AS longitude, AVG(tripduration)/60 AS avg_tripduration, COUNT(id) as num_trips FROM normalized_bluebikes"

    restriction = "WHERE (date(started_at) >= date(:start_date) AND date(started_at) < date(:end_date))"
    restriction = " ".join([restriction, get_rideable_type_restriction(is_include_ebikes, is_include_classic_bikes)])
    # TODO also allow selecting stations
    logger.debug("Further query restriction: '%s'", restriction)
    groupby = "GROUP BY 1, 2, 3, 4;"
    full_query = " ".join([base_query, restriction, groupby])
    logger.debug("Querying trip statistics grouped by station with params: %s", params)
    dataframe = run_sqlite_query_with_pandas(database, full_query, params)
    logger.debug("Data snippet: %s", dataframe)
    return dataframe
