import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta

# Load and clean timesheet data
def load_and_clean_timesheet(file_path):
    df = pd.read_excel(file_path, sheet_name='Timesheet details')
    df = df.dropna(axis=1, how='all')  # Remove empty columns

    df['Timesheet ID'] = df['Timesheet ID'].astype(int)

    datetime_cols = [
        'Timesheet Start Time',
        'Timesheet End Time',
        'Shift Start Time',
        'Shift End Time'
    ]
    for col in datetime_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')

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
        end_dt += timedelta(days=1)

    total_hours = 0
    current_time = start_dt
    while current_time < end_dt:
        current_hour = current_time.time()
        if shift_start <= shift_end:
            if shift_start <= current_hour < shift_end:
                total_hours += 1
        else:  # Overnight shift
            if current_hour >= shift_start or current_hour < shift_end:
                total_hours += 1
        current_time += timedelta(hours=1)
    return total_hours

# File path
timesheet_file_path = r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Timesheet detail 1 Nov 2023 to 30 June 2025.xlsx"

# Load data
timesheet_df = load_and_clean_timesheet(timesheet_file_path)

# Calculate total hours
timesheet_df['Difference in Hours'] = calculate_time_difference_in_hours(
    timesheet_df['TS_Start_Date'],
    timesheet_df['TS_TimeOnly_Start'],
    timesheet_df['TS_TimeOnly_End']
)

# Calculate night and day shift hours

timesheet_df['Day Shift Hours'] = timesheet_df.apply(
    lambda row: calculate_shift_hours(row['TS_TimeOnly_Start'], row['TS_TimeOnly_End'], time(6, 0), time(18, 0)),
    axis=1
)




timesheet_df['Night Shift Hours'] = timesheet_df.apply(
    lambda row: calculate_shift_hours(row['TS_TimeOnly_Start'], row['TS_TimeOnly_End'], time(18, 0), time(6, 0)),
    axis=1
)


# Step 1: Add `DOTW` (Day of the Week) where Saturday is 1 and Friday is 7
# Step 1: Map days of the week using the desired mapping
day_mapping = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7}  # Monday=1, Sunday=7

# # Create the DOTW column and apply the mapping
timesheet_df['DOTW'] = timesheet_df['Timesheet Start Time'].dt.weekday.map(day_mapping)
# Custom numeric mapping: Saturday = 1, Sunday = 2, ..., Friday = 7
# Add Day of the Week as text (e.g. Monday, Tuesday, etc.)
timesheet_df['Weekday'] = pd.to_datetime(timesheet_df['TS_Start_Date']).dt.day_name()





# Step 1: Calculate total shift hours
timesheet_df['Total Shift Hours'] = timesheet_df['Night Shift Hours'] + timesheet_df['Day Shift Hours']

# Step 2: Ensure TS_Start_Date is datetime
timesheet_df['TS_Start_Date'] = pd.to_datetime(timesheet_df['TS_Start_Date'])



# Week Ending (Sunday)
timesheet_df['Week Ending'] = timesheet_df['TS_Start_Date'] + pd.to_timedelta(
    6 - timesheet_df['TS_Start_Date'].dt.weekday, unit='d'
)



# Aggregate weekly totals per team member
weekly_df = timesheet_df.groupby(['Team member', 'Week Ending'], as_index=False)['Total Shift Hours'].sum()
weekly_df.rename(columns={'Total Shift Hours': 'weekly total hours'}, inplace=True)
weekly_df = weekly_df.sort_values(['Team member', 'Week Ending'])


# Step 4: Group by Team Member and Week Ending, then sum total shift hours 
timesheet_df['weekly cumulative total hours'] = timesheet_df.groupby( ['Team member', 'Week Ending'] )['Total Shift Hours'].transform('cumsum')


