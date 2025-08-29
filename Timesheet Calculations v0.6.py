import pandas as pd
import numpy as np

from datetime import datetime, date, time, timedelta


# Ordinary hours and overtime cutoffs

Max_Ord_Hrs = 76
First_2_Hrs_OT_Cutoff = 78

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
# def calculate_shift_hours(start_time, end_time, shift_start, shift_end):
#     start_dt = datetime.combine(datetime.today(), start_time)
#     end_dt = datetime.combine(datetime.today(), end_time)
#     if end_dt <= start_dt:
#         end_dt += timedelta(days=1)

#     total_hours = 0
#     current_time = start_dt
#     while current_time < end_dt:
#         current_hour = current_time.time()
#         if shift_start <= shift_end:
#             if shift_start <= current_hour < shift_end:
#                 total_hours += 1
#         else:  # Overnight shift
#             if current_hour >= shift_start or current_hour < shift_end:
#                 total_hours += 1
#         current_time += timedelta(hours=1)
#     return total_hours

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





# File path
timesheet_file_path = r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Timesheet detail 1 Nov 2023 to 30 June 2025.xlsx"
emplids_mapping = pd.read_excel(r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Employee IDs.xlsx", sheet_name='EMPLIDS')

payroll_data = r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Payroll_Output.xlsx"



# Load data
timesheet_df = load_and_clean_timesheet(timesheet_file_path)

print(timesheet_df.columns)

print(emplids_mapping.columns)

emplids_mapping['Team member'] = emplids_mapping['Team member'].astype(str)


timesheet_df = timesheet_df.merge(
    emplids_mapping[['Team member', 'Employee ID Consolidated']],
    on='Team member',
    how='left'
)

timesheet_df['Employee ID Consolidated'] = (
    timesheet_df['Employee ID Consolidated']
    .astype(str)
    .str.replace(r"\.0$", "", regex=True)  # strip only a trailing .0
    .str.strip()
)




# Drop rows where Team member is 'Anthony Knight'
timesheet_df = timesheet_df[timesheet_df['Team member'] != 'Anthony Knight']

# (Optional) Reset the index if you want a clean index after dropping
timesheet_df = timesheet_df.reset_index(drop=True)




# Calculate total hours
timesheet_df['Difference in Hours'] = calculate_time_difference_in_hours(
    timesheet_df['TS_Start_Date'],
    timesheet_df['TS_TimeOnly_Start'],
    timesheet_df['TS_TimeOnly_End']

)





# Calculate night and Day TS Hours

# timesheet_df['Day TS Hours'] = timesheet_df.apply(
#     lambda row: calculate_shift_hours(row['TS_TimeOnly_Start'], row['TS_TimeOnly_End'], time(6, 0), time(18, 0)),
#     axis=1
# )

# timesheet_df['Night TS Hours'] = timesheet_df.apply(
#     lambda row: calculate_shift_hours(row['TS_TimeOnly_Start'], row['TS_TimeOnly_End'], time(18, 0), time(6, 0)),
#     axis=1
# )

# Calculate night and Day TS Hours 




# def get_shift_hours(row):
#     dow = row['Day of the Week']  # assuming Mon=1, Sun=7
#     start, end = row['TS_TimeOnly_Start'], row['TS_TimeOnly_End']

#     if dow in [1, 2, 3, 4, 5]:  # Mon–Fri
#         return (
#             calculate_shift_hours(start, end, time(6, 0), time(18, 0)),   # Day
#             calculate_shift_hours(start, end, time(18, 0), time(6, 0)),  # Night
#             0,  # Saturday
#             0   # Sunday
#         )
#     elif dow == 6:  # Saturday
#         return (0, 0, (datetime.combine(datetime.today(), end) -
#                        datetime.combine(datetime.today(), start)).total_seconds() / 3600, 0)
#     elif dow == 7:  # Sunday
#         return (0, 0, 0,
#                 (datetime.combine(datetime.today(), end) -
#                  datetime.combine(datetime.today(), start)).total_seconds() / 3600)
#     else:
#         return (0, 0, 0, 0)

# # Apply function and assign to multiple columns
# timesheet_df[['Day TS Hours', 'Night TS Hours', 'Saturday TS Hours', 'Sunday TS Hours']] = (
#     timesheet_df.apply(get_shift_hours, axis=1, result_type='expand')
# )


# Step 1: Add `DOTW` (Day of the Week) where Saturday is 1 and Friday is 7
# Step 1: Map days of the week using the desired mapping
day_mapping = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7}  # Monday=1, Sunday=7

# # Create the DOTW column and apply the mapping
timesheet_df['DOTW'] = timesheet_df['Timesheet Start Time'].dt.weekday.map(day_mapping)
# Custom numeric mapping: Saturday = 1, Sunday = 2, ..., Friday = 7
# Add Day of the Week as text (e.g. Monday, Tuesday, etc.)
timesheet_df['Weekday'] = pd.to_datetime(timesheet_df['TS_Start_Date']).dt.day_name()



# Estimated pay date column for joining with Payroll data set. All pay dates are on Wednesday except 
#24/12/2024	and 31/12/2024	which fall on a Tuesday





# Can make these account for Weekend OT and PH once the PH list is complete

timesheet_df['Saturday_Penality_flag'] = np.where(
    timesheet_df['DOTW'] == 6,
    'Y',
    'N'
)

timesheet_df['Sunday_Penality_flag'] = np.where(
    timesheet_df['DOTW'] == 7,
    'Y',
    'N'
)



