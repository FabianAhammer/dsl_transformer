from string import Template
import pandas as pd
import datetime as dt


class Util:
    @staticmethod
    def write_am_start_timedelta_str(
        df: pd.DataFrame, index: int, value: dt.datetime
    ) -> None:
        """Writes to the Start Time Before Pause"""
        # df.loc[index, "C"] = value
        return

    @staticmethod
    def write_am_end_timedelta_str(
        df: pd.DataFrame, index: int, value: dt.datetime
    ) -> None:
        """Writes to the End Time Before Pause"""
        # df.loc[index, "D"] = value
        return

    @staticmethod
    def write_pm_start_timedelta_str(
        df: pd.DataFrame, index: int, value: dt.datetime
    ) -> None:
        """Writes to the Start Time After Pause"""
        # df.loc[index, "E"] = value
        return

    @staticmethod
    def write_pm_end_timedelta_str(
        df: pd.DataFrame, index: int, value: dt.datetime
    ) -> None:
        """Writes to the End Time After Pause"""
        # df.loc[index, "F"] = value
        return

    @staticmethod
    def get_booked_time_for_index(df: pd.DataFrame, index: int):
        """
        Get the booked time for a specific index in the DataFrame.
        """
        return df.loc[index, "H"]

    @staticmethod
    def get_day_for_index(df: pd.DataFrame, index: int):
        """
        Get the day for a specific index in the DataFrame.
        """
        return df.loc[index, "B"]

    @staticmethod
    def get_date_for_sheet(df: pd.DataFrame):
        """
        Get the date for a specific index in the DataFrame.
        """
        return df.loc[0, "K"]

    @staticmethod
    def get_holiday_amount_for_index(df: pd.DataFrame, index: int):
        """
        Get the date for a specific index in the DataFrame.
        """
        return df.loc[index, "L"]

    @staticmethod
    def get_required_hours_for_index(df: pd.DataFrame, index: int):
        """
        Get the required hours for a specific index in the DataFrame.
        """
        return df.loc[index, "G"]

    @staticmethod
    def generate_parsed_date_as_format_str(day: int, month_year: dt.datetime) -> str:
        """
        Generate a parsed date as a formatted string: "YYYY-MM-DD".
        """
        new_date = month_year.replace(day=day)
        return new_date.strftime("%Y-%m-%d")

    @staticmethod
    def get_round_up_time(total_seconds: int) -> tuple:
        """
        Get the rounded up time in hours, minutes, and seconds.
        Automatically rounds up the minutes if the seconds are 59.
        """
        hours_only = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if seconds == 59:
            minutes += 1
            seconds = 0
        return (hours_only, minutes, seconds)

    @staticmethod
    def strfdelta(tdelta, fmt):
        d = {"D": tdelta.days}
        hours, rem = divmod(tdelta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        if seconds == 59:
            minutes += 1
            seconds = 0
        d["H"] = "{:02d}".format(hours)
        d["M"] = "{:02d}".format(minutes)
        d["S"] = "{:02d}".format(seconds)
        t = DeltaTemplate(fmt)
        return t.substitute(**d)


class DeltaTemplate(Template):
    delimiter = "%"
