from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd


@dataclass
class ExcelChange:
    sheet_name: str
    row: int
    proposed_am_start: Optional[datetime.time] = None
    proposed_am_end: Optional[datetime.time] = None
    proposed_pm_start: Optional[datetime.time] = None
    proposed_pm_end: Optional[datetime.time] = None
    is_homeoffice: bool = False
    nlz_time: Optional[datetime.time] = None  # NLZ time as datetime.time


class ExcelChangesTracker:
    def __init__(self, excel_file_path: str):
        """Initialize with the path to the original Excel file"""
        self.excel_file_path = excel_file_path
        self.changes: Dict[str, List[ExcelChange]] = {}  # sheet_name -> list of changes
        self.excel_data = pd.ExcelFile(excel_file_path)

    def add_change(
        self,
        sheet_name: str,
        row: int,
        proposed_am_start: Optional[datetime.time] = None,
        proposed_am_end: Optional[datetime.time] = None,
        proposed_pm_start: Optional[datetime.time] = None,
        proposed_pm_end: Optional[datetime.time] = None,
        is_homeoffice: bool = False,
        nlz_time: Optional[str] = None,
    ) -> None:
        """Add a change for a specific sheet and row"""
        if sheet_name not in self.changes:
            self.changes[sheet_name] = []

        # Parse NLZ time if provided and in correct format
        parsed_nlz_time = None
        if nlz_time:
            try:
                # Check if the string matches HH:MM:SS format
                if len(nlz_time.split(":")) == 3:
                    parsed_nlz_time = datetime.strptime(nlz_time, "%H:%M:%S").time()
            except ValueError:
                # If parsing fails, leave it as None
                pass

        change = ExcelChange(
            sheet_name=sheet_name,
            row=row,
            proposed_am_start=proposed_am_start,
            proposed_am_end=proposed_am_end,
            proposed_pm_start=proposed_pm_start,
            proposed_pm_end=proposed_pm_end,
            is_homeoffice=is_homeoffice,
            nlz_time=parsed_nlz_time,
        )
        self.changes[sheet_name].append(change)

    def has_changes(self) -> bool:
        """Check if any changes were found"""
        return bool(self.changes)

    def save_to_excel(self) -> str:
        """Save changes to a new Excel file if any exist"""
        if not self.has_changes():
            return ""

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"timesheet_changes_{timestamp}.xlsx"

        # Create Excel writer
        with pd.ExcelWriter(output_file) as writer:
            # Only create sheets that have changes
            for sheet_name, changes in self.changes.items():
                # Read original sheet to get the structure
                orig_df = pd.read_excel(
                    self.excel_file_path, sheet_name=sheet_name, header=None
                )

                # Create empty dataframe with same structure as original
                df = pd.DataFrame(index=range(50), columns=range(orig_df.shape[1]))

                # Copy header rows (5, 6, 7 are indices 4, 5, 6 in zero-based indexing)
                for row in [4, 5, 6]:
                    df.iloc[row] = orig_df.iloc[row]

                # Apply changes and copy original day information
                for change in changes:
                    # Copy columns A and B from original (0 and 1 in zero-based indexing)
                    df.iloc[change.row, 0] = orig_df.iloc[change.row, 0]  # Column A
                    df.iloc[change.row, 1] = orig_df.iloc[change.row, 1]  # Column B
                    date_str_format = "%H:%M"
                    # Add proposed times
                    if change.proposed_am_start:
                        df.iloc[change.row, 2] = change.proposed_am_start.strftime(
                            date_str_format
                        )  # Column C
                    if change.proposed_am_end:
                        df.iloc[change.row, 3] = change.proposed_am_end.strftime(
                            date_str_format
                        )  # Column D
                    if change.proposed_pm_start:
                        df.iloc[change.row, 4] = change.proposed_pm_start.strftime(
                            date_str_format
                        )  # Column E
                    if change.proposed_pm_end:
                        df.iloc[change.row, 5] = change.proposed_pm_end.strftime(
                            date_str_format
                        )  # Column F
                    if change.is_homeoffice:
                        df.iloc[change.row, 8] = "x"  # Column I
                    if change.nlz_time:
                        df.iloc[change.row, 11] = change.nlz_time.strftime(
                            date_str_format
                        )  # Column L

                # Write the sheet to the new file
                df.to_excel(writer, sheet_name=sheet_name, header=False, index=False)

            # If no sheets were written (shouldn't happen due to has_changes check)
            if not self.changes:
                # Create an empty sheet to satisfy Excel requirements
                pd.DataFrame().to_excel(writer, sheet_name="No Changes", index=False)

        return output_file
