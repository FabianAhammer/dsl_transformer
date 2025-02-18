from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class TimesheetChange:
    date: str
    sheet_name: str
    dsl_task_time: str
    dsl_nlz_time: str
    jira_task_time: str
    jira_nlz_time: str
    am_start: Optional[datetime.time] = None
    am_end: Optional[datetime.time] = None
    pm_start: Optional[datetime.time] = None
    pm_end: Optional[datetime.time] = None
    is_homeoffice: bool = False
    proposed_am_start: Optional[datetime.time] = None
    proposed_am_end: Optional[datetime.time] = None
    proposed_pm_start: Optional[datetime.time] = None
    proposed_pm_end: Optional[datetime.time] = None


class TimesheetChangesTracker:
    def __init__(self):
        self.changes: List[TimesheetChange] = []

    def add_mismatch(
        self,
        date: str,
        sheet_name: str,
        dsl_task_time: str,
        dsl_nlz_time: str,
        jira_task_time: str,
        jira_nlz_time: str,
    ) -> None:
        """Add a mismatch between DSL and Jira times"""
        change = TimesheetChange(
            date=date,
            sheet_name=sheet_name,
            dsl_task_time=dsl_task_time,
            dsl_nlz_time=dsl_nlz_time,
            jira_task_time=jira_task_time,
            jira_nlz_time=jira_nlz_time,
        )
        self.changes.append(change)

    def add_unbooked_time(
        self,
        date: str,
        sheet_name: str,
        am_start: Optional[datetime.time],
        am_end: Optional[datetime.time],
        pm_start: Optional[datetime.time] = None,
        pm_end: Optional[datetime.time] = None,
        proposed_am_start: Optional[datetime.time] = None,
        proposed_am_end: Optional[datetime.time] = None,
        proposed_pm_start: Optional[datetime.time] = None,
        proposed_pm_end: Optional[datetime.time] = None,
        is_homeoffice: bool = False,
    ) -> None:
        """Add unbooked time that needs to be added to DSL"""
        change = TimesheetChange(
            date=date,
            sheet_name=sheet_name,
            dsl_task_time="Pause?",
            dsl_nlz_time="00:00:00",
            jira_task_time="",  # Will be calculated from proposed am/pm times
            jira_nlz_time="00:00:00",
            am_start=am_start,
            am_end=am_end,
            pm_start=pm_start,
            pm_end=pm_end,
            proposed_am_start=proposed_am_start,
            proposed_am_end=proposed_am_end,
            proposed_pm_start=proposed_pm_start,
            proposed_pm_end=proposed_pm_end,
            is_homeoffice=is_homeoffice,
        )
        # Calculate total jira time from proposed am/pm times
        total_seconds = 0
        if proposed_am_start and proposed_am_end:
            total_seconds += (
                datetime.combine(datetime.min, proposed_am_end)
                - datetime.combine(datetime.min, proposed_am_start)
            ).total_seconds()
        if proposed_pm_start and proposed_pm_end:
            total_seconds += (
                datetime.combine(datetime.min, proposed_pm_end)
                - datetime.combine(datetime.min, proposed_pm_start)
            ).total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        change.jira_task_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.changes.append(change)

    def has_changes(self) -> bool:
        """Check if any changes were found"""
        return len(self.changes) > 0

    def save_to_csv(self) -> str:
        """Save changes to a CSV file if any exist"""
        if not self.has_changes():
            return ""

        import csv
        from datetime import datetime

        filename = f"timesheet_changes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        headers = [
            "Date",
            "Sheet",
            "DSL Task Time",
            "DSL NLZ Time",
            "Jira Task Time",
            "Jira NLZ Time",
            "Current AM Start",
            "Current AM End",
            "Current PM Start",
            "Current PM End",
            "Proposed AM Start",
            "Proposed AM End",
            "Proposed PM Start",
            "Proposed PM End",
            "Homeoffice",
        ]

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for change in self.changes:
                writer.writerow(
                    [
                        change.date,
                        change.sheet_name,
                        change.dsl_task_time,
                        change.dsl_nlz_time,
                        change.jira_task_time,
                        change.jira_nlz_time,
                        change.am_start.strftime("%H:%M:%S") if change.am_start else "",
                        change.am_end.strftime("%H:%M:%S") if change.am_end else "",
                        change.pm_start.strftime("%H:%M:%S") if change.pm_start else "",
                        change.pm_end.strftime("%H:%M:%S") if change.pm_end else "",
                        change.proposed_am_start.strftime("%H:%M:%S")
                        if change.proposed_am_start
                        else "",
                        change.proposed_am_end.strftime("%H:%M:%S")
                        if change.proposed_am_end
                        else "",
                        change.proposed_pm_start.strftime("%H:%M:%S")
                        if change.proposed_pm_start
                        else "",
                        change.proposed_pm_end.strftime("%H:%M:%S")
                        if change.proposed_pm_end
                        else "",
                        "x" if change.is_homeoffice else "",
                    ]
                )

        return filename
