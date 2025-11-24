import pandas as pd
import numpy as np
import pytest 

from datetime import datetime, date, time, timedelta

# File path
#timesheet_file_path = r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Timesheet detail 1 Nov 2023 to 30 June 2025.xlsx"
timesheet_file_path  = r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Processed_Timesheet_withRoster.csv"

emplids_mapping = pd.read_excel(r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Employee IDs.xlsx", sheet_name='EMPLIDS')

payroll_data = r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Payroll_Output.xlsx"


# Ordinary daily and weekly hours and overtime cutoffs
Max_Ord_Hrs_Day = 10
# Define Max Ordinary Hours per Day
#Max_Ord_Hrs_Day = pd.Timedelta(hours=10)
Max_Ord_Hrs = 76
First_2_Hrs_OT_Cutoff = 78
Daily_Ordinary_Hours = 7.6


# Load and clean timesheet data from CSV
def load_and_clean_timesheet(file_path):
    df = pd.read_csv(file_path)
    df = df.dropna(axis=1, how='all')  # Remove empty columns

    # Convert relevant columns to appropriate types
    df['Timesheet ID'] = pd.to_numeric(df['Timesheet ID'], errors='coerce').astype('Int64')
    df['Employee ID Consolidated'] = pd.to_numeric(df['Employee ID Consolidated'], errors='coerce').astype('Int64')

    datetime_cols = [
        'Timesheet Start Time',
        'Timesheet End Time',
        'Shift Start Time',
        'Shift End Time'
    ]
    for col in datetime_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # Extract date and time components
    df['TS_Start_Date'] = df['Timesheet Start Time'].dt.date
    df['TS_End_Date'] = df['Timesheet End Time'].dt.date
    df['TS_TimeOnly_Start'] = df['Timesheet Start Time'].dt.time
    df['TS_TimeOnly_End'] = df['Timesheet End Time'].dt.time

    return df


# Calculate total hours worked
def calculate_time_difference_in_hours(date_series, time_series_start, time_series_end):
    start_dt = pd.to_datetime(date_series.astype(str) + ' ' + time_series_start.astype(str), errors='coerce')
    end_dt = pd.to_datetime(date_series.astype(str) + ' ' + time_series_end.astype(str), errors='coerce')
    end_dt = end_dt.where(end_dt >= start_dt, end_dt + pd.Timedelta(days=1))
    return (end_dt - start_dt).dt.total_seconds() / 3600

# Generic shift hour calculator
def calculate_shift_hours(start_time, end_time, shift_start, shift_end):
    start_dt = datetime.combine(datetime.today(), start_time)
    end_dt = datetime.combine(datetime.today(), end_time)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)  # handle overnight

    # Shift window (may cross midnight)
    if shift_end <= shift_start:
        shift_end_dt = datetime.combine(start_dt.date(), shift_end) + timedelta(days=1)
    else:
        shift_end_dt = datetime.combine(start_dt.date(), shift_end)
    shift_start_dt = datetime.combine(start_dt.date(), shift_start)

    # Calculate overlap in minutes
    latest_start = max(start_dt, shift_start_dt)
    earliest_end = min(end_dt, shift_end_dt)
    overlap = (earliest_end - latest_start).total_seconds() / 3600  # hours

    return max(0, round(overlap, 2))  # keep to 2 decimals, e.g. 4.5



# Load data
timesheet_df = load_and_clean_timesheet(timesheet_file_path)

emplids_mapping['Team member'] = emplids_mapping['Team member'].astype(str)


timesheet_df.to_csv('line103.csv')

print(timesheet_df.columns)

# Merge to get Employee ID Consolidated
timesheet_df = timesheet_df.merge(
    emplids_mapping[['Team member', 'Employee ID Consolidated']],
    on=['Employee ID Consolidated', 'Team member'],
    how='left'
)


print('columns after merge')
print(timesheet_df.columns)

# timesheet_df['Employee ID Consolidated'] = (
#     timesheet_df['Employee ID Consolidated']
#     .astype(str)
#     .str.replace(r"\.0$", "", regex=True)  # strip only a trailing .0
#     .str.strip()
# )

# Drop rows where Team member is 'Anthony Knight' as not in consent list
timesheet_df = timesheet_df[timesheet_df['Team member'] != 'Anthony Knight']

# Drop rows where Team member is 'Grahame Corbett' as Salary not shift worker
timesheet_df = timesheet_df[timesheet_df['Team member'] != 'Grahame Corbett']


# (Optional) Reset the index if you want a clean index after dropping
timesheet_df = timesheet_df.reset_index(drop=True)

# Sort by employee and start datetime

timesheet_df = timesheet_df.sort_values(by=['Employee ID Consolidated', 'Timesheet Start Time']).reset_index(drop=True)






# # Create full datetime columns using combine
# timesheet_df['Start_dt'] = timesheet_df.apply(
#     lambda row: pd.Timestamp.combine(row['TS_Start_Date'], row['TS_TimeOnly_Start']), axis=1
# )
# timesheet_df['End_dt'] = timesheet_df.apply(
#     lambda row: pd.Timestamp.combine(row['TS_End_Date'], row['TS_TimeOnly_End']), axis=1
# )


# # Identify next shift start and end times per employee
# timesheet_df['Next_Start_dt'] = (
#     timesheet_df.groupby('Employee ID Consolidated')['Timesheet Start Time'].shift(-1)
# )

# timesheet_df['Next_End_dt'] = (
#     timesheet_df.groupby('Employee ID Consolidated')['End_dt'].shift(-1)
# )

# # 0. Column names
# EMP_COL = 'Employee ID Consolidated'
# START   = 'Timesheet Start Time'
# END     = 'Timesheet End Time'

# # 1. Ensure datetimes
# timesheet_df[START] = pd.to_datetime(timesheet_df[START])
# timesheet_df[END]   = pd.to_datetime(timesheet_df[END])

# # 2. Remove exact dupes early
# timesheet_df = timesheet_df.drop_duplicates(
#     subset=[EMP_COL, START]
# ).sort_values([EMP_COL, START]).reset_index(drop=True)

# # 3. Create start/end_dt
# timesheet_df['Start_dt'] = timesheet_df[START]
# timesheet_df['End_dt']   = timesheet_df[END]

# # 4. Next/Prev shifts per employee
# grp = timesheet_df.groupby(EMP_COL)
# timesheet_df['Next_Start_dt'] = grp[START].shift(-1)
# timesheet_df['Next_End_dt']   = grp[END].shift(-1)
# timesheet_df['Prev_End_dt']   = grp[END].shift(1)

# # 5. Shift durations
# timesheet_df['Shift_Duration_Hours'] = (
#     (timesheet_df['End_dt'] - timesheet_df['Start_dt']).dt.total_seconds() / 3600
# )
# timesheet_df['Next_Shift_Duration_Hours'] = (
#     (timesheet_df['Next_End_dt'] - timesheet_df['Next_Start_dt']).dt.total_seconds() / 3600
# )

# # 6. Gaps (clip to 0 to avoid negatives)
# timesheet_df['Gap_to_Next_Shift_Hours'] = (
#     (timesheet_df['Next_Start_dt'] - timesheet_df['End_dt']).dt.total_seconds() / 3600.0
# ).clip(lower=0)



# G'Day Mate!


# === Start of Shift Gap and Duration Calculations ===

def calculate_shift_gaps(timesheet_df, emp_col='Employee ID Consolidated',
                         start_col='Timesheet Start Time', end_col='Timesheet End Time'):
    """
    Calculates next/previous shift times, shift durations, and gaps between shifts.

    Args:
        timesheet_df (pd.DataFrame): Shift data.
        emp_col (str): Employee identifier column.
        start_col (str): Shift start datetime column.
        end_col (str): Shift end datetime column.

    Returns:
        pd.DataFrame: Original dataframe with additional columns:
            - Start_dt, End_dt
            - Next_Start_dt, Next_End_dt, Prev_End_dt
            - Shift_Duration_Hours, Next_Shift_Duration_Hours
            - Gap_to_Next_Shift_Hours
    """
    df = timesheet_df.copy()

    # Ensure datetime types
    df[start_col] = pd.to_datetime(df[start_col])
    df[end_col]   = pd.to_datetime(df[end_col])

    # Remove exact duplicates and sort
    df = df.drop_duplicates(subset=[emp_col, start_col]).sort_values([emp_col, start_col]).reset_index(drop=True)

    # Create unified start/end columns
    df['Start_dt'] = df[start_col]
    df['End_dt']   = df[end_col]

    # Next / previous shift per employee
    grp = df.groupby(emp_col)
    df['Next_Start_dt'] = grp[start_col].shift(-1)
    df['Next_End_dt']   = grp[end_col].shift(-1)
    df['Prev_End_dt']   = grp[end_col].shift(1)

    # Shift durations
    df['Shift_Duration_Hours'] = (df['End_dt'] - df['Start_dt']).dt.total_seconds() / 3600
    df['Next_Shift_Duration_Hours'] = (df['Next_End_dt'] - df['Next_Start_dt']).dt.total_seconds() / 3600

    # Gap to next shift (clip negative gaps)
    df['Gap_to_Next_Shift_Hours'] = ((df['Next_Start_dt'] - df['End_dt']).dt.total_seconds() / 3600).clip(lower=0)

    return df

# === End of Shift Gap and Duration Calculations ===

# === Start of Combined Shift Calculations ===
timesheet_df = calculate_shift_gaps(timesheet_df)


# 7. Combined shift flag (allow small tolerances, e.g. <= 0.01h = 36s)
timesheet_df['Combined_Shift'] = np.where(
    timesheet_df['Gap_to_Next_Shift_Hours'] <= 0.01,
    'Y', 'N'
)

# concatenate the values within the row below for the following columns
# Timesheet location	Timesheet area	Timesheet Employee Comment	Comments_Roster
cols_to_concat = ['Timesheet location', 'Timesheet area', 'Timesheet Employee Comment', 'Comments_Roster']
for col in cols_to_concat:
    timesheet_df[col] = np.where(
        timesheet_df['Combined_Shift'] == 'Y',
        '1st part of shift: ' + timesheet_df[col] + '; 2nd part of shift:  ' + timesheet_df[col].shift(-1).fillna(''),
        timesheet_df[col]
    )


#If Combined_Shift is Y then we need to combine the two shifts into one row
timesheet_df['Timesheet End Time'] = np.where(
    (timesheet_df['Combined_Shift'] == 'Y') &
    (timesheet_df['Employee ID Consolidated'] == timesheet_df['Employee ID Consolidated'].shift(-1)),
    timesheet_df['Next_End_dt'],
    timesheet_df['Timesheet End Time']
)

timesheet_df['Roster_End DateTime'] = np.where(
    (timesheet_df['Combined_Shift'] == 'Y') &
    (timesheet_df['Employee ID Consolidated'] == timesheet_df['Employee ID Consolidated'].shift(-1)),
    timesheet_df['Roster_End DateTime'].shift(-1).fillna(timesheet_df['Roster_End DateTime']),
    timesheet_df['Roster_End DateTime']
)

timesheet_df['Shift End Time'] = np.where(
    (timesheet_df['Combined_Shift'] == 'Y') &
    (timesheet_df['Employee ID Consolidated'] == timesheet_df['Employee ID Consolidated'].shift(-1)),
    timesheet_df['Shift End Time'].shift(-1).fillna(timesheet_df['Shift End Time']),
    timesheet_df['Shift End Time']
)

timesheet_df['Timesheet Total Time'] = np.where(
    (timesheet_df['Combined_Shift'] == 'Y') &
    (timesheet_df['Employee ID Consolidated'] == timesheet_df['Employee ID Consolidated'].shift(-1)),
    timesheet_df['Timesheet Total Time'] + timesheet_df['Timesheet Total Time'].shift(-1).fillna(0),
    timesheet_df['Timesheet Total Time']
)

timesheet_df['Shift Total Time'] = np.where(
    (timesheet_df['Combined_Shift'] == 'Y') &
    (timesheet_df['Employee ID Consolidated'] == timesheet_df['Employee ID Consolidated'].shift(-1)),
    timesheet_df['Shift Total Time'] + timesheet_df['Shift Total Time'].shift(-1).fillna(0),
    timesheet_df['Shift Total Time']
)