# Day shift (Mon–Fri only, weekdays 1–5)
timesheet_df['Day TS Hours'] = timesheet_df.apply(
    lambda row: calculate_shift_hours(row['TS_TimeOnly_Start'], row['TS_TimeOnly_End'], time(6, 0), time(18, 0))
    if row['DOTW'] in [1, 2, 3, 4, 5] else 0,
    axis=1
)

# Night shift (Mon–Fri only, weekdays 1–5)
timesheet_df['Night TS Hours'] = timesheet_df.apply(
    lambda row: calculate_shift_hours(row['TS_TimeOnly_Start'], row['TS_TimeOnly_End'], time(18, 0), time(6, 0))
    if row['DOTW'] in [1, 2, 3, 4, 5] else 0,
    axis=1
)


# Saturday TS Hours (all worked hours on Sat)
timesheet_df['Saturday TS Hours'] = timesheet_df.apply(
    #lambda row: calculate_shift_hours(row['TS_TimeOnly_Start'], row['TS_TimeOnly_End'], time(0, 0), time(23, 59))
    lambda row: calculate_shift_hours(row['TS_TimeOnly_Start'], row['TS_TimeOnly_End'], time(0, 0), time(0, 0))
    if row['DOTW'] == 6 else 0,
    axis=1
)

# Sunday TS Hours (all worked hours on Sun)
timesheet_df['Sunday TS Hours'] = timesheet_df.apply(
    #lambda row: calculate_shift_hours(row['TS_TimeOnly_Start'], row['TS_TimeOnly_End'], time(0, 0), time(23, 59))
    lambda row: calculate_shift_hours(row['TS_TimeOnly_Start'], row['TS_TimeOnly_End'], time(0, 0), time(0, 0))
    if row['DOTW'] == 7 else 0,
    axis=1
)




# Need to add shift count feature per day so that we can calculate the below pay rule: 
# Broken Shift Minimum 3 Hours	  
# An employee who works broken shifts is entitled to be paid for at least 3 hours for each period of duty on a broken shift even if the employee works for a shorter time.

# Pivot table seems to indicate that broken shifts exist 



# Step 1: Calculate Total TS Hours Adj
timesheet_df['Total TS Hours'] = timesheet_df['Night TS Hours'] + timesheet_df['Day TS Hours'] + timesheet_df['Saturday TS Hours'] + timesheet_df['Sunday TS Hours']



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

# Day adjustment
timesheet_df['Day TS Hours Adj'] = np.where(
    (timesheet_df['Day TS Hours'] > 0) & (timesheet_df['Meal_Break_Deduction'] > 0),
    np.maximum(0, timesheet_df['Day TS Hours'] - timesheet_df['Meal_Break_Deduction']),
    timesheet_df['Day TS Hours']
)

# Night adjustment
timesheet_df['Night TS Hours Adj'] = np.where(
    (timesheet_df['Meal_Break_Deduction'] > 0),
    np.where(
        timesheet_df['Day TS Hours'] >= timesheet_df['Meal_Break_Deduction'],
        timesheet_df['Night TS Hours'],  # meal fully taken from day
        np.maximum(0, timesheet_df['Night TS Hours'] - np.maximum(0, timesheet_df['Meal_Break_Deduction'] - timesheet_df['Day TS Hours']))
    ),
    timesheet_df['Night TS Hours']
)


# !!!!!!!!!!!!!!!!   TO do 27/08/25!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Need to do the financial calculations on cleaned_timesheet_df rather than weeksheet_df 

# Step 2: Ensure TS_Start_Date is datetime
timesheet_df['TS_Start_Date'] = pd.to_datetime(timesheet_df['TS_Start_Date'])



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
exceptions = [pd.Timestamp('2024-12-24'), pd.Timestamp('2024-12-31')]
timesheet_df.loc[timesheet_df['Estimated Pay Date'].isin(exceptions), 'Estimated Pay Date'] -= pd.Timedelta(days=1)


# # Step 4: Group by Team Member and Roster Ending, then sum Total TS Hours 
# timesheet_df['Roster Period Total Hours'] = timesheet_df.groupby( ['Employee ID Consolidated', 'Roster Ending'] )['Total TS Hours Adj'].transform('sum')

print('duplicates check')

# Check if your dataframe has perfect duplicates
print(len(timesheet_df), len(timesheet_df.drop_duplicates()))

# If yes, drop them
timesheet_df = timesheet_df.drop_duplicates()



# 2) Weekly total hours per employee-week (same value on each row of that week)
timesheet_df['Weekly Total Hours'] = timesheet_df.groupby(
    ['Employee ID Consolidated', 'Week Ending']
)['Total TS Hours Adj'].transform('sum')

# 3) Weekly cumulative hours per employee-week (sorted within the week)
timesheet_df = timesheet_df.sort_values(
    ['Employee ID Consolidated', 'Week Ending', 'Timesheet Start Time']
)
timesheet_df['Weekly Cumulative Hours'] = timesheet_df.groupby(
    ['Employee ID Consolidated', 'Week Ending']
)['Total TS Hours Adj'].cumsum()


# Added to determine OT eligibility point in time
timesheet_df['Roster Cumulative Hours'] = timesheet_df.groupby(
    ['Employee ID Consolidated', 'Roster Ending']
)['Total TS Hours Adj'].cumsum()


# # 4) Fortnight (roster) total per employee (if you need it)
timesheet_df['Roster Period Total Hours'] = timesheet_df.groupby(
    ['Employee ID Consolidated', 'Roster Ending']
)['Total TS Hours Adj'].transform('sum')




