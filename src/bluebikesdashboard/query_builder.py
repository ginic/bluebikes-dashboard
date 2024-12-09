from datetime import datetime, date
import logging
import os
import sqlite3

import pandas as pd

logger = logging.getLogger(__name__)


def run_sqlite_query_with_pandas(database, base_query, params):
    logger.debug("Database %s exists: %s", database, os.path.exists(database))
    logger.debug("Querying database %s", database)
    with sqlite3.connect(database) as conn:
        dataframe = pd.read_sql_query(base_query, conn, params=params)
        logger.debug("Query completed")
        return dataframe


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

    if start_date is None:
        start_date = date(2011, 1, 1).isoformat()
    if end_date is None:
        end_date = datetime.today().isoformat()

    logger.debug("Query range %s to %s", start_date, end_date)

    restriction = "AND TRUE "
    if is_include_ebikes and not is_include_classic_bikes:
        restriction += " AND rideable_type = 'electric_bike'"
    elif is_include_classic_bikes and not is_include_ebikes:
        restriction += "AND rideable_type = 'classic_bike'"
    logger.debug("Further query restriction: '%s'", restriction)
    params = {
        "start_date": start_date,
        "end_date": end_date,
    }
    base_query = " ".join([base_query, restriction, "GROUP BY 1, 2 ORDER BY 1;"])

    logger.debug("Querying trips grouped by month with params: %s", params)
    dataframe = run_sqlite_query_with_pandas(database, base_query, params)
    logger.debug("Data snippet: %s", dataframe)
    # TODO Fill missing months with zeros
    return dataframe
