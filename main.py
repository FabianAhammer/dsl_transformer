import pandas as pd
import logging
from modules.booking_checker import BookingChecker
from modules.excel_changes import ExcelChangesTracker
from modules.util import Util
import datetime as dt
import os

# FILL IN BELLOW
#
#

# API TOKEN FROM TEMPO https://meteoserve.atlassian.net/plugins/servlet/ac/io.tempo.jira/tempo-app#!/configuration/api-integration
BookingChecker.bearer_token = ""
# EXCEL FILE
excel_file: str = ""

#
#
# FILL IN ABOVE


if __name__ == "__main__":
    logger = logging.getLogger()
    for h in logger.handlers:
        logger.removeHandler(h)  # clear all default handlers

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if not os.path.isfile(excel_file):
        if not excel_file:
            logger.error("Specify a file in 'main.py'!")
        else:
            logger.error(f"Cannot find file '{excel_file}', add it to the current dir!")
        exit()

    if not BookingChecker.bearer_token:
        logger.error(
            "Need API token from Jira Tempo: 'https://meteoserve.atlassian.net/plugins/servlet/ac/io.tempo.jira/tempo-app#!/configuration/api-integration'!"
        )
        exit()

    # Load the Excel file
    excel_data = pd.ExcelFile(excel_file)

    # Initialize Excel changes tracker
    excel_changes_tracker = ExcelChangesTracker(excel_file)
    checker = BookingChecker(excel_changes_tracker)

    if not checker.check_request():
        logger.error(
            "Incorrect API token, get it from from Jira Tempo: 'https://meteoserve.atlassian.net/plugins/servlet/ac/io.tempo.jira/tempo-app#!/configuration/api-integration'!"
        )
        exit()
    # Iterate over all sheets except the first
    for sheet_name in excel_data.sheet_names[1:]:
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
        df.columns = [chr(i) for i in range(ord("A"), ord("A") + len(df.columns))]
        month_year: dt.datetime = Util.get_date_for_sheet(
            df
        )  # K1 corresponds to row 0 and column K

        if month_year > dt.datetime.now():
            print(f"Skipping {month_year.strftime('%b')}, not yet reached!")
            break
        # Loop through cells "N8" to "N38" (which is column N, rows 7 to 37 in zero-based indexing)
        for index in range(7, 38):  # N8 corresponds to row 7 (zero-based)
            try:
                booked_time = Util.get_booked_time_for_index(df, index)
                booked_time.total_seconds()
            except Exception:
                booked_time = dt.timedelta(0)

            day = Util.get_day_for_index(df, index)
            if not pd.to_numeric(day, errors="coerce") or pd.isna(day):
                break

            try:
                required_hours = Util.get_required_hours_for_index(df, index)
                required_hours.total_seconds()
            except Exception:
                required_hours = dt.timedelta(0)

            try:
                holiday_amount = Util.get_holiday_amount_for_index(df, index)
                holiday_amount.total_seconds()
            except Exception:
                holiday_amount = dt.timedelta(0)

            if pd.isna(required_hours):
                break

            if pd.isna(holiday_amount):
                holiday_amount = None

            checker.check_line(
                day=day,
                month_year=month_year,
                required_hours=required_hours,
                holiday_amount=holiday_amount,
                booked_time_dsl=booked_time,
                sheet_name=sheet_name,
                logger=logger,
                index=index,
            )

    # Save changes to Excel if any were found
    if excel_changes_tracker.has_changes():
        excel_file = excel_changes_tracker.save_to_excel()
        logger.info(f"Changes have been saved to {excel_file}")
    else:
        logger.info("No changes were found in the timesheet")