print('columns as per line 307')
print(timesheet_df.columns)


timesheet_df.to_csv('timesheet_preGapCalc.csv')


# Create full datetime columns using combine
timesheet_df['Start_dt'] = timesheet_df.apply(
    lambda row: pd.Timestamp.combine(row['TS_Start_Date'], row['TS_TimeOnly_Start']), axis=1
)
timesheet_df['End_dt'] = timesheet_df.apply(
    lambda row: pd.Timestamp.combine(row['TS_End_Date'], row['TS_TimeOnly_End']), axis=1
)


# Sort by employee and start datetime


timesheet_df = timesheet_df.sort_values(by=['Employee ID Consolidated', 'Shift Start Time']).reset_index(drop=True)



Daily_Ordinary_Hours = 7.6

timesheet_df = timesheet_df.drop_duplicates(
    subset=['Employee ID Consolidated', 'Shift Start Time']
).sort_values(
    by=['Employee ID Consolidated', 'Shift Start Time']
).reset_index(drop=True)

timesheet_df['Next_Start_dt'] = (
    timesheet_df.groupby('Employee ID Consolidated')['Shift Start Time'].shift(-1)
)

timesheet_df['Next_End_dt'] = (
    timesheet_df.groupby('Employee ID Consolidated')['End_dt'].shift(-1)
)

# Calculate current shift duration in hours
timesheet_df['Shift_Duration_Hours'] = (
    (timesheet_df['End_dt'] - timesheet_df['Start_dt']).dt.total_seconds() / 3600
)

timesheet_df['Next_Shift_Duration_Hours'] = (
    (timesheet_df['Next_End_dt'] - timesheet_df['Next_Start_dt']).dt.total_seconds() / 3600
)

# Check if end and next start are on the same calendar day
timesheet_df['Same_Day'] = (
    timesheet_df['End_dt'].dt.date == timesheet_df['Next_Start_dt'].dt.date
)

# Apply Broken Shift rules
timesheet_df['Broken_Shift_Flag'] = np.where(
    (timesheet_df['Same_Day']) &
    (timesheet_df['Shift_Duration_Hours'] < Daily_Ordinary_Hours) &
    (timesheet_df['Next_Shift_Duration_Hours'] < Daily_Ordinary_Hours),
    'Y',
    'N'
)

# Calculate gap in hours between current end and next start
timesheet_df['Gap_to_Next_Shift_Hours'] = (
    (timesheet_df['Next_Start_dt'] - timesheet_df['End_dt']).dt.total_seconds() / 3600
)

# If broken shift, ensure gap is greater than 0 and less than 12 hours
timesheet_df['Broken_Shift_Flag'] = np.where(
    (timesheet_df['Broken_Shift_Flag'] == 'Y') &
    (timesheet_df['Gap_to_Next_Shift_Hours'] > 0) &
    (timesheet_df['Gap_to_Next_Shift_Hours'] < 12),
    'Y',
    'N'
)


timesheet_df['Broken Shift Allowance Amount'] = np.where(
    timesheet_df['Broken_Shift_Flag'] == 'Y',
    17.47,
    0
)


timesheet_df['Breaks between work periods'] = np.where(
    (timesheet_df['Gap_to_Next_Shift_Hours'] < 8 ) &
    (timesheet_df['Gap_to_Next_Shift_Hours'] > 0 ) &
    (timesheet_df['Broken_Shift_Flag'] == 'N'),
    'Less than 8 hours',
    'Greater than 8 hours'
)

# Optional: filter or flag gaps
# timesheet_df['Flag_Short_Gap'] = timesheet_df['Gap_to_Next_Shift_Hours'] < 12

# Display or export
print(timesheet_df[['Employee ID Consolidated', 'Start_dt', 'End_dt', 'Gap_to_Next_Shift_Hours']])



timesheet_df.to_csv('timesheet_with_gaps.csv')






### !!!!!! OverTime Calculations !!!!!!!!!!!!!!!!!
### 2 week roster so Ordinary Hours are 76 hours ###

Max_Ord_Hrs_Day = 10
Max_Ord_Hrs = 76
First_2_Hrs_OT_Cutoff = 78



timesheet_df['Daily OT Flag'] = np.where(
    timesheet_df['Total TS Hours Adj'] > Max_Ord_Hrs_Day,
    'Y',
    'N'
    )





timesheet_df['Weekly OT Flag'] = np.where(
    #(timesheet_df['Roster Period Total Hours'] > Max_Ord_Hrs & timesheet_df['Roster Cumulative Hours'] > Max_Ord_Hrs),
    (timesheet_df['Roster Cumulative Hours'] > Max_Ord_Hrs),
    'Y',
    'N'
)


timesheet_df['Daily OT Hours'] = np.where(
    ((timesheet_df['Daily OT Flag'] == 'Y') & (timesheet_df['Sunday_Penality_flag'] == 'N') & (timesheet_df['Weekly OT Flag'] == 'N')),
    timesheet_df['Total TS Hours Adj'] - Max_Ord_Hrs_Day,
    0)


# Condition: OT flag is Y and cumulative hours *before* this shift exceed 38
condition1 = (timesheet_df['Weekly OT Flag'] == 'Y') & \
            ((timesheet_df['Roster Cumulative Hours'] - timesheet_df['Total TS Hours Adj']) > Max_Ord_Hrs)
             #((timesheet_df['Roster Period Total Hours'] - timesheet_df['Total TS Hours Adj']) > Max_Ord_Hrs)
             


