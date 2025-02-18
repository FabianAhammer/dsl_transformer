# Timesheet Validation Tool

This tool helps validate timesheet entries by cross-checking them with Jira data. It ensures that the time booked in the timesheet matches the time logged in Jira.

## Goals

1. [x] Current functionality: Log to console when there are mismatches between timesheet and Jira
2. [x] New functionality: Create a new CSV file with changes when mismatches are found
   - [x] Do nothing if there are no mismatches
   - [x] Generate a CSV file with the changes if mismatches are found
3. [x] Enhanced functionality:
   - [x] For mismatches, calculate and propose new time entries based on Jira data
   - [x] Track homeoffice status from Jira work attributes
   - [x] Include both current and proposed time entries in the CSV output
4. [x] Excel-compatible output format:
   - [x] Generate output in same format as input Excel sheet
   - [x] Use same sheet names as input file
   - [x] Place proposed times in correct columns:
     - Column C: Proposed AM Start
     - Column D: Proposed AM End
     - Column E: Proposed PM Start
     - Column F: Proposed PM End
     - Column I: Homeoffice status
   - [x] Use same row numbers as input file for changes
5. [x] Additional data from original file:
   - [x] For changed rows:
     - [x] Copy columns A and B (day information)
     - [x] Add NLZ time to column L if calculated
   - [x] Copy header information:
     - [x] Copy rows 5, 6, and 7 from original file

## Implementation Progress

### Current Implementation
- Reads Excel timesheet file
- Connects to Jira API to get worklog data
- Validates timesheet entries against Jira data
- Logs inconsistencies to console
- Generates an Excel file with proposed changes in the original format

### Output Format

The generated Excel file contains:

1. Header information:
   - Rows 5, 6, and 7 from original file

2. For each changed row:
   - Columns A and B: Original day information
   - Column C: Proposed AM Start time
   - Column D: Proposed AM End time
   - Column E: Proposed PM Start time
   - Column F: Proposed PM End time
   - Column I: Homeoffice status (marked with "x")
   - Column L: NLZ time (if calculated)

Key features:
- Only sheets with changes are included
- Changes are placed in the exact same rows as in the input file
- Original header information is preserved
- Day information (columns A, B) is copied for changed rows
- Each sheet maintains the original Excel format

## Usage

```bash
python tracking.py
```

The script will:
1. Read the timesheet Excel file
2. Compare entries with Jira data
3. If mismatches are found:
   - Create a CSV file with the changes (new feature)
   - Log details to console
4. If no mismatches:
   - Exit silently