timesheet_df['Roster_Hours'] = np.where(
    (timesheet_df['Combined_Shift'] == 'Y') &
    (timesheet_df['Employee ID Consolidated'] == timesheet_df['Employee ID Consolidated'].shift(-1)),
    timesheet_df['Roster_Hours'] + timesheet_df['Roster_Hours'].shift(-1).fillna(0),
    timesheet_df['Roster_Hours']
)

timesheet_df['Timesheet ID (Combined Shift)'] = np.where(
    (timesheet_df['Combined_Shift'] == 'Y') &
    (timesheet_df['Employee ID Consolidated'] == timesheet_df['Employee ID Consolidated'].shift(-1)),
    timesheet_df['Timesheet ID'].shift(-1).fillna(0),
    0
)

# Flag second row of a combined shift
timesheet_df['Drop_Row'] = (
    timesheet_df['Combined_Shift'].shift(1) == 'Y'
) & (
    timesheet_df['Employee ID Consolidated'] == timesheet_df['Employee ID Consolidated'].shift(1)
)

# Drop the flagged rows
timesheet_df = timesheet_df[~timesheet_df['Drop_Row']].drop(columns='Drop_Row').reset_index(drop=True)

timesheet_df = calculate_shift_gaps(timesheet_df)


# === End of Combined Shift Calculations ===


# check
timesheet_df.to_csv('line200.csv')


# === Start of Broken Shift and Break Between Work Period Calculations ===


# Check if end and next start are on the same calendar day
timesheet_df['Same_Day'] = (
    #timesheet_df['End_dt'].dt.date == timesheet_df['Next_Start_dt'].dt.date
    timesheet_df['Start_dt'].dt.date == timesheet_df['Next_Start_dt'].dt.date
)

# -------------------------------
# Apply Broken Shift rules
# -------------------------------
timesheet_df['Broken_Shift_Flag'] = np.where(
    (timesheet_df['Same_Day']) &
    (timesheet_df['Roster_Start DateTime'].notnull()) &
    (timesheet_df['Next_Shift_Duration_Hours'] < Daily_Ordinary_Hours),
    'Y',
    'N'
)

# -------------------------------
# Propagate the Broken Shift flag
# -------------------------------
# Tag each broken shift pair as H1 (first half) and H2 (second half).
# Logic:
#   - If current row is 'Y', mark as H1
#   - If the *previous* row is 'Y', mark current row as H2
timesheet_df['Broken_Shift_Tag'] = np.where(
    timesheet_df['Broken_Shift_Flag'] == 'Y',
    'H1',
    np.where(
        timesheet_df['Broken_Shift_Flag'].shift(fill_value='N') == 'Y',
        'H2',
        ''
    )
)
# -------------------------------



timesheet_df['Broken Shift Topup Hours'] = np.where(
    (timesheet_df['Broken_Shift_Tag'].isin(['H1', 'H2'])) & 
    (timesheet_df['Timesheet Total Time'] - 3  < 0),
    3 - timesheet_df['Timesheet Total Time'],
    0
)




timesheet_df.to_csv('line383.csv')


# === End of Broken Shift Calculations ===

# Calculate total timesheet hours for row
timesheet_df['Difference in Hours'] = calculate_time_difference_in_hours(
    timesheet_df['TS_Start_Date'],
    timesheet_df['TS_TimeOnly_Start'],
    timesheet_df['TS_TimeOnly_End']

)







# Calculate night and Day TS Hours


# Step 1: Add `DOTW` (Day of the Week) where Saturday is 1 and Friday is 7
# Step 1: Map days of the week using the desired mapping
day_mapping = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7}  # Monday=1, Sunday=7

# # Create the DOTW column and apply the mapping
timesheet_df['DOTW'] = timesheet_df['Timesheet Start Time'].dt.weekday.map(day_mapping)
# Included Endshift to cover nightshift hours that go into Sat or Sunday
timesheet_df['DOTW_ENDShift'] = timesheet_df['Timesheet End Time'].dt.weekday.map(day_mapping)
# Custom numeric mapping: Saturday = 1, Sunday = 2, ..., Friday = 7
# Add Day of the Week as text (e.g. Monday, Tuesday, etc.)
timesheet_df['Weekday'] = pd.to_datetime(timesheet_df['TS_Start_Date']).dt.day_name()


# Estimated pay date column for joining with Payroll data set. 
# All pay dates are on Wednesday except 
#24/12/2024	and 31/12/2024	which fall on a Tuesday

# Can make these account for Weekend OT and PH once the PH list is complete