# Condition: OT flag is Y (used in second np.where)
condition2 = timesheet_df['Weekly OT Flag'] == 'Y'

timesheet_df['Weekly OT Hours'] = np.where(
    condition1,
    # All shift hours are OT if we've already exceeded 38 before this shift
    timesheet_df['Total TS Hours Adj'],
    np.where(
        condition2,
        # Part of this shift may push us over 38, so subtract the remaining non-OT hours
        timesheet_df['Total TS Hours Adj'] - (
            Max_Ord_Hrs - (timesheet_df['Roster Cumulative Hours'] - timesheet_df['Total TS Hours Adj'])
            #Max_Ord_Hrs - (timesheet_df['Roster Period Total Hours'] - timesheet_df['Total TS Hours Adj'])
        ),
        0
    )
)

# Ensure OT hours don't go negative
timesheet_df['Weekly OT Hours'] = timesheet_df['Weekly OT Hours'].clip(lower=0)




# First two hours will be on the weekly OT hours basis until told otherwise by CU or VU - 14.08.25
# Condition: weekly cumulative hours > 38 but <= 40



mask_first_2_ot = (
    (timesheet_df['Roster Period Total Hours'] > Max_Ord_Hrs) &
    (timesheet_df['Roster Period Total Hours'] <= First_2_Hrs_OT_Cutoff)
)

# Amount of shift hours that fall in the 38–40 window
first_2_hours_calc = np.minimum(
    timesheet_df['Total TS Hours Adj'],
    First_2_Hrs_OT_Cutoff - (timesheet_df['Roster Period Total Hours'] - timesheet_df['Total TS Hours Adj'])
)



# Step 2 – create pre-shift cumulative hours
timesheet_df['pre_shift_cumulative'] = (
    timesheet_df['Roster Period Total Hours'] - timesheet_df['Weekly OT Hours']
)



# # Step 1 – calculate candidate first 2 hours
# timesheet_df['OT First 2 Hours (Weekly)'] = np.where(
#     (timesheet_df['Weekly OT Flag'] == 'Y') & (timesheet_df['Sunday_Penality_flag'] == 'N'),
#     np.clip(timesheet_df['Weekly OT Hours'], 0, 2),
#     0
# )

timesheet_df['OT First 2 Hours (Weekly)'] = np.where(
    (timesheet_df['Roster Cumulative Hours'] > Max_Ord_Hrs) & 
    (timesheet_df['Sunday_Penality_flag'] == 'N') &
    (timesheet_df['Weekly OT Flag'] == 'Y') &
    ((timesheet_df['Roster Cumulative Hours'] - timesheet_df['Total TS Hours Adj']) <= Max_Ord_Hrs),
    2,
   np.clip(timesheet_df['Weekly OT Hours'], 0, 2)
)

timesheet_df['OT First 2 Hours (Daily)'] = np.where(
    (timesheet_df['Daily OT Flag'] == 'Y') &
    (timesheet_df['Sunday_Penality_flag'] == 'N') &
    (timesheet_df['Weekly OT Flag'] == 'N'),
    np.clip(timesheet_df['Daily OT Hours'], 0, 2),
    0
)



timesheet_df['OT Post 2 Hours (Weekly)'] = np.where(
    timesheet_df['Weekly OT Hours'] - timesheet_df['OT First 2 Hours (Weekly)'] > 0,
    timesheet_df['Weekly OT Hours'] - timesheet_df['OT First 2 Hours (Weekly)'],
    0

)

timesheet_df['OT Post 2 Hours (Daily)'] = np.where(
    timesheet_df['Daily OT Hours'] - timesheet_df['OT First 2 Hours (Daily)'] > 0,
    timesheet_df['Daily OT Hours'] - timesheet_df['OT First 2 Hours (Daily)'],
    0
)

# Add the Daily and Weekly OT first 2 hours and post 2 hours as there is no overlap

timesheet_df['OT First 2 Hours'] = timesheet_df['OT First 2 Hours (Weekly)'] + timesheet_df['OT First 2 Hours (Daily)']
timesheet_df['OT Post 2 Hours'] = timesheet_df['OT Post 2 Hours (Weekly)'] + timesheet_df['OT Post 2 Hours (Daily)']


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

timesheet_df['Total Day TS Hours'] = (
    timesheet_df.groupby(group_cols)['Day TS Hours']
    .transform('sum')
)





# Ratio of night shift hours
timesheet_df['Night Shift Ratio'] = (
    timesheet_df['Total Night TS Hours'] / (timesheet_df['Total Night TS Hours'] + timesheet_df['Total Day TS Hours'])
)
timesheet_df['Perm_Night_Ratio_Flag'] = np.where(
    timesheet_df['Night Shift Ratio'] > (2/3),
    'Y',
    'N'
)

timesheet_df = timesheet_df.drop_duplicates(subset=['Timesheet ID', 'Team member'])








# Use 10 hours for daily overtime 



#timesheet_df['OT200']


# Need to pull in the pay rates