# Function to calculate rolling totals for any week window
def add_rolling_weeks(df, weeks=4):
    df = df.sort_values(['Team member', 'Week Ending'])
    df[f'rolling_{weeks}_weeks_hours'] = (
        df.groupby('Team member')['weekly total hours']
          .rolling(window=weeks, min_periods=1)
          .sum()
          .reset_index(level=0, drop=True)
    )
    df[f'Week Ending ({weeks}w)'] = df['Week Ending']
    return df

# Example: 2, 3, 4, 8-week rolling totals
# Commented out due to 1 week roster being used
#for w in [1, 2, 3, 4, 8]:
for w in [1]:
    weekly_df = add_rolling_weeks(weekly_df, weeks=w)

# Optional: merge rolling totals back to original timesheet_df if needed
timesheet_df = timesheet_df.merge(
    weekly_df.drop(columns=['weekly total hours']),
    on=['Team member', 'Week Ending'],
    how='left'
)

# 1 week roster so Weekly Ordinary Hours is 38 hours

timesheet_df['Weekly OT Flag'] = np.where(
    timesheet_df['weekly cumulative total hours'] > 38,
    'Y',
    'N'
)

# Condition: OT flag is Y and cumulative hours *before* this shift exceed 38
condition1 = (timesheet_df['Weekly OT Flag'] == 'Y') & \
             ((timesheet_df['weekly cumulative total hours'] - timesheet_df['Total Shift Hours']) > 38)

# Condition: OT flag is Y (used in second np.where)
condition2 = timesheet_df['Weekly OT Flag'] == 'Y'

timesheet_df['Weekly OT Hours'] = np.where(
    condition1,
    # All shift hours are OT if we've already exceeded 38 before this shift
    timesheet_df['Total Shift Hours'],
    np.where(
        condition2,
        # Part of this shift may push us over 38, so subtract the remaining non-OT hours
        timesheet_df['Total Shift Hours'] - (
            38 - (timesheet_df['weekly cumulative total hours'] - timesheet_df['Total Shift Hours'])
        ),
        0
    )
)

# Ensure OT hours don't go negative
timesheet_df['Weekly OT Hours'] = timesheet_df['Weekly OT Hours'].clip(lower=0)


timesheet_df['OT First 2 Hours'] = 



# # Step 3: Create a 'Week Ending' column (Sunday as week end)
# # Week ending on Friday (weekday=4)
# timesheet_df['Week Ending'] = timesheet_df['TS_Start_Date'] + pd.offsets.Week(weekday=6)







# # Step 1: Sort by Team Member and Week Ending
# timesheet_df = timesheet_df.sort_values(['Team member', 'Week Ending'])

# # Step 4: Function to calculate rolling totals for any week window
# def add_rolling_weeks(df, weeks=4):
#     df = df.sort_values(['Team member', 'Week Ending'])
#     df[f'rolling_{weeks}_weeks_hours'] = (
#         df.groupby('Team member')['weekly total hours']
#           .rolling(window=weeks, min_periods=1)
#           .sum()
#           .reset_index(level=0, drop=True)
#     )
#     # Optional: create Week Ending column for rolling window (last week in window)
#     df[f'Week Ending ({weeks}w)'] = df['Week Ending']
#     return df

# # Example: 2, 3, 4, 8-week rolling totals
# for w in [2, 3, 4, 8]:
#     weekly_df = add_rolling_weeks(weekly_df, weeks=w)

# # Step 5: Compute cumulative sum per Team Member
# weekly_totals['Cumulative Shift Hours'] = weekly_totals.groupby('Team member')['Total Shift Hours'].cumsum()


# print(weekly_totals)

# weekly_totals.to_csv('weeklyTotals.csv')

# Optional: Save to Excel
# weekly_cumsum.to_excel("weekly_cumulative_shift_hours.xlsx")



# Optional: Save to Excel
# timesheet_df.to_excel("processed_timesheet.xlsx", index=False)

# Preview
print(timesheet_df[['TS_TimeOnly_Start', 'TS_TimeOnly_End', 'Difference in Hours', 'Night Shift Hours', 'Day Shift Hours']])
timesheet_df.to_excel("Timesheet_clean.xlsx", sheet_name='timesheet', index=False)