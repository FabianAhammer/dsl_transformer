import logging
from datetime import datetime, timedelta
import pandas
import requests
from modules.util import Util


class BookingChecker:
    # Read the first sheet for common values
    bearer_token: str = None

    # Initialize API URL and headers
    url = "https://api.tempo.io/4/worklogs/search"

    def __init__(self, excel_changes_tracker):
        self.excel_changes_tracker = excel_changes_tracker  # For Excel output

    def check_request(self) -> bool:
        data = {
            "from": datetime.now().strftime("%Y-%m-%d"),
            "to": datetime.now().strftime("%Y-%m-%d"),
            "limit": 1,
        }
        response = requests.post(
            self.url,
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json",
            },
            json=data,
        )
        if response.status_code != 200:
            return False
        return True

    def check_line(
        self,
        booked_time_dsl: str | timedelta,
        day: int,
        month_year: datetime,
        required_hours: timedelta,
        holiday_amount: None | timedelta,
        sheet_name: str,
        logger: logging.Logger,
        index: int,
    ) -> bool:
        formatted_date = Util.generate_parsed_date_as_format_str(int(day), month_year)

        data = {"from": formatted_date, "to": formatted_date, "limit": 50}
        if holiday_amount is None:
            holiday_amount = timedelta(seconds=0)

        # Send the POST request
        response = requests.post(
            self.url,
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json",
            },
            json=data,
        )
        response_json = response.json()

        # Extract and sum the worklog times
        seconds_list = [
            item["timeSpentSeconds"] for item in response_json.get("results", [])
        ]
        total_real_task_seconds = sum(seconds_list)

        grouped_nlz_seconds = sum(
            [
                item["timeSpentSeconds"]
                for item in response_json.get("results", [])
                if item["issue"]["self"]
                == "https://meteoserve.atlassian.net/rest/api/2/issue/16804"
            ]
            or [0]
        )

        # Remove not prod time from the total time
        total_real_task_seconds -= grouped_nlz_seconds

        # Format the total hours as HH:MM:SS
        (hours_only, minutes, seconds) = Util.get_round_up_time(total_real_task_seconds)

        formatted_time_real_tasks_api = f"{hours_only:02}:{minutes:02}:{seconds:02}"

        (hours_only, minutes, seconds) = Util.get_round_up_time(grouped_nlz_seconds)
        formatted_time_nlz_api = f"{hours_only:02}:{minutes:02}:{seconds:02}"

        formatted_time_real_tasks_api_str = datetime.strptime(
            formatted_time_real_tasks_api, "%H:%M:%S"
        ).strftime("%H:%M:%S")

        formatted_nlz_time_api_str = datetime.strptime(
            formatted_time_nlz_api, "%H:%M:%S"
        ).strftime("%H:%M:%S")

        formatted_holiday_dsl = (
            datetime.strptime(holiday_amount, "%H:%M:%S").strftime("%H:%M:%S")
            if type(holiday_amount) is str
            else Util.strfdelta(holiday_amount, "%H:%M:%S")
        )

        # If the time is in a pause on dsl, it means we have may not booked it -> we need to book time
        # We have to determine if its Holiday first though
        # For that we need to group "nlz" from API which is the timeSpentSeconds but only for those items with the ["ISSUE"]["self"] == 'https://meteoserve.atlassian.net/rest/api/2/issue/16804'
        # If the total time is less than the required hours, we need to book the difference
        if booked_time_dsl == "Pause?":
            # check if it the holiday amount is not None, if it is, we need to book the difference
            if holiday_amount.total_seconds() == 0:
                # Check if we actually have a difference in required hours and booked hours in jira
                if abs(total_real_task_seconds - required_hours.total_seconds()) > 5:
                    # we only need to book if we have something in jira, otherwise skip
                    if total_real_task_seconds > 0:
                        logger.error(
                            f"Found unbooked Time in DSL Sheet '{sheet_name}' - {formatted_date}, calculating date"
                        )
                        # find the earliest timedelta
                        # json["results"]["startTime"]: "09:00:00"
                        earliest_time = min(
                            [
                                datetime.strptime(item["startTime"], "%H:%M:%S").time()
                                for item in response_json["results"]
                            ]
                        )

                        logger.error("Earliest time found: " + str(earliest_time))
                        logger.error(f"Jira Tasks:{formatted_time_real_tasks_api_str}")

                        # Check if we need a break (6 hours or more)
                        needs_break = (
                            total_real_task_seconds >= 21600
                        )  # 6 hours in seconds

                        if needs_break:
                            # Calculate time available until 12:00
                            seconds_to_12 = (
                                timedelta(hours=12).total_seconds()
                                - timedelta(
                                    hours=earliest_time.hour,
                                    minutes=earliest_time.minute,
                                    seconds=earliest_time.second,
                                ).seconds
                            )

                            # Split the time with a break
                            start_am = earliest_time
                            end_am = datetime.strptime("12:00:00", "%H:%M:%S").time()
                            start_pm = datetime.strptime("12:30:00", "%H:%M:%S").time()
                            end_pm = self.add_seconds_to_time(
                                start_pm, total_real_task_seconds - seconds_to_12
                            )
                            logger.error(
                                f"Need to book {start_am.strftime('%H:%M:%S')} - {end_am.strftime('%H:%M:%S')}"
                            )
                            logger.error(
                                f"and then {start_pm.strftime('%H:%M:%S')} - {end_pm.strftime('%H:%M:%S')}"
                            )

                            # Check if any worklog has homeoffice attribute
                            is_homeoffice = any(
                                any(
                                    attr.get("key") == "_TestBox_"
                                    and attr.get("value") == "JA"
                                    for attr in item.get("attributes", {}).get(
                                        "values", []
                                    )
                                )
                                for item in response_json.get("results", [])
                            )

                            # Add to Excel tracker with break
                            self.excel_changes_tracker.add_change(
                                sheet_name=sheet_name,
                                row=index,
                                proposed_am_start=start_am,
                                proposed_am_end=end_am,
                                proposed_pm_start=start_pm,
                                proposed_pm_end=end_pm,
                                is_homeoffice=is_homeoffice,
                                nlz_time=formatted_nlz_time_api_str
                                if grouped_nlz_seconds > 0
                                else None,
                            )
                        else:
                            # No break needed - book all time starting from earliest_time
                            start_am = earliest_time
                            end_am = self.add_seconds_to_time(
                                earliest_time, total_real_task_seconds
                            )
                            logger.error(
                                f"Need to book {start_am.strftime('%H:%M:%S')} - {end_am.strftime('%H:%M:%S')}"
                            )

                            # Check if any worklog has homeoffice attribute
                            is_homeoffice = any(
                                any(
                                    attr.get("key") == "_TestBox_"
                                    and attr.get("value") == "JA"
                                    for attr in item.get("attributes", {}).get(
                                        "values", []
                                    )
                                )
                                for item in response_json.get("results", [])
                            )

                            # Add to Excel tracker without break
                            self.excel_changes_tracker.add_change(
                                sheet_name=sheet_name,
                                row=index,
                                proposed_am_start=start_am,
                                proposed_am_end=end_am,
                                is_homeoffice=is_homeoffice,
                                nlz_time=formatted_nlz_time_api_str
                                if grouped_nlz_seconds > 0
                                else None,
                            )

                        return True

            else:
                # Check if the difference is more than 5 seconds, if it is, we need to book the difference
                if abs(grouped_nlz_seconds - holiday_amount.total_seconds()) > 5:
                    logger.error(
                        f"Inconsistent booking found in Sheet '{sheet_name}' - {formatted_date}"
                    )
                    logger.error(f"DSL NLZ:   {formatted_holiday_dsl}")
                    logger.error(f"Jira NLZ:  {formatted_nlz_time_api_str}")

                    # Check if any worklog has homeoffice attribute
                    is_homeoffice = any(
                        any(
                            attr.get("key") == "_TestBox_" and attr.get("value") == "JA"
                            for attr in item.get("attributes", {}).get("values", [])
                        )
                        for item in response_json.get("results", [])
                    )

                    # Add to Excel tracker
                    self.excel_changes_tracker.add_change(
                        sheet_name=sheet_name,
                        row=index,
                        is_homeoffice=is_homeoffice,
                        nlz_time=formatted_nlz_time_api_str
                        if grouped_nlz_seconds > 0
                        else None,
                    )
                    return False

        # check if the booked is the same in both jira and dsl, otherwise advise
        # also check if there is booked nlz, as this is not real time, and we need to check if
        # the booked time is less than the required time
        else:
            formatted_task_dsl = (
                datetime.strptime(booked_time_dsl, "%H:%M:%S").strftime("%H:%M:%S")
                if type(booked_time_dsl) is str
                else Util.strfdelta(booked_time_dsl, "%H:%M:%S")
            )
            if formatted_task_dsl != formatted_time_real_tasks_api_str:
                logger.error(
                    f"Inconsistent booking found in Sheet '{sheet_name}' - {formatted_date}"
                )
                logger.error(f"DSL Task:  {formatted_task_dsl}")
                logger.error(f"DSL NLZ:   {formatted_holiday_dsl}")
                logger.error(f"Jira Tasks:{formatted_time_real_tasks_api_str}")
                logger.error(f"Jira NLZ:  {formatted_nlz_time_api_str}")

                # Check if any worklog has homeoffice attribute
                is_homeoffice = any(
                    any(
                        attr.get("key") == "_TestBox_" and attr.get("value") == "JA"
                        for attr in item.get("attributes", {}).get("values", [])
                    )
                    for item in response_json.get("results", [])
                )

                # Calculate proposed times based on Jira entries
                earliest_time = min(
                    [
                        datetime.strptime(item["startTime"], "%H:%M:%S").time()
                        for item in response_json["results"]
                    ]
                )

                # Check if we need a break (6 hours or more)
                needs_break = total_real_task_seconds >= 21600  # 6 hours in seconds

                if needs_break:
                    # Calculate time available until 12:00
                    seconds_to_12 = (
                        timedelta(hours=12).total_seconds()
                        - timedelta(
                            hours=earliest_time.hour,
                            minutes=earliest_time.minute,
                            seconds=earliest_time.second,
                        ).seconds
                    )

                    # Split the time with a break
                    proposed_am_start = earliest_time
                    proposed_am_end = datetime.strptime("12:00:00", "%H:%M:%S").time()
                    proposed_pm_start = datetime.strptime("12:30:00", "%H:%M:%S").time()
                    proposed_pm_end = self.add_seconds_to_time(
                        proposed_pm_start, total_real_task_seconds - seconds_to_12
                    )
                else:
                    # No break needed - book all time starting from earliest_time
                    proposed_am_start = earliest_time
                    proposed_am_end = self.add_seconds_to_time(
                        earliest_time, total_real_task_seconds
                    )
                    proposed_pm_start = None
                    proposed_pm_end = None

                # Add to Excel tracker
                self.excel_changes_tracker.add_change(
                    sheet_name=sheet_name,
                    row=index,
                    proposed_am_start=proposed_am_start,
                    proposed_am_end=proposed_am_end,
                    proposed_pm_start=proposed_pm_start,
                    proposed_pm_end=proposed_pm_end,
                    is_homeoffice=is_homeoffice,
                    nlz_time=formatted_nlz_time_api_str
                    if grouped_nlz_seconds > 0
                    else None,
                )
        return False

    def add_seconds_to_time(self, time: datetime.time, seconds: float) -> datetime.time:
        """
        Add seconds to a datetime.time object.
        """
        return (
            datetime.combine(datetime.today(), time) + timedelta(seconds=seconds)
        ).time()