payrates_df = pd.read_excel(r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\2025.08.19 - Employee classification & rate.xlsx", sheet_name='Staff List_FY level min rates')

# where employee ID matches and between data range,  pull in the relevant pay rates
# timesheet_df['Employee ID Consolidated'] and timseheet_df['Estimated Pay Date']


# --- Assumptions ---
# payrates_df has columns: ['Employee ID', 'Start Date', 'End Date', 'Rate_Hourly Day', ...]
# timesheet_df has columns: ['Employee ID Consolidated', 'Estimated Pay Date', ...]
# Dates are datetime dtype (if not, we’ll convert).

# Ensure dates are datetime
payrates_df['FY Starting'] = pd.to_datetime(payrates_df['FY Starting'])
payrates_df['FY Ending'] = pd.to_datetime(payrates_df['FY Ending'])
timesheet_df['Estimated Pay Date'] = pd.to_datetime(timesheet_df['Estimated Pay Date'])


# Ensure both Employee IDs are the same dtype
timesheet_df['Employee ID Consolidated'] = timesheet_df['Employee ID Consolidated'].astype(str).str.strip()
payrates_df['Employee ID'] = payrates_df['Employee ID'].astype(str).str.strip()


# pull in Allied Pay Rate	Award Pay Rate



# Select only the needed columns from payrates_df
payrates_subset = payrates_df[
    ['Employee ID', 'FY Starting', 'FY Ending', 
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


# columns to be used in dollar amount calculations
# Perm_Night_Ratio_Flag
# Saturday TS Hours
# Sunday TS Hours
# Day TS Hours
# Night TS Hours
# Total TS Hours
# Meal_Break_Deduction
# Total TS Hours Adj
# Weekly Total Hours
# Gap_to_Next_Shift_Hours
# Daily_Ordinary_Hours
# Daily OT Flag
# Weekly OT Flag
# Daily OT Hours
# Weekly OT Hours
# OT First 2 Hours
# OT Post 2 Hours
# Saturday_Penality_flag
# Sunday_Penality_flag
# Day adjustment
# Day TS Hours Adj
# Night TS Hours Adj



# Night Amount = Night TS Hours Adj * Award Night Pay Rate or Paid Night Pay Rate
timesheet_df['Night Amount'] = timesheet_df['Night TS Hours Adj'] * timesheet_df['Award Night Pay Rate']
timesheet_df['Day Amount'] = timesheet_df['Day TS Hours Adj'] * timesheet_df['Award Minimum Hourly Pay Rate']
timesheet_df['Saturday Amount'] = np.where(
    timesheet_df['Saturday_Penality_flag'] == 'Y',
    timesheet_df['Saturday TS Hours'] * timesheet_df['Award Saturday Pay Rate'],
    0
)
timesheet_df['Sunday Amount'] = np.where(
    timesheet_df['Sunday_Penality_flag'] == 'Y',
    timesheet_df['Sunday TS Hours'] * timesheet_df['Award Sunday Pay Rate'],
    0
)
timesheet_df['OT First 2 Hours Amount'] = timesheet_df['OT First 2 Hours'] * timesheet_df['Award Overtime First 2 Hours']
timesheet_df['OT Post 2 Hours Amount'] = timesheet_df['OT Post 2 Hours'] * timesheet_df['Award Overtime After 2 Hours']
timesheet_df['Total Amount'] = (
    timesheet_df['Night Amount'] +
    timesheet_df['Day Amount'] +
    timesheet_df['Saturday Amount'] +
    timesheet_df['Sunday Amount'] +
    timesheet_df['OT First 2 Hours Amount'] +
    timesheet_df['OT Post 2 Hours Amount']
)





columns_to_drop = [
    'First name',
'Last name',
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
'pre_shift_cumulative',
'Employee ID',
'FY Starting',
'FY Ending',
'Total Night TS Hours',
'Total Day TS Hours',
'Night Shift Ratio'


]


timesheet_df = timesheet_df.drop(columns=columns_to_drop)
# Reorder columns for better readability





column_order = [

    'Timesheet ID',
'Team member',
'Employee ID Consolidated',
'Timesheet Status',
'Timesheet Start Time',
'Timesheet End Time',
'TS_Start_Date',
'TS_End_Date',
'TS_TimeOnly_Start',
'TS_TimeOnly_End',
'Timesheet Total Time',
'Shift Start Time',
'Shift End Time',
'Shift Total Time',
'Timesheet location',
'Timesheet area',
'Timesheet leave policy',
'Timesheet Employee Comment',
'Difference in Hours',
'Weekday',
'Saturday_Penality_flag',
'Sunday_Penality_flag',
'Day TS Hours',
'Night TS Hours',
'Perm_Night_Ratio_Flag',
'Saturday TS Hours',
'Sunday TS Hours',
'Total TS Hours',
'Meal_Break_Deduction',
'Total TS Hours Adj',
'Week Number',
'Roster Starting',
'Roster Ending',
'Week Ending',
'Estimated Pay Date',
'Weekly Total Hours',
'Weekly Cumulative Hours',
'Roster Cumulative Hours',
'Roster Period Total Hours',
'Next_Start_dt',
'Gap_to_Next_Shift_Hours',
'Daily OT Flag',
'Weekly OT Flag',
'Daily OT Hours',
'Weekly OT Hours',
'OT First 2 Hours',
'OT Post 2 Hours',
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
# Reorder columns
timesheet_df = timesheet_df[column_order]


# Preview
print(timesheet_df[['TS_TimeOnly_Start', 'TS_TimeOnly_End', 'Difference in Hours', 'Night TS Hours', 'Day TS Hours']])
timesheet_df.to_excel("Timesheet_clean.xlsx", sheet_name='timesheet', index=False)













# Create new DF so we can group weekly by EMPLID and Pay Date rather than Roster Ending
timesheet_df_weekly_for_Leave = timesheet_df


# Step 3: Build EmpID_PayDay_Key (EmpID + Pay Date)
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



timesheet_df_weekly_for_Leave['EmpID_Week_Key'] = (
    timesheet_df_weekly_for_Leave['Employee ID Consolidated'].astype(str) + "_" +
    timesheet_df_weekly_for_Leave['Roster Ending'].dt.strftime("%Y-%m-%d") + "_W" +
    timesheet_df_weekly_for_Leave['Week Number'].astype(str)
)

print(timesheet_df_weekly_for_Leave['Week Number'].value_counts())

timesheet_df_weekly_for_Leave.to_csv('timesheet_df_weekly_for_Leave_preGroup.csv')

timesheet_df_weekly_for_Leave = timesheet_df_weekly_for_Leave.groupby('EmpID_Week_Key').agg({
    'EmpID_PayDay_Key' : 'first',
    'Employee ID Consolidated': 'first',
    'Estimated Pay Date': 'first',
    'Roster Starting': 'first',
    'Roster Ending': 'first',
    'Week Number': 'first',
    'Team member': 'first',
    'Day TS Hours': 'sum',
    # 'Timesheet Start Time', 'Timesheet End Time',
    #    'Timesheet Total Time', 'Shift Start Time', 'Shift End Time',
    #    'Shift Total Time', 'Timesheet location', 'Timesheet area',
       #'Timesheet leave policy', 'Timesheet Employee Comment',
       
       #'Timesheet Cost',
    #      'TS_Start_Date', 'TS_End_Date', 'TS_TimeOnly_Start',
    #    'TS_TimeOnly_End', 'Employee ID Consolidated', 'Difference in Hours',
       'Day TS Hours' : 'sum',
       'Night TS Hours' : 'sum', 
    #    'DOTW', 'Weekday',
    #    'Saturday_Penality_flag', 'Sunday_Penality_flag', 
       'Total TS Hours Adj' : 'sum',
       # 'Roster Ending' : 'first', 
      # 'Roster Period Total Hours' : 'first',

       #'rolling_1_weeks_hours', 
       #'Roster Ending (1w)' : 'last', 




       #'rolling_2_weeks_hours',
       #'Roster Ending (2w)' : 'last'



})

timesheet_df_weekly_for_Leave.to_csv('timesheet_df_weekly_for_Leave_preMerge.csv')

payroll_data = pd.read_excel(payroll_data)

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
#'Rate_Personal Salary',
#'Current_Personal Salary',
# 'Rate_Public Holiday Hourly',
# 'Current_Public Holiday Hourly',
# 'Rate_Public Holiday Not W...',
# 'Current_Public Holiday Not W...',
#'Rate_Salary',
#'Current_Salary',


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
'Rate_Annual Holiday Loadi...',
'Current_Annual Holiday Loadi...',
'Rate_Annual Leave',
'Current_Annual Leave',
'Rate_Holiday Hourly',
'Current_Holiday Hourly',
'Rate_Holiday Loading',
'Current_Holiday Loading',
'Rate_Holiday Salary',
'Current_Holiday Salary',
'Rate_Sick Leave Hourly',
'Current_Sick Leave Hourly',
'Rate_Sick Leave Salary',
'Current_Sick Leave Salary',

]

# Annual Leave QTY gets lost in data process due to be null. Create column using Rate and Current columns

# timesheet_df_weekly_for_Leave['Current_Annual Leave'] = (
#     timesheet_df_weekly_for_Leave['Current_Annual Leave']
#     .fillna(0)
#     .astype(float)
# )

# timesheet_df_weekly_for_Leave['Rate_Annual Leave'] = (
#     timesheet_df_weekly_for_Leave['Rate_Annual Leave']
#     .fillna(0)
#     .astype(float)
# )

# timesheet_df_weekly_for_Leave['Rate_Holiday Hourly'] = (
#     timesheet_df_weekly_for_Leave['Rate_Holiday Hourly']
#     .fillna(0)
#     .astype(float)
# )



# timesheet_df_weekly_for_Leave['Current_Holiday Hourly'] = (
#     timesheet_df_weekly_for_Leave['Current_Holiday Hourly']
#     .fillna(0)
#     .astype(float)
# )



# timesheet_df_weekly_for_Leave['Rate_Holiday Salary'] = (
#     timesheet_df_weekly_for_Leave['Rate_Holiday Salary']
#     .fillna(0)
#     .astype(float)
# )


# timesheet_df_weekly_for_Leave['Current_Holiday Salary'] = (
#     timesheet_df_weekly_for_Leave['Current_Holiday Salary']
#     .fillna(0)
#     .astype(float)
# )


# Can pick out leave loading here if we wish


# timesheet_df_weekly_for_Leave['Qty_Annual_Leave'] = timesheet_df_weekly_for_Leave['Current_Annual Leave'] / timesheet_df_weekly_for_Leave['Rate_Annual Leave']

# timesheet_df_weekly_for_Leave['Qty_Holiday Hourly'] = timesheet_df_weekly_for_Leave['Current_Holiday Hourly'] / timesheet_df_weekly_for_Leave['Rate_Holiday Hourly']

# timesheet_df_weekly_for_Leave['Qty_Holiday Salary'] = timesheet_df_weekly_for_Leave['Current_Holiday Salary'] / timesheet_df_weekly_for_Leave['Rate_Holiday Salary']


# Total Leave Hours = Qty_Holiday Salary + Qty_Holiday Hourly + Qty_Annual_Leave

timesheet_df_weekly_for_Leave['Total Leave Hours'] = timesheet_df_weekly_for_Leave['Qty_Holiday Salary'] + timesheet_df_weekly_for_Leave['Qty_Holiday Hourly'] + timesheet_df_weekly_for_Leave['Qty_Annual Leave'] 

timesheet_df_weekly_for_Leave['Total Leave Hours'] = (
    timesheet_df_weekly_for_Leave[['Qty_Holiday Salary', 'Qty_Holiday Hourly', 'Qty_Annual Leave']]
    .fillna(0)
    .sum(axis=1)
)

timesheet_df_weekly_for_Leave['Fortnight_Key'] = (
    timesheet_df_weekly_for_Leave['Employee ID Consolidated'].astype(str) + '_' +
    timesheet_df_weekly_for_Leave['Roster Ending'].astype(str)
)


def calculate_effective_hours(df):
    df = df.copy()
    
    # Step 1: Adjust leave if payout condition triggered
    df['Effective_Leave'] = np.where(
        (df['Total Leave Hours'] > 38) & (df['Total TS Hours Adj'] > 0),

        #(df['Total TS Hours Adj'] > 38) & (df['Total Leave Hours'] > 0),
        0,
        df['Total Leave Hours']
    )
    
    df['Effective_Total'] = df['Total TS Hours Adj'] + df['Effective_Leave']
    return df






def calculate_overtime(group):
    Max_Ord_Hrs = 76  # max ordinary hours for fortnight

    # Calculate fortnight total
    fortnight_total = group['Effective_Total'].sum()
    
    # Only show Fortnight_Total on Week 2
    group['Fortnight_Total'] = np.nan
    group.loc[group['Week Number'] == 2, 'Fortnight_Total'] = fortnight_total

    # Compute excess hours
    excess = max(fortnight_total - Max_Ord_Hrs, 0)

    # Keep original OT calculation intact
    group = group.sort_values('Week Number')
    ot = []
    for _, row in group.iterrows():
        if (row['Week Number'] == 2) and (row['Total TS Hours Adj'] == 0) and (row['Effective_Leave'] > 0):
            ot_hours = 0
        else:
            ot_hours = min(row['Total TS Hours Adj'], excess)
            excess -= ot_hours

        ot.append(ot_hours)

    # Cosmetic: shift OT to Week 2
    week2_idx = group[group['Week Number'] == 2].index
    if len(week2_idx) > 0:
        # Put all OT in the first Week 2 row
        group['Overtime_Hours'] = np.nan
        group.loc[week2_idx[0], 'Overtime_Hours'] = sum(ot)

    return group





# Apply per employee + roster cycle
timesheet_df_weekly_for_Leave = calculate_effective_hours(timesheet_df_weekly_for_Leave)
timesheet_df_weekly_for_Leave = timesheet_df_weekly_for_Leave.groupby(['Fortnight_Key','Roster Ending'], group_keys=False).apply(calculate_overtime)





# Drop only if the columns exist in your DataFrame
timesheet_df_weekly_for_Leave = timesheet_df_weekly_for_Leave.drop(columns=[col for col in columns_to_drop if col in timesheet_df_weekly_for_Leave.columns])



# 1 week roster so Weekly Ordinary Hours is 38 hours --



# timesheet_df['Weekly OT Flag'] = np.where(
#     timesheet_df['Roster Period Total Hours'] > Max_Ord_Hrs,
#     'Y',
#     'N'
# )

# # Condition: OT flag is Y and cumulative hours *before* this shift exceed 38
# condition1 = (timesheet_df_weekly_for_Leave['Overtime_Hours'] > 0) & \
#              ((timesheet_df_weekly_for_Leave['Roster Period Total Hours'] - timesheet_df_weekly_for_Leave['Total TS Hours Adj']) > Max_Ord_Hrs)

# # Condition: OT flag is Y (used in second np.where)
# condition2 = timesheet_df['Weekly OT Flag'] == 'Y'

# timesheet_df['Weekly OT Hours'] = np.where(
#     condition1,
#     # All shift hours are OT if we've already exceeded 38 before this shift
#     timesheet_df['Total TS Hours Adj'],
#     np.where(
#         condition2,
#         # Part of this shift may push us over 38, so subtract the remaining non-OT hours
#         timesheet_df['Total TS Hours Adj'] - (
#             Max_Ord_Hrs - (timesheet_df['Roster Period Total Hours'] - timesheet_df['Total TS Hours Adj'])
#         ),
#         0
#     )
# )

# # Ensure OT hours don't go negative
# timesheet_df['Weekly OT Hours'] = timesheet_df['Weekly OT Hours'].clip(lower=0)




# First two hours will be on the weekly OT hours basis until told otherwise by CU or VU - 14.08.25
# Condition: weekly cumulative hours > 38 but <= 40



mask_first_2_ot = (
    (timesheet_df_weekly_for_Leave['Fortnight_Total'] > Max_Ord_Hrs) &
    (timesheet_df_weekly_for_Leave['Fortnight_Total'] <= First_2_Hrs_OT_Cutoff)
)

# Amount of shift hours that fall in the 38–40 window
first_2_hours_calc = np.minimum(
    timesheet_df_weekly_for_Leave['Total TS Hours Adj'],
    First_2_Hrs_OT_Cutoff - (timesheet_df_weekly_for_Leave['Fortnight_Total'] - timesheet_df_weekly_for_Leave['Total TS Hours Adj'])
)


# 27/08/25  -  due to including leave in the OT calc we can't accurately determine whether the first 2 hour of overtime occured on a Sunday or not
# so we will exclude the Sunday penalty flag from the first 2 hours calc
# this may need to be revisited if CU or VU advise otherwise


# Step 1 – calculate candidate first 2 hours

timesheet_df_weekly_for_Leave['OT First 2 Hours'] = np.where(
    mask_first_2_ot,
    timesheet_df_weekly_for_Leave['Overtime_Hours'],
    np.where(timesheet_df_weekly_for_Leave['Overtime_Hours'] > 2, 2, 0
    )
)

# timesheet_df_weekly_for_Leave['OT First 2 Hours'] = np.where(
#     (timesheet_df_weekly_for_Leave['Overtime_Hours'] > 0) & 
#     (timesheet_df_weekly_for_Leave['Overtime_Hours'] < 2),
#     timesheet_df_weekly_for_Leave['Overtime_Hours'],
#     np.where(
#         mask_first_2_ot,
#         first_2_hours_calc,
#         0
#     )
# )


timesheet_df_weekly_for_Leave['OT Post 2 Hours'] = (
     timesheet_df_weekly_for_Leave['Overtime_Hours'] - timesheet_df_weekly_for_Leave['OT First 2 Hours']


)

# # Step 2 – create pre-shift cumulative hours
# timesheet_df['pre_shift_cumulative'] = (
#     timesheet_df['Roster Period Total Hours'] - timesheet_df['Weekly OT Hours']
# )

# # Step 3 – zero out if cumulative already ≥ 40 before the shift
# timesheet_df.loc[timesheet_df['pre_shift_cumulative'] >= First_2_Hrs_OT_Cutoff, 'OT First 2 Hours'] = 0

# # Step 4 – ensure only first occurrence in week gets the "first 2 hours"
# # Assuming you have a 'Week' column or can group by year-week
# timesheet_df['OT First 2 Hours'] = (
#     timesheet_df
#     .groupby(['Team member', 'Roster Ending'])['OT First 2 Hours']
#     .transform(lambda x: x.where(x.cumsum() <= 2, 0))
# )

# timesheet_df['OT Post 2 Hours'] = (
#     timesheet_df['Weekly OT Hours'] - timesheet_df['OT First 2 Hours']

# # )

# timesheet_df_weekly_for_Leave['Total Allied Weekly Pay'] = (
    
# (timesheet_df_weekly_for_Leave['Qty_Hourly Day'] * timesheet_df_weekly_for_Leave['Rate_Hourly Day']) +
# (timesheet_df_weekly_for_Leave['Qty_Hourly Night'] * timesheet_df_weekly_for_Leave['Rate_Hourly Night']) +
# (timesheet_df_weekly_for_Leave['Qty_Hourly Public Holiday'] * timesheet_df_weekly_for_Leave['Rate_Hourly Public Holiday']) +
# (timesheet_df_weekly_for_Leave['Qty_Hourly Saturday'] * timesheet_df_weekly_for_Leave['Rate_Hourly Saturday']) +
# (timesheet_df_weekly_for_Leave['Qty_Hourly Sunday'] * timesheet_df_weekly_for_Leave['Rate_Hourly Sunday']) +
# (timesheet_df_weekly_for_Leave['Qty_Personal Salary'] * timesheet_df_weekly_for_Leave['Rate_Personal Salary']) +
# (timesheet_df_weekly_for_Leave['Qty_Salary'] * timesheet_df_weekly_for_Leave['Rate_Salary'])
# )





pairs = [
    ('Qty_Hourly Day',            'Rate_Hourly Day'),
    ('Qty_Hourly Night',          'Rate_Hourly Night'),
    ('Qty_Hourly Public Holiday', 'Rate_Hourly Public Holiday'),
    ('Qty_Hourly Saturday',       'Rate_Hourly Saturday'),
    ('Qty_Hourly Sunday',         'Rate_Hourly Sunday'),
    ('Qty_Personal Salary',       'Rate_Personal Salary'),
    ('Qty_Salary',                'Rate_Salary'),
]

# Helper to coerce a column to numeric safely (handles $, commas, blanks)
def _num(series_or_scalar):
    if isinstance(series_or_scalar, pd.Series):
        s = series_or_scalar.astype(str).str.replace(r'[\$,]', '', regex=True)
        return pd.to_numeric(s, errors='coerce').fillna(0.0)
    else:
        # if the column doesn't exist and we got the default scalar 0
        return 0.0

# Start with a zero Series aligned to the DataFrame index
total = pd.Series(0.0, index=timesheet_df_weekly_for_Leave.index)

for qty_col, rate_col in pairs:
    q = _num(timesheet_df_weekly_for_Leave.get(qty_col, 0))
    r = _num(timesheet_df_weekly_for_Leave.get(rate_col, 0))
    total += q * r

timesheet_df_weekly_for_Leave['Total Allied Weekly Pay'] = total.round(2)






timesheet_df_weekly_for_Leave['Allied Above Award Day Rate (Min Rate)'] = (
    timesheet_df_weekly_for_Leave['Rate_Hourly Day']
    .replace(0, np.nan)              # treat 0 the same as NaN
    .ffill()                         # forward fill down
)




# timesheet_df_weekly_for_Leave['Allied Weekly Pay including Overtime'] = (

# (timesheet_df_weekly_for_Leave['OT First 2 Hours'] * timesheet_df_weekly_for_Leave['Allied Above Award Day Rate (Min Rate)']  * 1.5)
# + (timesheet_df_weekly_for_Leave['OT Post 2 Hours'] * timesheet_df_weekly_for_Leave['Allied Above Award Day Rate (Min Rate)']  * 2)


timesheet_df_weekly_for_Leave.to_csv('timesheet_df_weekly_for_Leave.csv')