PUBLIC_HOLIDAYS = pd.read_excel(r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Public Holidays Victoria.xlsx", sheet_name='PH')

PUBLIC_HOLIDAYS['Date'] = pd.to_datetime(PUBLIC_HOLIDAYS['Date'], errors='coerce').dt.date
timesheet_df['TS_Start_Date'] = pd.to_datetime(timesheet_df['TS_Start_Date'], errors='coerce').dt.date

timesheet_df['Public_Holiday_flag'] = np.where(
    timesheet_df['TS_Start_Date'].isin(PUBLIC_HOLIDAYS['Date']),
    'Y',
    'N'
)




timesheet_df['Saturday_Penality_flag'] = np.where(
    #shifts that start on Sat
    (timesheet_df['DOTW'] == 6) 
     |
    # shifts that end on Sat
    (timesheet_df['DOTW_ENDShift'] == 6)
      & 
    (timesheet_df['Public_Holiday_flag'] =='N'),
    'Y',
    'N'
)

timesheet_df['Sunday_Penality_flag'] = np.where(
    # Shifts that start on Sun
    (timesheet_df['DOTW'] == 7) 
    |
    # shifts that end on Sun
    (timesheet_df['DOTW_ENDShift'] == 7)
    & 
    (timesheet_df['Public_Holiday_flag'] =='N'),
    'Y',
    'N'
)



# === Day, Night, Sat, Sunday and PH allocations ===

# --- Populate set from Public holiday calendar ---
PUBLIC_HOLIDAYS = set(pd.to_datetime(PUBLIC_HOLIDAYS['Date']).dt.date)


# --- helpers ---
def hours_between(a: datetime, b: datetime) -> float:
    return (b - a).total_seconds() / 3600.0

# Used for Public Holiday Hours
def split_by_midnights(start: datetime, end: datetime):
    """
    Yield (isoweekday, part_start, part_end) where each part is within a single calendar date.
    Normalise end if it's <= start by assuming it moves to the next day.
    """
    if end <= start:
        end = end + timedelta(days=1)

    cur_start = start
    cur_dotw = start.isoweekday()  # 1=Mon ... 7=Sun

    while cur_start.date() != end.date():
        next_midnight = datetime.combine(cur_start.date() + timedelta(days=1), time(0, 0))
        yield (cur_dotw, cur_start, next_midnight)
        cur_start = next_midnight
        cur_dotw = 1 if cur_dotw == 7 else cur_dotw + 1

    yield (cur_dotw, cur_start, end)

    
# Used where there is overlap between night and PH hours
def overlap_hours_in_window(s: datetime, e: datetime, win_start: time, win_end: time) -> float:
    """
    Overlap between [s, e) and a time-of-day window on s.date().
    Supports windows that roll overnight (e.g., 18:00->06:00).
    """
    day = s.date()
    day_start = datetime.combine(day, time(0, 0))
    day_end   = day_start + timedelta(days=1)

    if win_start < win_end:
        window_start_dt = datetime.combine(day, win_start)
        window_end_dt   = datetime.combine(day, win_end)
        a = max(s, window_start_dt)
        b = min(e, window_end_dt)
        return max(0.0, hours_between(a, b))
    else:
        # overnight window: treat as two windows:
        # [win_start, 24:00) and [00:00, win_end] (both on the same "day" footprint)
        w1_start = datetime.combine(day, win_start)
        w1_end   = day_end
        a1 = max(s, w1_start); b1 = min(e, w1_end)
        h1 = max(0.0, hours_between(a1, b1))
        w2_start = day_start
        w2_end   = datetime.combine(day, win_end)
        a2 = max(s, w2_start); b2 = min(e, w2_end)
        h2 = max(0.0, hours_between(a2, b2))
        return h1 + h2

# night window
NIGHT_START = time(18, 0)
NIGHT_END   = time(6, 0)

# --- classifier (row -> Series) ---
def classify_shift_row(row):
    start_dt = row['Timesheet Start Time']
    end_dt   = row['Timesheet End Time']

    night = saturday = sunday = ph = day = 0.0

    for d, s, e in split_by_midnights(start_dt, end_dt):
        part_hours = hours_between(s, e)
        if part_hours <= 0:
            continue

        # PH check per calendar date segment (PH runs only until midnight)
        if s.date() in PUBLIC_HOLIDAYS:
            ph += part_hours
            continue

        # non-PH classification
        if d in (1, 2, 3, 4, 5):  # Mon-Fri
            nh = overlap_hours_in_window(s, e, NIGHT_START, NIGHT_END)
            night += nh
            day   += max(0.0, part_hours - nh)
        elif d == 6:
            saturday += part_hours
        elif d == 7:
            sunday += part_hours

    return pd.Series([night, saturday, sunday, ph, day],
                     index=['Night TS Hours','Saturday TS Hours','Sunday TS Hours','PH TS Hours','Day TS Hours'])

# --- apply to dataframe ---
timesheet_df[['Night TS Hours',
              'Saturday TS Hours',
              'Sunday TS Hours',
              'PH TS Hours',
              'Day TS Hours']] = timesheet_df.apply(classify_shift_row, axis=1)




# Step 1: Calculate Total TS Hours Adj
timesheet_df['Total TS Hours'] = timesheet_df['Night TS Hours'] + timesheet_df['Day TS Hours'] + timesheet_df['Saturday TS Hours'] + timesheet_df['Sunday TS Hours'] + timesheet_df['PH TS Hours']


# Meal Breaks deduct half an hour if shift is over 5 hours
timesheet_df['Meal_Break_Deduction'] = np.where(
    timesheet_df['Total TS Hours'] > 5,
    0.5,
    0
)

timesheet_df['Total TS Hours Adj'] = timesheet_df['Total TS Hours'] - timesheet_df['Meal_Break_Deduction']


# Need adjustments for shifts that have day and nights hours
# If a shift has both day and night hours then the meal break should be deducted from the
# day hours only. If the day hours are less than 0.5 then deduct the balance from the night hours.



# Candidates to remove - 19/09/25
# Day adjustment
# timesheet_df['Day TS Hours Adj'] = np.where(
#     (timesheet_df['Day TS Hours'] > 0) & (timesheet_df['Meal_Break_Deduction'] > 0),
#     np.maximum(0, timesheet_df['Day TS Hours'] - timesheet_df['Meal_Break_Deduction']),
#     timesheet_df['Day TS Hours']
# )

# # Night adjustment
# timesheet_df['Night TS Hours Adj'] = np.where(
#     (timesheet_df['Meal_Break_Deduction'] > 0),
#     np.where(
#         timesheet_df['Day TS Hours'] >= timesheet_df['Meal_Break_Deduction'],
#         timesheet_df['Night TS Hours'],  # meal fully taken from day
#         np.maximum(0, timesheet_df['Night TS Hours'] - np.maximum(0, timesheet_df['Meal_Break_Deduction'] - timesheet_df['Day TS Hours']))
#     ),
#     timesheet_df['Night TS Hours']
# )


# need to do the same for Saturday, Sunday and PH hours if less than 0.5 Day or Night TS Hours exist



# If both Day and Night TS Hours are less than 0.5, apply deduction to Sat/Sun/PH

def apply_meal_break_deduction(timesheet_df):
    """
    Deducts meal break in the following priority order:
    Day TS Hours → Night TS Hours → Saturday TS Hours → Sunday TS Hours → PH TS Hours
    Ensures no double deduction and no negative values.
    """
    # Start with full meal break
    remaining_deduction = timesheet_df['Meal_Break_Deduction'].copy()

    # Day TS Hours Adjustment
    day_deduct = np.minimum(timesheet_df['Day TS Hours'], remaining_deduction)
    timesheet_df['Day TS Hours Adj'] = timesheet_df['Day TS Hours'] - day_deduct
    remaining_deduction -= day_deduct

    # Night TS Hours Adjustment
    night_deduct = np.minimum(timesheet_df['Night TS Hours'], remaining_deduction)
    timesheet_df['Night TS Hours Adj'] = timesheet_df['Night TS Hours'] - night_deduct
    remaining_deduction -= night_deduct

    # Saturday TS Hours Adjustment
    sat_deduct = np.minimum(timesheet_df['Saturday TS Hours'], remaining_deduction)
    timesheet_df['Saturday TS Hours Adj'] = timesheet_df['Saturday TS Hours'] - sat_deduct
    remaining_deduction -= sat_deduct

    # Sunday TS Hours Adjustment
    sun_deduct = np.minimum(timesheet_df['Sunday TS Hours'], remaining_deduction)
    timesheet_df['Sunday TS Hours Adj'] = timesheet_df['Sunday TS Hours'] - sun_deduct
    remaining_deduction -= sun_deduct

    # PH TS Hours Adjustment (last resort)
    ph_deduct = np.minimum(timesheet_df['PH TS Hours'], remaining_deduction)
    timesheet_df['PH TS Hours Adj'] = timesheet_df['PH TS Hours'] - ph_deduct
    remaining_deduction -= ph_deduct

    return timesheet_df

timesheet_df = apply_meal_break_deduction(timesheet_df)

# Ensure datetime
timesheet_df['TS_Start_Date'] = pd.to_datetime(timesheet_df['TS_Start_Date'], errors='coerce')

# === Set your roster cycle anchor (a Monday that began a known roster fortnight) ===
CYCLE_ANCHOR = pd.Timestamp('2023-10-30')  # <- adjust to your real cycle start
if CYCLE_ANCHOR.weekday() != 0:
    raise ValueError("CYCLE_ANCHOR must be a Monday")

# Monday of the week that contains TS_Start_Date
monday_of_week = timesheet_df['TS_Start_Date'] - pd.to_timedelta(timesheet_df['TS_Start_Date'].dt.weekday, unit='D')

# Whole weeks since anchor
weeks_since_anchor = ((monday_of_week - CYCLE_ANCHOR) // pd.Timedelta(days=7)).astype(int)

# Roster week number: Week 1 (even), Week 2 (odd)
timesheet_df['Week Number'] = np.where(weeks_since_anchor % 2 == 0, 1, 2)

# Roster Starting = Monday of the Week 1 in this cycle
timesheet_df['Roster Starting'] = np.where(
    timesheet_df['Week Number'] == 1,
    monday_of_week,
    monday_of_week - pd.Timedelta(days=7)
)
timesheet_df['Roster Starting'] = pd.to_datetime(timesheet_df['Roster Starting'])

# Roster markers
timesheet_df['Week 1 Ending']   = timesheet_df['Roster Starting'] + pd.Timedelta(days=6)   # Sun of Week 1
timesheet_df['Week 2 Starting'] = timesheet_df['Roster Starting'] + pd.Timedelta(days=7)   # Mon of Week 2
timesheet_df['Roster Ending']   = timesheet_df['Roster Starting'] + pd.Timedelta(days=13)  # Sun of Week 2

# Per-row Week Ending (Sun)
timesheet_df['Week Ending'] = np.where(
    timesheet_df['Week Number'] == 1,
    timesheet_df['Week 1 Ending'],
    timesheet_df['Roster Ending']
)



# Pay Dates
# Week 1 Pay Date (Wednesday after Week 1 Ending)
wed_offset_w1 = (2 - timesheet_df['Week 1 Ending'].dt.weekday + 7) % 7
timesheet_df['Week 1 Pay Date'] = timesheet_df['Week 1 Ending'] + pd.to_timedelta(wed_offset_w1, unit='D')

# Week 2 Pay Date (Wednesday after Roster Ending)
wed_offset_w2 = (2 - timesheet_df['Roster Ending'].dt.weekday + 7) % 7
timesheet_df['Week 2 Pay Date'] = timesheet_df['Roster Ending'] + pd.to_timedelta(wed_offset_w2, unit='D')

# Final Estimated Pay Date (based on which week the shift falls into)
timesheet_df['Estimated Pay Date'] = np.where(
    timesheet_df['Week Number'] == 1,
    timesheet_df['Week 1 Pay Date'],
    timesheet_df['Week 2 Pay Date']
)

# === Handle Tuesday exceptions (e.g. Christmas Eve/NYE) ===
# Handle exceptions: adjust pay dates that fall on Christmas Day or New Year's Day
exceptions = [pd.Timestamp('2024-12-25'), pd.Timestamp('2025-01-01')]
timesheet_df.loc[
    timesheet_df['Estimated Pay Date'].isin(exceptions),
    'Estimated Pay Date'
] -= pd.Timedelta(days=1)

# === End of Roster and Pay Date Calculations ===



### ===  Condensing Dataset where incomplete data provided ===

# Cut off Timesheet where Review period incomplete

# Define your cut-off dates
start_date = pd.Timestamp('2025-07-02')  # after this date
end_date = pd.Timestamp('2023-11-15')    # on or before this date

# Filter the DataFrame
timesheet_df = timesheet_df.copy()
timesheet_df = timesheet_df[
    (timesheet_df['Estimated Pay Date'] <= start_date) &
    (timesheet_df['Estimated Pay Date'] > end_date)
]

# Optional: reset index
timesheet_df.reset_index(drop=True, inplace=True)

### === End of Condensing of dataset ===

### === Adding Finacial Year Column ===
        # Assign the financial year (FY) based on the Week Ending
timesheet_df['Financial_Year'] = np.where(
        timesheet_df['Week Ending'].dt.month >= 7,
        timesheet_df['Week Ending'].dt.year + 1,  # July–Dec belongs to the next FY
        timesheet_df['Week Ending'].dt.year  # Jan–June belongs to the current FY
    )

    # Fill NaN values before converting to int
timesheet_df['Financial_Year'] = timesheet_df['Financial_Year'].fillna(0).astype(int)




# Remove perfect duplicates
print('Perfect duplicates check:')
# Check if your dataframe has perfect duplicates
print(len(timesheet_df), len(timesheet_df.drop_duplicates()))
# If yes, drop them
timesheet_df = timesheet_df.drop_duplicates()


# Weekly total hours per employee-week (same value on each row of that week)
timesheet_df['Weekly Total Hours'] = timesheet_df.groupby(
    ['Employee ID Consolidated', 'Week Ending']
)['Total TS Hours Adj'].transform('sum')



# Sort so that cumulative sums follow the actual worked order
timesheet_df = timesheet_df.sort_values(
    by=['Employee ID Consolidated', 'Week Ending', 'Timesheet Start Time', 'Timesheet End Time']
)


# Weekly cumulative hours
timesheet_df['Weekly Cumulative Hours'] = timesheet_df.groupby(
    ['Employee ID Consolidated', 'Week Ending']
)['Total TS Hours Adj'].cumsum()



# Added for OT calculations
timesheet_df['Roster Period Total Hours'] = timesheet_df.groupby(
    ['Employee ID Consolidated', 'Roster Ending']
)['Total TS Hours Adj'].transform('sum')





# Sort by employee and start datetime

timesheet_df = timesheet_df.sort_values(by=['Employee ID Consolidated', 'Timesheet Start Time']).reset_index(drop=True)





# === Minimum Hours Top-up Calculations ===
# Minimum Ordinary Hours, inclusive of Part Time Minimum Hours
# Calculated by taking 20% of the average weekly hours across the review period for each employee 
# or 4 hours if the average is less than 4 hours as per the award.
# flagged as a part time employee
# Part time employees are 41, 356, 429, 457 and 543
# All other employees are full time with a minimum of 7.6 hours per day


timesheet_df['Minimum_Daily_Ordinary_Hours'] = np.where(
    timesheet_df['Employee ID Consolidated'] == 543,  # Part-time minimum hours
    4,
    np.where(
        timesheet_df['Employee ID Consolidated'] == 41,  # Part-time minimum hours
        6.2,
        np.where(
            timesheet_df['Employee ID Consolidated'] == 356,  # Part-time minimum hours
            5.80,
            np.where(
                timesheet_df['Employee ID Consolidated'] == 429,  # Part-time minimum hours
                6,
                np.where(
                    timesheet_df['Employee ID Consolidated'] == 457,  # Part-time minimum hours
                    6.8,
                    Daily_Ordinary_Hours  # Full-time minimum hours
                )
            )
        )
    )
)
    

timesheet_df['Minimum_Hours_Topup'] = np.where(
    (timesheet_df['Total TS Hours'].fillna(0) < timesheet_df['Minimum_Daily_Ordinary_Hours'].fillna(0)) &
    (~timesheet_df['Broken_Shift_Tag'].fillna('').isin(['H1', 'H2'])),
    timesheet_df['Minimum_Daily_Ordinary_Hours'].fillna(0) - timesheet_df['Total TS Hours'].fillna(0),
    0
)
# No instances where it is an issue in our output file but the award says Minimum Ordinary Hours so need to ensure that we don't top up a shift that is fully Roster OT


# Mannual Adjustments
# Timesheet ID == 60478
# Adjust Minimum Hours Topup and Amount to 0 as sick leave was take for that shift
timesheet_df['Minimum_Hours_Topup'] = np.where(
    timesheet_df['Timesheet ID'] == 60478, 
    0,
    timesheet_df['Minimum_Hours_Topup']
)

# === End of Minimum Hours Top-up Calculations ===


# check
timesheet_df.to_csv('line861.csv')




# Flag to detect last shift in dataset
timesheet_df['Gap_Label'] = timesheet_df['Gap_to_Next_Shift_Hours'].isna().map(
    {True: "Last Shift in Review", False: "Has Next Shift"}
)

# If broken shift, ensure gap is greater than 0 and less than 12 hours
# timesheet_df['Broken_Shift_Flag'] = np.where(
#     (timesheet_df['Broken_Shift_Flag'] == 'Y') &
#     (timesheet_df['Gap_to_Next_Shift_Hours'] > 0) &
#     (timesheet_df['Gap_to_Next_Shift_Hours'] < 12),
#     'Y',
#     'N'
# )




# Identify gaps less than 8 hours but greater than 1 hour between shifts (not broken shifts)
timesheet_df['Breaks between work periods Breach'] = np.where(
    (timesheet_df['Gap_to_Next_Shift_Hours'] < 8 ) &
    (timesheet_df['Gap_to_Next_Shift_Hours'] > 1 ) &
    (timesheet_df['Broken_Shift_Flag'] == 'N'),
    'Less than 8 hours',
    'Greater than 8 hours'
)

# Flag if prior shift caused a break between work periods breach, Breach will be on the previous row, but the payable hours are on the current row
# So we need to shift the breach column down one row within each employee group
timesheet_df['Breaks between work periods Top Up Flag'] = (
    timesheet_df.groupby('Employee ID Consolidated')['Breaks between work periods Breach']
    .shift(1)  # look at the previous row in the group
    .eq('Less than 8 hours')  # check if it equals that string
    .map({True: 'Y', False: 'N'})  # convert to Y/N
)

# Calculate Breaks between work periods - Hours
# If breach flag is Y then the current shift hours are payable as top up hours
timesheet_df['Breaks between work periods - Hours'] = np.where(
    (timesheet_df['Breaks between work periods Top Up Flag'] == 'Y') &
    (timesheet_df['Public_Holiday_flag'] != 'Y'),
    timesheet_df['Total TS Hours Adj'],
    0
)

# Added in overwrite of Breaks between work periods Breach column to prevent confusion and flag when prior shift breached
timesheet_df['Breaks between work periods Breach'] = np.where(
    timesheet_df['Breaks between work periods Top Up Flag'] == 'Y',
    'Gap between Prior shift and this shift caused the breach',
    timesheet_df['Breaks between work periods Breach']
)

# === End of Broken Shift and Break Between Work Period Calculations ===



# === Start of Daily and Weekly Overtime Calculations Hours ===
### Daily Overtime if over 10 hours in a day == Max_Ord_Hrs_Day ###
### 2 week roster so Ordinary Hours are 76 hours == Max_Ord_Hrs###



# Daily OT Flag
timesheet_df['Daily OT Flag'] = np.where(
    timesheet_df['Total TS Hours Adj'] > Max_Ord_Hrs_Day,
    'Y',
    'N'
    )





# Daily OT Hours 
# Condition: OT flag is Y and not on a Sunday and not already OT due to weekly hours
# Result: All hours above 10 in the day are OT
timesheet_df['Daily OT Hours'] = np.where(
    ((timesheet_df['Daily OT Flag'] == 'Y') & 
    #  (timesheet_df['Sunday_Penality_flag'] == 'N') & 
    #  (timesheet_df['Public_Holiday_flag'] == 'N') & 
     # Addeed condition to exclude if part time OT hours exist
     # === Logic is incomplete for furture development as Weekly OT considerations 
     # === but vthere are no instances in current data set where Weekly OT exists at the same time as Part time OT
     (timesheet_df['part_time_OT_hours'] == 0)),
     #(timesheet_df['Roster OT Flag'] == 'N'),
    timesheet_df['Total TS Hours Adj'] - Max_Ord_Hrs_Day,
    0)


# If part time OT hours exist then overwrite Daily OT Hours with part time OT hours
timesheet_df['Daily OT Hours'] = np.where(
    timesheet_df['part_time_OT_hours'] > 0,
    timesheet_df['part_time_OT_hours'],
    timesheet_df['Daily OT Hours']
)



# Roster cumulative hours
# Need to subtract Daily OT Hours from cumulative total as these hours are already OT and not Ordinary hours
timesheet_df['Total TS Hours (OT Adj)'] = timesheet_df['Total TS Hours Adj'] - timesheet_df['Daily OT Hours']


timesheet_df['Roster Cumulative Hours'] = timesheet_df.groupby(
    ['Employee ID Consolidated', 'Roster Ending']
)['Total TS Hours (OT Adj)'].cumsum()


# Add back to avoid double counting of OT Hours
# Needed to include Sunday and Public Holiday hours previously so that Total TS Hours Adj is correct and includes hours that are OT Sunday and PH

timesheet_df['Daily OT Hours'] = np.where(
    ((timesheet_df['Daily OT Flag'] == 'Y') & 
     (timesheet_df['Sunday_Penality_flag'] == 'N') & 
     (timesheet_df['Public_Holiday_flag'] == 'N') & 
     # Addeed condition to exclude if part time OT hours exist
     # === Logic is incomplete for furture development as Weekly OT considerations 
     # === but vthere are no instances in current data set where Weekly OT exists at the same time as Part time OT
     (timesheet_df['part_time_OT_hours'] == 0)),
     #(timesheet_df['Roster OT Flag'] == 'N'),
    timesheet_df['Total TS Hours Adj'] - Max_Ord_Hrs_Day,
    0)





# Roster OT Flag
# Identify the first instance where cumulative hours exceed Max_Ord_Hrs in the Roster Period
timesheet_df['Roster OT Flag'] = np.where(
    #(timesheet_df['Roster Period Total Hours'] > Max_Ord_Hrs & timesheet_df['Roster Cumulative Hours'] > Max_Ord_Hrs),
    (timesheet_df['Roster Cumulative Hours'] > Max_Ord_Hrs),
    'Y',
    'N'
)

# Add back to avoid double counting of OT Hours

# Daily OT Hours 
# Condition: OT flag is Y and not on a Sunday and not already OT due to weekly hours
# Result: All hours above 10 in the day are OT
timesheet_df['Daily OT Hours'] = np.where(
    ((timesheet_df['Daily OT Flag'] == 'Y') & 
     (timesheet_df['Sunday_Penality_flag'] == 'N') & 
     (timesheet_df['Public_Holiday_flag'] == 'N') & 
     # Addeed condition to exclude if part time OT hours exist
     # === Logic is incomplete for furture development as Weekly OT considerations 
     # === but vthere are no instances in current data set where Weekly OT exists at the same time as Part time OT
     (timesheet_df['part_time_OT_hours'] == 0)) & 
     (timesheet_df['Roster OT Flag'] == 'N'),
    timesheet_df['Total TS Hours Adj'] - Max_Ord_Hrs_Day,
    0)


# Define time boundaries
day_start = pd.to_datetime('06:00').time()
day_end = pd.to_datetime('18:00').time()


def get_ot_segment(row):
    # Check if Daily OT Hours is greater than 0
    if row.get('Daily OT Hours', 0) <= 0:
        return 'Not Applicable'

    start = row['Timesheet Start Time']
    end = row['Timesheet End Time']

    # Handle overnight shifts
    if end < start:
        end += pd.Timedelta(days=1)

    # Calculate the datetime when ordinary hours are exceeded
    ot_start = start + pd.Timedelta(hours=Max_Ord_Hrs_Day)


    # Determine the calendar date and time of OT start
    ot_date = ot_start.date()
    ot_day = ot_start.day_name()
    ot_time = ot_start.time()

    # Classify based on the calendar day of the OT segment
    if ot_date in PUBLIC_HOLIDAYS:
        return 'Public Holiday'
    elif ot_day == 'Saturday':
        return 'Saturday'
    elif ot_day == 'Sunday':
        return 'Sunday'
    elif day_start <= ot_time < day_end:
        return 'Day'
    else:
        return 'Night'


timesheet_df['OT Segment'] = timesheet_df.apply(get_ot_segment, axis=1)


# Define time boundaries
day_start = pd.to_datetime('06:00').time()
day_end = pd.to_datetime('18:00').time()

def assign_roster_ot_segment(timesheet_df):
    """
    Determines the exact datetime when Roster Overtime begins and assigns OT Segment
    based on whether that point falls in Day, Night, Saturday, Sunday, or Public Holiday.
    Only applies if Roster OT Flag is True.
    """

    def get_roster_ot_segment(row):
        if not row['Roster OT Flag']:
            return 'Not Applicable'

        start = row['Timesheet Start Time']
        end = row['Timesheet End Time']
        shift_duration = pd.Timedelta(hours=row['Timesheet Total Time'])
        cumulative_hours = row['Roster Cumulative Hours']

        # Handle overnight shifts
        if end < start:
            end += pd.Timedelta(days=1)

        # Calculate how far into the current shift the OT begins
        excess_hours = cumulative_hours - Max_Ord_Hrs
        if excess_hours <= 0:
            return 'Not Applicable'

        # OT starts at this offset from shift start
        ot_offset = shift_duration - pd.Timedelta(hours=excess_hours)
        ot_start = start + ot_offset

        # Determine OT segment
        ot_date = ot_start.date()
        ot_day = ot_start.day_name()
        ot_time = ot_start.time()

        if ot_date in PUBLIC_HOLIDAYS:
            return 'Public Holiday'
        elif ot_day == 'Saturday':
            return 'Saturday'
        elif ot_day == 'Sunday':
            return 'Sunday'
        elif day_start <= ot_time < day_end:
            return 'Day'
        else:
            return 'Night'

    # Apply the function and assign the result to a new column
    timesheet_df['Roster OT Segment'] = timesheet_df.apply(get_roster_ot_segment, axis=1)
    return timesheet_df

timesheet_df = assign_roster_ot_segment(timesheet_df)



# Condition 1: all hours are OT if cumulative before this shift > Max_Ord_Hrs
condition1 = (
    (timesheet_df['Roster OT Flag'] == 'Y') &
    ((timesheet_df['Roster Cumulative Hours'] - timesheet_df['Total TS Hours Adj']) > Max_Ord_Hrs)
)

# Condition 2: shift pushes cumulative over Max_Ord_Hrs (partially OT)
condition2 = (timesheet_df['Roster OT Flag'] == 'Y')

timesheet_df['Roster OT Hours'] = np.where(
    condition1,
    # All adjusted hours are OT
    timesheet_df['Total TS Hours Adj'],
    np.where(
        condition2,
        # Part of this shift is OT = adjusted shift hours - remaining ordinary capacity
        timesheet_df['Total TS Hours Adj'] - (
            Max_Ord_Hrs - (timesheet_df['Roster Cumulative Hours'] - timesheet_df['Total TS Hours Adj'])
        ),
        0
    )
)




# # Where Roster OT Hours consumes the whole shift and Daily OT Hours exist then need to adjust the Roster Cumulative Hours
# timesheet_df['Roster Cumulative Hours'] = np.where(
#     (timesheet_df['Roster Cumulative Hours'] > Max_Ord_Hrs) &
#     ((timesheet_df['Roster Cumulative Hours'] + timesheet_df['Daily OT Hours']) >= timesheet_df['Total TS Hours Adj']) &
#     #(timesheet_df['Daily OT Hours'] > 0),
#     (timesheet_df['Roster Cumulative Hours'] + timesheet_df['Daily OT Hours']),
#     timesheet_df['Roster Cumulative Hours']
# )




# Ensure OT hours don't go negative
timesheet_df['Roster OT Hours'] = timesheet_df['Roster OT Hours'].clip(lower=0)

# === End of Daily and Weekly Overtime Calculations Hours ===

# === Avoiding Double counting of Hours ===

# OT Segment == ‘Night & Roster OT Segment == ‘Not Applicable’
# Return Night TS Hours Adj - Daily OT Hours 

timesheet_df['Night TS Hours Adj'] =  np.where(
    (timesheet_df['OT Segment'] == 'Night') &
    (timesheet_df['Roster OT Segment'] == 'Not Applicable'),
    timesheet_df['Night TS Hours Adj'] - timesheet_df['Daily OT Hours'],
    timesheet_df['Night TS Hours Adj'] 
)


# 2. Day OT only (no Roster OT)
timesheet_df['Day TS Hours Adj'] = np.where(
    (timesheet_df['OT Segment'] == 'Day') &
    (timesheet_df['Roster OT Segment'] == 'Not Applicable'),
    timesheet_df['Day TS Hours Adj'] - timesheet_df['Daily OT Hours'],
    timesheet_df['Day TS Hours Adj']
)

# 3. Public Holiday OT only (no Roster OT)
timesheet_df['Daily OT Hours'] = np.where(
    (timesheet_df['OT Segment'] == 'Public Holiday') &
    (timesheet_df['Roster OT Segment'] == 'Not Applicable'),
    0,
    timesheet_df['Daily OT Hours']
)

# 4. Sunday OT only (no Roster OT)
timesheet_df['Daily OT Hours'] = np.where(
    (timesheet_df['OT Segment'] == 'Sunday') &
    (timesheet_df['Roster OT Segment'] == 'Not Applicable'),
    0,
    timesheet_df['Daily OT Hours']
)

# 5. Saturday OT only (no Roster OT)
timesheet_df['Saturday TS Hours Adj'] = np.where(
    (timesheet_df['OT Segment'] == 'Saturday') &
    (timesheet_df['Roster OT Segment'] == 'Not Applicable'),
    timesheet_df['Saturday TS Hours Adj'] - timesheet_df['Daily OT Hours'],
    timesheet_df['Saturday TS Hours Adj']
)







def adjust_weekly_hours(timesheet_df):
    # --- 1. Day Roster OT ---
    mask_day = (timesheet_df['OT Segment'] == 'Not Applicable') & (timesheet_df['Roster OT Segment'] == 'Day')
    day_deduction = np.where(mask_day, timesheet_df['Roster OT Hours'], 0)

    timesheet_df['Day TS Hours Adj'] -= day_deduction
    remainder = np.where(timesheet_df['Day TS Hours Adj'] < 0, -timesheet_df['Day TS Hours Adj'], 0)
    timesheet_df['Day TS Hours Adj'] = np.maximum(timesheet_df['Day TS Hours Adj'], 0)

    timesheet_df['Night TS Hours Adj'] -= remainder
    remainder = np.where(timesheet_df['Night TS Hours Adj'] < 0, -timesheet_df['Night TS Hours Adj'], 0)
    timesheet_df['Night TS Hours Adj'] = np.maximum(timesheet_df['Night TS Hours Adj'], 0)

    timesheet_df['Saturday TS Hours Adj'] -= remainder
    timesheet_df['Saturday TS Hours Adj'] = np.maximum(timesheet_df['Saturday TS Hours Adj'], 0)

    # --- 2. Night Roster OT ---
    mask_night = (timesheet_df['OT Segment'] == 'Not Applicable') & (timesheet_df['Roster OT Segment'] == 'Night')

    # Night hours are reclassified into OT (not Sunday or PH)
    night_to_ot = np.minimum(timesheet_df.loc[mask_night, 'Night TS Hours Adj'],
                            timesheet_df.loc[mask_night, 'Roster OT Hours'])

    # Move hours into OT
    timesheet_df.loc[mask_night, 'Night TS Hours Adj'] -= night_to_ot
    timesheet_df.loc[mask_night, 'Roster OT Hours'] = night_to_ot


    # --- 3. Public Holiday Roster OT ---
    mask_ph = (timesheet_df['OT Segment'] == 'Not Applicable') & (timesheet_df['Roster OT Segment'] == 'Public Holiday')
    timesheet_df['Roster OT Hours'] = np.where(mask_ph, 0, timesheet_df['Roster OT Hours'])

    # --- 4. Sunday Roster OT ---
    mask_sun = (timesheet_df['OT Segment'] == 'Not Applicable') & (timesheet_df['Roster OT Segment'] == 'Sunday')
    timesheet_df['Roster OT Hours'] = np.where(mask_sun, 0, timesheet_df['Roster OT Hours'])

    # --- 5. Saturday Roster OT ---
    mask_sat = (timesheet_df['OT Segment'] == 'Not Applicable') & (timesheet_df['Roster OT Segment'] == 'Saturday')

    # Saturday Hours are reclassified into OT (not Sunday or PH)
    sat_to_ot = np.minimum(timesheet_df.loc[mask_sat, 'Saturday TS Hours Adj'],
                           timesheet_df.loc[mask_sat, 'Roster OT Hours'])
    
    # Move hours into OT
    timesheet_df.loc[mask_sat, 'Saturday TS Hours Adj'] -= sat_to_ot
    timesheet_df.loc[mask_sat, 'Roster OT Hours'] = sat_to_ot



    return timesheet_df



# Apply weekly adjustment
timesheet_df = adjust_weekly_hours(timesheet_df)





# === Start of First 2 Hours OT and Post 2 Hours OT Calculations ===
# First two hours will be on the weekly OT hours basis until told otherwise by CU or VU - 14.08.25
# Condition: weekly cumulative hours > 76 but <= 78
# Weekly OT First 2 Hours and Daily OT First 2 Hours
# Weekly OT First 2 Hours
# Condition: Roster Cumulative Hours > Max_Ord_Hrs, not Sunday, Roster OT Flag is Y and cumulative hours before this shift are <= Max_Ord_Hrs
# Result: no greater than 2 hours OT\
# Need to need to cap at 2 hours if more than 2 hours OT in the week


# Running total of OT hours including this row
# timesheet_df['cumu_ot'] = (
#     timesheet_df.groupby(['Employee ID Consolidated','Roster Ending'])['Roster OT Hours']
#     .cumsum()
# )

# # Remaining cap AT this row (not shifted)
# timesheet_df['remaining_cap'] = (2 - timesheet_df['cumu_ot']).clip(lower=0, upper=2)

# # Allocation for this row = min(this row’s OT, room left BEFORE this row)
# timesheet_df['OT First 2 Hours (Weekly)'] = np.minimum(
#     timesheet_df['Roster OT Hours'],
#     2 - (timesheet_df['cumu_ot'] - timesheet_df['Roster OT Hours']).clip(lower=0, upper=2)
# )

# # Excess goes into post-2 hours
# timesheet_df['OT Post 2 Hours (Weekly)'] = (
#     timesheet_df['Roster OT Hours'] - timesheet_df['OT First 2 Hours (Weekly)']
# ).clip(lower=0)

# First 2 hours of Roster OT (capped at 2)
timesheet_df['OT First 2 Hours (Weekly)'] = np.clip(timesheet_df['Roster OT Hours'], 0, 2)

# Antyhing above 2 goes into post-2
timesheet_df['OT Post 2 Hours (Weekly)'] = (
    timesheet_df['Roster OT Hours'] - timesheet_df['OT First 2 Hours (Weekly)']
).clip(lower=0)


# First 2 hours of daily OT (capped at 2)
timesheet_df['OT First 2 Hours (Daily)'] = np.clip(timesheet_df['Daily OT Hours'], 0, 2)

# Anything above 2 goes into post-2
timesheet_df['OT Post 2 Hours (Daily)'] = (
    timesheet_df['Daily OT Hours'] - timesheet_df['OT First 2 Hours (Daily)']
).clip(lower=0)



# Add the Daily and Weekly OT first 2 hours and post 2 hours as there is no overlap

timesheet_df['OT First 2 Hours'] = timesheet_df['OT First 2 Hours (Weekly)'] + timesheet_df['OT First 2 Hours (Daily)']
timesheet_df['OT Post 2 Hours'] = timesheet_df['OT Post 2 Hours (Weekly)'] + timesheet_df['OT Post 2 Hours (Daily)']




# === End of First 2 Hours OT and Post 2 Hours OT Calculations ===

# === Start of Night, Night (Perm) and Day TS Hours  ===

# if night shift makes up more than 2/3 of time in the roster period then all night shift hours are at 130% rate
# if night shift makes up less than 2/3 of time in the roster period then all night shift hours are at 121.7% Rate
# columns needed: Night TS Hours, Roster Period Total Hours
# Need to cumulate night shift hours over the roster period

# Added to determine OT eligibility point in time
# Ensure the grouping columns uniquely define a roster period (adjust if needed)
group_cols = ['Employee ID Consolidated', 'Roster Ending']

# Total Night TS Hours per roster period (aligned back with original rows)
timesheet_df['Total Night TS Hours'] = (
    timesheet_df.groupby(group_cols)['Night TS Hours']
    .transform('sum')
)
# Total Day TS Hours per roster period (aligned back with original rows)
timesheet_df['Total Day TS Hours'] = (
    timesheet_df.groupby(group_cols)['Day TS Hours']
    .transform('sum')
)


# Ratio of night shift hours
# If more than 2/3 hours are nights within Roster Period then flag as Y otherwise N
timesheet_df['Night Shift Ratio'] = (
    timesheet_df['Total Night TS Hours'] / (timesheet_df['Total Night TS Hours'] + timesheet_df['Total Day TS Hours'])
)
#Condition: If night shift ratio is greater than 2/3 then flag as Y otherwise N
timesheet_df['Perm_Night_Ratio_Flag'] = np.where(
    timesheet_df['Night Shift Ratio'] > (2/3),
    'Y',
    'N'
)

timesheet_df = timesheet_df.drop_duplicates(subset=['Timesheet ID', 'Team member'])

# === End of Night, Night (Perm) and Day TS Hours  ===

timesheet_df.to_excel("pre_payroll_timesheet.xlsx", sheet_name='test')


# === Start of Merge for Payrates with Timesheet dataframe ===
# Pull in the pay rates

payrates_df = pd.read_excel(r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\2025.08.19 - Employee classification & rate.xlsx", sheet_name='Staff List_FY level min rates')


# Ensure dates are datetime
payrates_df['FY Starting'] = pd.to_datetime(payrates_df['FY Starting'])
payrates_df['FY Ending'] = pd.to_datetime(payrates_df['FY Ending'])
timesheet_df['Estimated Pay Date'] = pd.to_datetime(timesheet_df['Estimated Pay Date'])

# Ensure both Employee IDs are the same dtype
timesheet_df['Employee ID Consolidated'] = timesheet_df['Employee ID Consolidated'].astype(str).str.strip()
payrates_df['Employee ID'] = payrates_df['Employee ID'].astype(str).str.strip()




# Select only the needed columns from payrates_df
payrates_subset = payrates_df[
    ['Employee ID', 'FY Starting', 'FY Ending', 
     'Broken Shift Allowance Rate',
     'First Aid Allowance Rate',
     'Meal Allowance Rate',
     'Paid Minimum Hourly Pay Rate',
    'Award Minimum Hourly Pay Rate',
    'Award Night Pay Rate',
    'Award Perm Night Pay Rate',
    'Award Saturday Pay Rate',
    'Award Sunday Pay Rate',
    'Award Public Holiday Pay Rate',
    'Award Overtime First 2 Hours',
    'Award Overtime After 2 Hours',
    'Paid Night Pay Rate',
    'Paid Perm Night Pay Rate',
    'Paid Saturday Pay Rate',
    'Paid Sunday Pay Rate',
    'Paid Public Holiday Pay Rate',
    'Paid Overtime First 2 Hours',
    'Paid Overtime after 2 Hours'
]
]

# Merge
timesheet_df = timesheet_df.merge(
    payrates_subset,
    left_on='Employee ID Consolidated',
    right_on='Employee ID',
    how='left'
)

# Filter by date range to trims down to only the correct payrate row — 
# where the timesheet’s pay date actually falls within the valid payrate period.
timesheet_df = timesheet_df[
    (timesheet_df['Estimated Pay Date'] >= timesheet_df['FY Starting']) &
    (timesheet_df['Estimated Pay Date'] <= timesheet_df['FY Ending'])
]

# 1) Remove perfect duplicates
print('Perfect duplicates check:')
# Check if your dataframe has perfect duplicates
print(len(timesheet_df), len(timesheet_df.drop_duplicates()))
# If yes, drop them
timesheet_df = timesheet_df.drop_duplicates()

# === End of Merge for Payrates with timesheet dataframe



# === Start of First Aid and Broken Shift Allowance Calculations ===
# First Aid Allowance is payable at $7.33 per shift up to a maximum of $36.46 per week or approximately 5 shifts per week.
#All employees in review hold a current Senior First Aid Certificate (also known as Provide First Aid or Workplace First Aid)


# Pull in correct Broken Shift Allowance Rate
# Pull in correct Broken Shift Allowance Rate
timesheet_df['Broken Shift Allowance Amount'] = np.where(
    (timesheet_df['Broken_Shift_Tag'] == 'H1') | (timesheet_df['Broken_Shift_Tag'] == 'H2'),
    timesheet_df['Broken Shift Allowance Rate'] / 2,
    0
)


#  Cumulative shift count within the week
timesheet_df['Shift_count_cum'] = timesheet_df.groupby(
    ['Employee ID Consolidated', 'Week Ending']
).cumcount() + 1

# Condition: Cut off after 5 shifts within a week
timesheet_df['First Aid Allowance Flag'] =np.where(
    timesheet_df['Shift_count_cum'] <= 5,
    'Y',
    'N'
)

# Amount due per shift for the allowance
# Condtion:  Where Flag is Y, Gap to next shift is 0.5 or greater and Broken Shift Flag is no in order to avoid counting one shift as two
# Also added in a Gap_Label for instances where it is the last shift in the review period and thus we won't have a shift gap
# Result: First Aid Allowance Rate per shift
# timesheet_df['First Aid Allowance Amount'] = np.where(
#     (timesheet_df['First Aid Allowance Flag'] == 'Y') & 
#     (
#         (timesheet_df['Gap_to_Next_Shift_Hours'] >= 0.5) |
#         (timesheet_df['Gap_Label'] == "Last Shift in Review")
#     ) &
#     (timesheet_df['Broken_Shift_Flag'] == 'N'),
#     timesheet_df['First Aid Allowance Rate'],
#     0
# )


timesheet_df['First Aid Allowance Amount'] = np.where(
    (timesheet_df['First Aid Allowance Flag'] == 'Y') ,
    timesheet_df['First Aid Allowance Rate'],
    0
)
# === End of First Aid and Broken Shift Calcs


# === Meal Allowance Calculations ===
timesheet_df['Timesheet End Time'] = pd.to_datetime(timesheet_df['Timesheet End Time'], errors='coerce')
timesheet_df['Roster_End DateTime'] = pd.to_datetime(timesheet_df['Roster_End DateTime'], errors='coerce')


# Meal allowance if shift ends 1 hour or more after rostered end time
valid_mask = timesheet_df['Timesheet End Time'].notna() & timesheet_df['Roster_End DateTime'].notna()
timesheet_df['Meal_Allowance_Flag'] = 'N'  # default
timesheet_df.loc[valid_mask, 'Meal_Allowance_Flag'] = np.where(
    timesheet_df.loc[valid_mask, 'Timesheet End Time'] - timesheet_df.loc[valid_mask, 'Roster_End DateTime'] >= pd.Timedelta(hours=1),
    'Y',
    'N'
)

timesheet_df['Meal_Allowance_Amount'] = np.where(
    timesheet_df['Meal_Allowance_Flag'] == 'Y',
    timesheet_df['Meal Allowance Rate'],
    0
)
  


# Zero out hours in shift that are recorded in Day, Night, Saturday and Sunday where hours exists in 'Breaks between work periods - Hours'
# Added to avoid confusion when client reviews file can be commented out if we prefer

timesheet_df['Day TS Hours Adj'] = np.where(
    timesheet_df['Breaks between work periods - Hours'] > 0,
    0,
    timesheet_df['Day TS Hours Adj']
)

timesheet_df['Night TS Hours'] = np.where(
    timesheet_df['Breaks between work periods - Hours'] > 0,
    0,
    timesheet_df['Night TS Hours'] 
)


timesheet_df['Night TS Hours Adj'] = np.where(
     timesheet_df['Breaks between work periods - Hours'] > 0,
    0,
    timesheet_df['Night TS Hours Adj']
)

timesheet_df['Saturday TS Hours Adj'] = np.where(
    timesheet_df['Breaks between work periods - Hours'] > 0,
    0,
    timesheet_df['Saturday TS Hours Adj']
)

timesheet_df['Sunday TS Hours Adj'] = np.where(
    timesheet_df['Breaks between work periods - Hours'] > 0,
    0,
    timesheet_df['Sunday TS Hours Adj']
)

timesheet_df['OT First 2 Hours'] = np.where(
    timesheet_df['Breaks between work periods - Hours'] > 0,
    0,
    timesheet_df['OT First 2 Hours']
)

timesheet_df['OT Post 2 Hours'] = np.where(
    timesheet_df['Breaks between work periods - Hours'] > 0,
    0,
    timesheet_df['OT Post 2 Hours']
)
             




# Zero out hours in shift that are recorded in Day, Night, Saturday and Sunday where hours exists in 'Overtime'
# Added to avoid confusion when client reviews file can be commented out if we prefer

# Minumum Hours Top up Amount
# Minmum hours tiop is payable at the Award Minimum Hourly Pay Rate
# and is completely separate to any other allowances or penalties

timesheet_df['Minimum_Hours_Topup_Amount'] = timesheet_df['Minimum_Hours_Topup'] * timesheet_df['Award Minimum Hourly Pay Rate']

timesheet_df['Broken_Shift_Topup_Amount'] = timesheet_df['Broken Shift Topup Hours'] * timesheet_df['Award Minimum Hourly Pay Rate']

# Mannual Adjustments
# Timesheet ID == 60478
# Adjust Minimum Hours Topup and Amount to 0 as sick leave was take for that shift
timesheet_df['Minimum_Hours_Topup_Amount'] = np.where(
    timesheet_df['Timesheet ID'] == 60478,
    0,
    timesheet_df['Minimum_Hours_Topup_Amount']
)

# Night Amount due as per award perm nights and none perm nights
timesheet_df['Night Amount (Award)'] = np.where(
    timesheet_df['Perm_Night_Ratio_Flag'] == 'Y',
    (timesheet_df['Night TS Hours Adj'] * timesheet_df['Award Perm Night Pay Rate']).round(2),
    np.where(
        (timesheet_df['Perm_Night_Ratio_Flag'] == 'N'),
        (timesheet_df['Night TS Hours Adj'] * timesheet_df['Award Night Pay Rate']).round(2),
        0
)
)

# Day Amount (Award) calculation
timesheet_df['Day Amount (Award)'] = (
    (timesheet_df['Day TS Hours Adj'] * timesheet_df['Award Minimum Hourly Pay Rate']).round(2)
)

# Saturday Amount (Award) calculation
# Condition: Saturday Penality flag is Y and Breaks between work periods Top Up Flag is N
timesheet_df['Saturday Amount (Award)'] = np.where(
    #(timesheet_df['Saturday_Penality_flag'] == 'Y') 
    (timesheet_df['Saturday TS Hours Adj'] > 0) &
    (timesheet_df['Breaks between work periods Top Up Flag'] == 'N') &
    #(timesheet_df['Public_Holiday_flag'] =='N')
    (timesheet_df['PH TS Hours Adj'] <= 0),
    
    (timesheet_df['Saturday TS Hours Adj'] * timesheet_df['Award Saturday Pay Rate']).round(2),
    0
)

# Sunday Amount (Award) calculation
# Condition: Sunday Penality flag is Y and PH Flag is N
timesheet_df['Sunday Amount (Award)'] = np.where(
    #(timesheet_df['Sunday_Penality_flag'] == 'Y') 
    (timesheet_df['Sunday TS Hours Adj'] > 0),
    #(timesheet_df['PH TS Hours Adj'] <= 0),
   # (timesheet_df['Public_Holiday_flag'] =='N'),
    (timesheet_df['Sunday TS Hours Adj'] * timesheet_df['Award Sunday Pay Rate']).round(2),
    0
)

# PH Amount Calculation
timesheet_df['Public Holiday Amount (Award)'] =np.where(
   # (timesheet_df['Public_Holiday_flag'] =='Y'),
    (timesheet_df['PH TS Hours Adj'] > 0),
    (timesheet_df['PH TS Hours Adj'] * timesheet_df['Award Public Holiday Pay Rate']).round(2),
    0

)
# First 2 hours OT Calculation
timesheet_df['OT First 2 Hours Amount (Award)'] = np.where(
    (timesheet_df['OT First 2 Hours'] > 0) &
    (timesheet_df['Breaks between work periods Top Up Flag'] == 'N'),
    (timesheet_df['OT First 2 Hours'] * timesheet_df['Award Overtime First 2 Hours']).round(2),
    0
)

# Post First 2 hours OT Calc
timesheet_df['OT Post 2 Hours Amount (Award)'] = np.where(
    (timesheet_df['OT Post 2 Hours'] > 0) &
    (timesheet_df['Breaks between work periods Top Up Flag'] == 'N'),
    (timesheet_df['OT Post 2 Hours'] * timesheet_df['Award Overtime After 2 Hours']).round(2),
    0
)

# Break between work periods breach - Amount
timesheet_df['Breaks between work periods - Amount (Award)'] = np.where(
    timesheet_df['Breaks between work periods Top Up Flag'] == 'Y',
    (timesheet_df['Breaks between work periods - Hours'] * (timesheet_df['Award Minimum Hourly Pay Rate']*2)).round(2),
    0
)
timesheet_df['Total Amount (Award)'] = ( 
    timesheet_df['Night Amount (Award)'] +
    timesheet_df['Day Amount (Award)'] +
    timesheet_df['Saturday Amount (Award)'] +
    timesheet_df['Sunday Amount (Award)'] +
    timesheet_df['Public Holiday Amount (Award)'] +
    timesheet_df['OT First 2 Hours Amount (Award)'] +
    timesheet_df['OT Post 2 Hours Amount (Award)'] + 
    timesheet_df['Breaks between work periods - Amount (Award)'] +
    timesheet_df['Minimum_Hours_Topup_Amount'] +
    timesheet_df['Broken_Shift_Topup_Amount']
).round(2)




columns_to_drop = [

#'TS_Start_Date',
#'TS_End_Date',
#'TS_TimeOnly_Start',
#'TS_TimeOnly_End',
'DOTW',
'Week 1 Ending',
'Week 2 Starting',
'Week 1 Pay Date',
'Week 2 Pay Date',
'Start_dt',
'End_dt',
#'Next_Start_dt',
#'Gap_to_Next_Shift_Hours',

'Timesheet Cost',
'Employee ID',
'FY Starting',
'FY Ending',
'Total Night TS Hours',
'Total Day TS Hours',
'Night Shift Ratio'


]


timesheet_df = timesheet_df.drop(columns=columns_to_drop)
# Reorder columns for better readability

timesheet_df['TS_Start_Date'] = pd.to_datetime(timesheet_df['TS_Start_Date']).dt.date





# Build EmpID_PayDay_Key (EmpID + Pay Date)
# Ensure it's datetime
timesheet_df['Estimated Pay Date'] = pd.to_datetime(
    timesheet_df['Estimated Pay Date'], errors='coerce'
)

# Now safe to format
timesheet_df['EmpID_PayDay_Key'] = (
    timesheet_df['Employee ID Consolidated'].astype(str) + "_" +
    timesheet_df['Estimated Pay Date'].dt.strftime("%Y-%m-%d")
)



# Ensure datetime types
timesheet_df['TS_Start_Date'] = pd.to_datetime(timesheet_df['TS_Start_Date'])
timesheet_df['Roster Ending'] = pd.to_datetime(timesheet_df['Roster Ending'])

# Calculate the difference in days
timesheet_df['Days Before Roster End'] = (timesheet_df['Roster Ending'] - timesheet_df['TS_Start_Date']).dt.days

# Assign Week Number based on the 7-day threshold
timesheet_df['Week Number'] = timesheet_df['Days Before Roster End'].apply(
    lambda x: 1 if x >= 7 else 2
)


# Create Unique key on Employee Id, Roster Ending and Week Number for later aggregation
timesheet_df['EmpID_Week_Key'] = (
    timesheet_df['Employee ID Consolidated'].astype(str) + "_" +
    timesheet_df['Roster Ending'].dt.strftime("%Y-%m-%d") + "_W" +
    timesheet_df['Week Number'].astype(str)
)




column_order = [
    'EmpID_PayDay_Key',
    'EmpID_Week_Key',

    'Timesheet ID',
    'Timesheet ID (Combined Shift)',
'Team member',
'Employee ID Consolidated',
#'Timesheet Status',
'Timesheet Start Time',
'Timesheet End Time',
'Financial_Year',
'TS_Start_Date',
'TS_End_Date',
'TS_TimeOnly_Start',
'TS_TimeOnly_End',
'Timesheet Total Time',
'Shift Start Time',
'Shift End Time',
'Shift Total Time',
'Roster_Start DateTime', 
'Roster_End DateTime', 
'Roster_Hours',
'Timesheet location',
'Timesheet area',

'Timesheet Employee Comment',
'Comments_Roster',
'Combined_Shift',
'Broken_Shift_Tag',

'Week Number',
'Roster Starting',
'Week Ending',
'Roster Ending',
'Estimated Pay Date',
#'Difference in Hours',
'Weekday',
"Public_Holiday_flag",
'Saturday_Penality_flag',
'Sunday_Penality_flag',
'Day TS Hours',
'Night TS Hours',

'Saturday TS Hours',
'Sunday TS Hours',
'PH TS Hours',
            
'Meal_Break_Deduction',
#'Meal_Allowance_Flag',
'Meal_Allowance_Amount',
'Minimum_Daily_Ordinary_Hours',
'Day TS Hours Adj',
'Night TS Hours Adj',
'Perm_Night_Ratio_Flag',
'Saturday TS Hours Adj',
'Sunday TS Hours Adj',
'Breaks between work periods - Hours',
'PH TS Hours Adj',
'Total TS Hours',
'Total TS Hours Adj',
'Total TS Hours (OT Adj)',
'Broken Shift Topup Hours',
'Minimum_Hours_Topup',

#'Weekly Cumulative Hours',
'Roster Cumulative Hours',
#'Weekly Total Hours',
#'Roster Period Total Hours',
'Next_Start_dt',
'Gap_to_Next_Shift_Hours',
#'Shift_Duration_Hours',
'Next_Shift_Duration_Hours',
'Broken_Shift_Flag',
'Broken_Shift_Tag',
'Breaks between work periods Breach',
'Breaks between work periods Top Up Flag',
#'Breaks between work periods - Hours',


'Daily OT Flag',
'Roster OT Flag',
'part_time_OT_hours',
'Daily OT Hours',
'Roster OT Hours',
'OT First 2 Hours',
'OT Post 2 Hours',
'Paid Minimum Hourly Pay Rate',
'Award Minimum Hourly Pay Rate',
#'Award Night Pay Rate',
#'Award Perm Night Pay Rate',
#'Award Saturday Pay Rate',
#'Award Sunday Pay Rate',
#'Award Public Holiday Pay Rate',
#'Award Overtime First 2 Hours',
#'Award Overtime After 2 Hours',
#'Paid Night Pay Rate',
#'Paid Perm Night Pay Rate',
#'Paid Saturday Pay Rate',
#'Paid Sunday Pay Rate',
#'Paid Public Holiday Pay Rate',
#'Paid Overtime First 2 Hours',
#'Paid Overtime after 2 Hours',
'Night Amount (Award)',
'Day Amount (Award)',
'Saturday Amount (Award)',
'Sunday Amount (Award)',
'Public Holiday Amount (Award)',
'OT First 2 Hours Amount (Award)',
'OT Post 2 Hours Amount (Award)',
'Breaks between work periods - Amount (Award)',
'Minimum_Hours_Topup_Amount',
'Broken_Shift_Topup_Amount',
'Total Amount (Award)',
'First Aid Allowance Amount',

'Broken Shift Allowance Amount',
]
# Reorder columns
timesheet_df = timesheet_df[column_order]







# Preview
#timesheet_df.to_excel("Timesheet_clean.xlsx", sheet_name='timesheet', index=False)
timesheet_df.to_excel("Timesheet_Pre_Payroll_Join.xlsx", sheet_name='timesheet', index=False)

### === End of Timesheet standalone Calculations ===

### === Start of Overtime Calculations Inclusive of Leave

# Create new DF so we can group weekly by EMPLID and Pay Date rather than Roster Ending
timesheet_df_weekly_for_Leave = timesheet_df.copy()


# Build EmpID_PayDay_Key (EmpID + Pay Date)
# Ensure it's datetime
timesheet_df_weekly_for_Leave['Estimated Pay Date'] = pd.to_datetime(
    timesheet_df_weekly_for_Leave['Estimated Pay Date'], errors='coerce'
)

# Now safe to format
timesheet_df_weekly_for_Leave['EmpID_PayDay_Key'] = (
    timesheet_df_weekly_for_Leave['Employee ID Consolidated'].astype(str) + "_" +
    timesheet_df_weekly_for_Leave['Estimated Pay Date'].dt.strftime("%Y-%m-%d")
)


# Ensure datetime types
timesheet_df_weekly_for_Leave['TS_Start_Date'] = pd.to_datetime(timesheet_df_weekly_for_Leave['TS_Start_Date'])
timesheet_df_weekly_for_Leave['Roster Ending'] = pd.to_datetime(timesheet_df_weekly_for_Leave['Roster Ending'])

# Calculate the difference in days
timesheet_df_weekly_for_Leave['Days Before Roster End'] = (timesheet_df_weekly_for_Leave['Roster Ending'] - timesheet_df_weekly_for_Leave['TS_Start_Date']).dt.days

# Assign Week Number based on the 7-day threshold
timesheet_df_weekly_for_Leave['Week Number'] = timesheet_df_weekly_for_Leave['Days Before Roster End'].apply(
    lambda x: 1 if x >= 7 else 2
)


# Create Unique key on Employee Id, Roster Ending and Week Number for later aggregation
timesheet_df_weekly_for_Leave['EmpID_Week_Key'] = (
    timesheet_df_weekly_for_Leave['Employee ID Consolidated'].astype(str) + "_" +
    timesheet_df_weekly_for_Leave['Roster Ending'].dt.strftime("%Y-%m-%d") + "_W" +
    timesheet_df_weekly_for_Leave['Week Number'].astype(str)
)



def first_nonnull(series):
    """Return first non-null value, or NaN if all null."""
    non_nulls = series.dropna()
    return non_nulls.iloc[0] if not non_nulls.empty else np.nan


ts = first_nonnull(timesheet_df_weekly_for_Leave)
print(ts)



agg_dict = {
    # identifiers / dates (use first_nonnull)
    'EmpID_PayDay_Key'       : first_nonnull,
    'Employee ID Consolidated': first_nonnull,
    'Estimated Pay Date'     : first_nonnull,
    'Financial_Year'         : first_nonnull,
    'Roster Starting'        : first_nonnull,
    'Week Ending'            : first_nonnull,
    'Roster Ending'          : first_nonnull,
    'Week Number'            : first_nonnull,
    'Team member'            : first_nonnull,

    # numeric columns (sum them up)
    'Day TS Hours'           : 'sum',
    'Night TS Hours'         : 'sum',
    'Saturday TS Hours' : 'sum',
    'Sunday TS Hours' : 'sum',
    'PH TS Hours' : 'sum',
    'Day TS Hours Adj'       : 'sum',
    'Night TS Hours Adj'     : 'sum', 
    'PH TS Hours Adj'            : 'sum',
    'Saturday TS Hours Adj'      : 'sum',
    'Sunday TS Hours Adj'        : 'sum',
    'Timesheet Total Time'   : 'sum',
    'Total TS Hours Adj'     : 'sum',
    'Roster OT Hours'        : 'sum',
    'OT First 2 Hours'       : 'sum',
    'OT Post 2 Hours'        : 'sum',
    'Breaks between work periods - Hours': 'sum',
    'Minimum_Hours_Topup'    : 'sum',

    'Night Amount (Award)'   : 'sum',
    'Day Amount (Award)'     : 'sum',
    'Saturday Amount (Award)': 'sum',
    'Sunday Amount (Award)'  : 'sum',
    'Public Holiday Amount (Award)': 'sum',

    'OT First 2 Hours Amount (Award)'  : 'sum',
    'OT Post 2 Hours Amount (Award)'   : 'sum',
    'Breaks between work periods - Amount (Award)': 'sum',
    'Minimum_Hours_Topup_Amount' : 'sum',
    'Broken_Shift_Topup_Amount' : 'sum',
    'Total Amount (Award)'   : 'sum',
    'First Aid Allowance Amount': 'sum',
    'Broken Shift Allowance Amount': 'sum',
    'Meal_Allowance_Amount' : 'sum',
    'Timesheet Total Time' : 'sum',
    'Total TS Hours' : 'sum',
    'Total TS Hours (OT Adj)' : 'sum',
    'Shift Total Time' : 'sum',
    # Pull in Min Hourly rate for Leave Loading use
    'Award Minimum Hourly Pay Rate' : 'mean'
}

timesheet_df_weekly_for_Leave = (
    timesheet_df_weekly_for_Leave
      .groupby('EmpID_Week_Key', as_index=False)
      .agg(agg_dict)
)


timesheet_df_weekly_for_Leave.to_excel('line1622.xlsx', sheet_name='shifttotaltimecheck')

payroll_data = pd.read_excel(payroll_data)

# Left Join timesheet weekly data with payroll data using Employee and Pay Day Key
timesheet_df_weekly_for_Leave = timesheet_df_weekly_for_Leave.merge(payroll_data,
                                   on=['EmpID_PayDay_Key'],
                                   how='left')


# Drop unneed columns and keep only Leave related ones

columns_to_drop = [

# PAY RELATED COLUMNS TO Keep

#     'Rate_BACK PAY',
# 'Current_BACK PAY',
# 'Rate_Bereavement',
# 'Current_Bereavement',
# 'Rate_Extra Payment',
# 'Qty_Extra Payment',
# 'Current_Extra Payment',
# 'Rate_First Aid Allowance',
# 'Qty_First Aid Allowance',
# 'Current_First Aid Allowance',
# 'Current_Gross Pay',
# 'Rate_Hourly Day',
# 'Current_Hourly Day',
# 'Rate_Hourly Night',
# 'Current_Hourly Night',
# 'Rate_Hourly Public Holiday',
# 'Current_Hourly Public Holiday',
# 'Rate_Hourly Saturday',
# 'Current_Hourly Saturday',
#'Rate_Hourly Sunday',
#'Current_Hourly Sunday',
#'Rate_Personal Hourly',
#'Current_Personal Hourly',

'Rate_Personal Salary',
'Current_Personal Salary',
'Qty_Holiday Salary',


# 'Rate_Public Holiday Hourly',
# 'Current_Public Holiday Hourly',
# 'Rate_Public Holiday Not W...',
# 'Current_Public Holiday Not W...',


'Rate_Salary',
'Current_Salary',
'Qty_Salary',
'Qty_Sick Leave Salary',
'Qty_Personal Salary',


# PAY RELATED COLUMNS TO DROP
'Rate_Net Pay',
'Qty_Net Pay',
'Current_Net Pay',
'Rate_PAYG Tax',
'Qty_PAYG Tax',
'Current_PAYG Tax',


'Current_Reimbursement',
'Rate_Super',
'Qty_Super',
'Current_Super',
'Rate_Supervisor Allowance',
'Qty_Supervisor Allowance',
'Current_Supervisor Allowance',

# LEAVE RELATED COLUMNS TO DROP
#'Rate_Annual Holiday Loadi...',
#'Current_Annual Holiday Loadi...',
'Rate_Annual Leave',
'Current_Annual Leave',
'Rate_Holiday Hourly',
'Current_Holiday Hourly',
'Rate_Holiday Loading',
'Current_Holiday Loading',
'Rate_Holiday Salary',
'Current_Holiday Salary',

'Qty_Public Holiday Not Worked',
'Rate_Public Holiday Not Worked',
'Current_Public Holiday Not Worked',
'Fortnight_Total',


'Rate_Sick Leave Salary',
'Current_Sick Leave Salary',
'Qty_Personal Salary',

#'Current_Sick Leave Hourly',
#'Rate_Sick Leave Hourly',

'Roster OT Hours'

]


# Total Leave Hours =  Qty_Holiday Hourly + Qty_Annual_Leave + Qty_Sick Leave Hourly

timesheet_df_weekly_for_Leave['Total Leave Hours'] = (
    timesheet_df_weekly_for_Leave[['Qty_Holiday Hourly', 'Qty_Annual Leave', 'Qty_Sick Leave Hourly']]
    .fillna(0)
    .sum(axis=1)
)



timesheet_df_weekly_for_Leave = timesheet_df_weekly_for_Leave.rename(
    columns={'Qty_Annual Holiday Loadi...': 'Qty_Annual_Holiday_Loading'}
)
timesheet_df_weekly_for_Leave['Qty_Annual_Holiday_Loading'] = pd.to_numeric(timesheet_df_weekly_for_Leave['Qty_Annual_Holiday_Loading'])


# Get actual QTY of leave for loading rather than dollar amount
timesheet_df_weekly_for_Leave['Qty_Annual_Holiday_Loading_AMOUNT'] = (timesheet_df_weekly_for_Leave['Qty_Annual_Holiday_Loading'] * 0.175).round(2)
timesheet_df_weekly_for_Leave['Qty_Annual_Holiday_Loading'] = timesheet_df_weekly_for_Leave['Qty_Annual_Holiday_Loading'] / timesheet_df_weekly_for_Leave['Rate_Hourly Day']

# Fixes to Payroll data missing values

# Fixes to Payroll data missing values
timesheet_df_weekly_for_Leave.loc[513, 'Qty_Annual_Holiday_Loading'] = 12
timesheet_df_weekly_for_Leave.loc[834, 'Qty_Annual_Holiday_Loading'] = 36
timesheet_df_weekly_for_Leave.loc[1531, 'Qty_Annual_Holiday_Loading'] = 16
timesheet_df_weekly_for_Leave.loc[1787, 'Qty_Annual_Holiday_Loading'] = 32
timesheet_df_weekly_for_Leave.loc[1825, 'Qty_Annual_Holiday_Loading'] = 18

timesheet_df_weekly_for_Leave['Total Leave Loading (SW Calc)'] =  ((timesheet_df_weekly_for_Leave['Total Leave Hours'] * timesheet_df_weekly_for_Leave['Award Minimum Hourly Pay Rate']) * 0.175).round(2)


timesheet_df_weekly_for_Leave['Leave Loading Hour Diff'] = (timesheet_df_weekly_for_Leave['Total Leave Hours'] - timesheet_df_weekly_for_Leave['Qty_Annual_Holiday_Loading']).round(2)

timesheet_df_weekly_for_Leave['Leave Loading Amount Discrepancy'] = (timesheet_df_weekly_for_Leave['Qty_Annual_Holiday_Loading_AMOUNT'] - timesheet_df_weekly_for_Leave['Total Leave Loading (SW Calc)']).round(2)




# Create a unique key for each employee and roster period to group data later
timesheet_df_weekly_for_Leave['Fortnight_Key'] = (
    timesheet_df_weekly_for_Leave['Employee ID Consolidated'].astype(str) + '_' +
    timesheet_df_weekly_for_Leave['Roster Ending'].astype(str)
)






def calculate_effective_hours(df):
    df = df.copy()

    # Step 1: Calculate effective leave hours
    # Exclude leave in Week 2 entirely
   
    df['Effective_Leave'] = np.where(
        df['Week Number'] == 2,
        0,  # Always exclude leave in Week 2


    # Change Threshold to be where hours worked + Leave is greatet than 50 effective leave = 0 


        np.where(
            (df['Total Leave Hours'] + df['Total TS Hours (OT Adj)']) > 50,
            0,
             #np.maximum(38 - df['Total TS Hours (OT Adj)'], 0),  # Include only enough leave to reach 38 hours
            df['Total Leave Hours']  # Otherwise, include all leave hours
        )
    )




    # Step 2: Calculate total effective hours (adjusted timesheet + effective leave)
    df['Effective_Total'] = df['Total TS Hours (OT Adj)'] + df['Effective_Leave']

    return df


# def calculate_overtime(group):
#     # Step 1: Calculate total hours for the fortnight
#     fortnight_total = group['Effective_Total'].sum()
    
#     # Step 2: Only show the fortnight total on Week 2 rows
#     group['Fortnight_Total'] = np.nan
#     group.loc[group['Week Number'] == 2, 'Fortnight_Total'] = fortnight_total

#     # Step 3: Calculate excess hours over the maximum ordinary hours (e.g., 76 for 2 weeks)
#     excess = max(fortnight_total - Max_Ord_Hrs, 0)

#     # Step 4: Calculate overtime per week
#     group = group.sort_values('Week Number')  # Ensure weeks are in order
#     ot = []
#     for _, row in group.iterrows():
#         # If Week 2 has no adjusted hours but has leave, don't count as overtime
#         if (row['Week Number'] == 2) and (row['Total TS Hours (OT Adj)'] == 0) and (row['Effective_Leave'] > 0):
#             ot_hours = 0
#         else:
#             # Allocate overtime from adjusted hours, up to the remaining excess
#             ot_hours = min(row['Total TS Hours (OT Adj)'], excess)
#             excess -= ot_hours

#         ot.append(ot_hours)

#     # Step 5: Cosmetic adjustment – show all overtime in the first Week 2 row
#     week2_idx = group[group['Week Number'] == 2].index
#     if len(week2_idx) > 0:
#         group['Weekly_Overtime_Hours (Incl Leave)'] = np.nan
#         group.loc[week2_idx[0], 'Weekly_Overtime_Hours (Incl Leave)'] = sum(ot)

#     return group



def calculate_overtime(group):
    # Step 1: Calculate total hours for the fortnight
    fortnight_total = group['Effective_Total'].sum()
    
    # Step 2: Only show the fortnight total on Week 2 rows
    group['Fortnight_Total'] = np.nan
    group.loc[group['Week Number'] == 2, 'Fortnight_Total'] = fortnight_total

    # Step 3: Calculate excess hours over the maximum ordinary hours (e.g., 76 for 2 weeks)
    excess = max(fortnight_total - Max_Ord_Hrs, 0)

    # Step 4: Calculate overtime per week
    group = group.sort_values('Week Number')  # Ensure weeks are in order
    ot = []
    for _, row in group.iterrows():
        # Always exclude leave from Week 2
        if row['Week Number'] == 2:
            effective_hours = row['Total TS Hours (OT Adj)']
        else:
            effective_hours = row['Effective_Total']

        # Allocate overtime from adjusted hours, up to the remaining excess
        ot_hours = min(effective_hours, excess)
        excess -= ot_hours
        ot.append(ot_hours)

    # Step 5: Cosmetic adjustment – show all overtime in the first Week 2 row
    week2_idx = group[group['Week Number'] == 2].index
    group['Weekly_Overtime_Hours (Incl Leave)'] = np.nan
    if len(week2_idx) > 0:
        group.loc[week2_idx[0], 'Weekly_Overtime_Hours (Incl Leave)'] = sum(ot)

    return group







# Apply per employee + roster cycle
timesheet_df_weekly_for_Leave = calculate_effective_hours(timesheet_df_weekly_for_Leave)
timesheet_df_weekly_for_Leave = timesheet_df_weekly_for_Leave.groupby(['Fortnight_Key','Roster Ending'], group_keys=False).apply(calculate_overtime)

# Rename Roster OT Hours to Roster OT Hours (Excl Leave)
# Leave data is only provided in weekly form and not on days taken
timesheet_df_weekly_for_Leave['Roster OT Hours (Excl Leave)'] = timesheet_df_weekly_for_Leave['Roster OT Hours'] 


# Drop only if the columns exist in your DataFrame
timesheet_df_weekly_for_Leave = timesheet_df_weekly_for_Leave.drop(columns=[col for col in columns_to_drop if col in timesheet_df_weekly_for_Leave.columns])




# Calculate if any difference between prior calculated OT and OT Inclusive of Leave
# Further Calculation logic can follow where we look at where to apply the addition OT i.e. First 2 Hours or Post First Two hours
# Revisit this later if required - 3/09/2025
timesheet_df_weekly_for_Leave['Difference between  Weekly OT (Excl Leave) and Weekly OT (Incl Leave)'] =  timesheet_df_weekly_for_Leave['Weekly_Overtime_Hours (Incl Leave)'] - timesheet_df_weekly_for_Leave['Roster OT Hours (Excl Leave)'] 

timesheet_df_weekly_for_Leave['Weekly_Overtime_Hours (Incl Leave)'].rename(
    'Roster_Overtime_Hours (Incl Leave)'
)


# Define pairs of quantity and rate columns that represent different types of worked hours
pairs = [
    ('Qty_Hourly Day',            'Rate_Hourly Day'),
    ('Qty_Hourly Night',          'Rate_Hourly Night'),
    ('Qty_Public Holiday Hourly', 'Rate_Public Holiday Hourly'),
    ('Qty_Hourly Saturday',       'Rate_Hourly Saturday'),
    ('Qty_Hourly Sunday',         'Rate_Hourly Sunday'),
]

# Helper function: safely convert a column (Series) or scalar to numeric
# - Handles strings with $, commas, or blanks
# - Converts invalid or missing values to 0

def _num(series_or_scalar):
    if isinstance(series_or_scalar, pd.Series):
        # Convert values to string, strip out $ and commas, convert to float
        s = series_or_scalar.astype(str).str.replace(r'[\$,]', '', regex=True)
        return pd.to_numeric(s, errors='coerce').fillna(0.0)
    else:
        # If the column doesn’t exist, get() will return the default scalar 0
        # In that case just return 0.0
        return 0.0

# Create a running total Series initialised to 0.0, aligned to the DataFrame index
# This ensures that calculations for each row are accumulated correctly
total = pd.Series(0.0, index=timesheet_df_weekly_for_Leave.index)

# Loop through each pair of (quantity column, rate column)
for qty_col, rate_col in pairs:
    # Get the quantity column, or 0 if it doesn’t exist, and convert to numeric
    q = _num(timesheet_df_weekly_for_Leave.get(qty_col, 0))
    # Get the rate column, or 0 if it doesn’t exist, and convert to numeric
    r = _num(timesheet_df_weekly_for_Leave.get(rate_col, 0))
    # Multiply quantity * rate and add to the running total
    total += q * r

# Allied OTE and Penality hours, OT never paid so not included 
timesheet_df_weekly_for_Leave['Allied Oridnary Hours and Penality Amount'] = total.round(2)




# Define the quantity columns that represent different types of worked hours
qty_columns = [
    'Qty_Hourly Day',
    'Qty_Hourly Night',
    'Qty_Public Holiday Hourly',
    'Qty_Hourly Saturday',
    'Qty_Hourly Sunday',
]


# Create a running total Series initialised to 0.0, aligned to the DataFrame index
total_hours = pd.Series(0.0, index=timesheet_df_weekly_for_Leave.index)

# Loop through each quantity column and accumulate the total hours
for qty_col in qty_columns:
    q = _num(timesheet_df_weekly_for_Leave.get(qty_col, 0))
    total_hours += q

# Add the total hours to the DataFrame
timesheet_df_weekly_for_Leave['Total Worked Hours (Paystubs)'] = total_hours.round(2)



# Total Amount (Award) = Day + Night + Sat + Sunday + PH + OT First 2 + OT Post First 2 + Breaks between work period penality 
# Allied Oridnary Hours and Penality Amount = Day + Night + Saturday + Sunday + PH 
# Disrepancy for Pay as per Award Vs Actual payments made by Allied at higher rates but with no OT calcualtions 
timesheet_df_weekly_for_Leave['Discrepancy_Actual_Vs_Award (Excluding Allowances)'] = timesheet_df_weekly_for_Leave['Allied Oridnary Hours and Penality Amount'] -  timesheet_df_weekly_for_Leave['Total Amount (Award)']

# Difference between
timesheet_df_weekly_for_Leave['Discrepancy_First_Aid_Allowance'] = timesheet_df_weekly_for_Leave['Current_First Aid Allowance'] - timesheet_df_weekly_for_Leave['First Aid Allowance Amount']

# Allied made no payments for Broken Shift Allowance so Disrepancy is exactly equal to our calcs
timesheet_df_weekly_for_Leave['Discrepancy_Broken_Shift_Allowance'] = timesheet_df_weekly_for_Leave['Broken Shift Allowance Amount']

timesheet_df_weekly_for_Leave['Discrepancy_Meal_Allowance'] = timesheet_df_weekly_for_Leave['Meal_Allowance_Amount']

timesheet_df_weekly_for_Leave['Discrepancy_Actual_Vs_Award (Including Allowances)'] = (timesheet_df_weekly_for_Leave['Allied Oridnary Hours and Penality Amount'] + \
                                                                                      timesheet_df_weekly_for_Leave['Current_First Aid Allowance'] )  - \
                                                                                      (timesheet_df_weekly_for_Leave['Total Amount (Award)' ] + \
                                                                                       timesheet_df_weekly_for_Leave['First Aid Allowance Amount'] + \
                                                                                       timesheet_df_weekly_for_Leave['Broken Shift Allowance Amount'] + \
                                                                                       timesheet_df_weekly_for_Leave['Meal_Allowance_Amount'])
                                                                                      



timesheet_df_weekly_for_Leave.to_excel('SW_Payment_Calcs_As_Per_Award_Vs_ Allied_Actual_Pay.xlsx', sheet_name='Award_Vs_Actuals') 

entitlements_data = timesheet_df_weekly_for_Leave.copy()

entitlements_data['Overtime Hours Discrepancy'] = -(entitlements_data['OT First 2 Hours Amount (Award)']  + entitlements_data['OT Post 2 Hours Amount (Award)'])

entitlements_data['Night Amount Discrepancy'] =  (entitlements_data['Qty_Hourly Night'] * entitlements_data['Rate_Hourly Night']) - entitlements_data['Night Amount (Award)']

entitlements_data['Saturday Amount Discrepancy'] = (entitlements_data['Rate_Hourly Saturday'] * entitlements_data['Qty_Hourly Saturday']) - entitlements_data['Saturday Amount (Award)'] 

entitlements_data['Sunday Amount Discrepancy'] = (entitlements_data['Qty_Hourly Sunday'] * entitlements_data['Rate_Hourly Sunday']) -  entitlements_data['Sunday Amount (Award)'] 

entitlements_data['Public Holiday Amount Discrepancy'] = (entitlements_data['Rate_Public Holiday Hourly'] * entitlements_data['Qty_Public Holiday Hourly']) - entitlements_data['Public Holiday Amount (Award)'] 


column_toKeep = [
    'EmpID_Week_Key',
'EmpID_PayDay_Key',
'Employee ID Consolidated',
'Estimated Pay Date',
'Financial_Year',
'Roster Starting',
'Week Ending',
'Roster Ending',
'Week Number',
'Team member',
# 'Day TS Hours',
# 'Night TS Hours',
# 'Saturday TS Hours',
# 'Sunday TS Hours',
# 'PH TS Hours',
# 'Day TS Hours Adj',
# 'Night TS Hours Adj',
# 'PH TS Hours Adj',
# 'Saturday TS Hours Adj',
# 'Sunday TS Hours Adj',
# 'Timesheet Total Time',
# 'Total TS Hours Adj',
'OT First 2 Hours',
'OT Post 2 Hours',
'Breaks between work periods - Hours',
'Minimum_Hours_Topup',
'Breaks between work periods - Amount (Award)',
'Minimum_Hours_Topup_Amount',
'Broken_Shift_Topup_Amount',
'First Aid Allowance Amount',
'Broken Shift Allowance Amount',
'Meal_Allowance_Amount',
'Leave Loading Amount Discrepancy',
'Discrepancy_First_Aid_Allowance',
'Discrepancy_Broken_Shift_Allowance',
'Discrepancy_Meal_Allowance',
'Overtime Hours Discrepancy',
'Night Amount Discrepancy',
'Saturday Amount Discrepancy',
'Sunday Amount Discrepancy',
'Public Holiday Amount Discrepancy',
'Allied Oridnary Hours and Penality Amount'

]

entitlements_data = entitlements_data[column_toKeep]


entitlements_data.to_excel('Entitlements_Discrepancy_Check.xlsx', sheet_name='Entitlements_Check')