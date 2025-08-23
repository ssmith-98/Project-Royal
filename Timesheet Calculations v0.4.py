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



# Need to add shift count feature per day so that we can calculate the below pay rule: 
# Broken Shift Minimum 3 Hours	  
# An employee who works broken shifts is entitled to be paid for at least 3 hours for each period of duty on a broken shift even if the employee works for a shorter time.

# Pivot table seems to indicate that broken shifts exist 














# Step 1: Calculate total shift hours
timesheet_df['Total Shift Hours'] = timesheet_df['Night Shift Hours'] + timesheet_df['Day Shift Hours']

# Step 2: Ensure TS_Start_Date is datetime
timesheet_df['TS_Start_Date'] = pd.to_datetime(timesheet_df['TS_Start_Date'])



# 1 Week Ending (Sunday)
# timesheet_df['Roster Ending'] = timesheet_df['TS_Start_Date'] + pd.to_timedelta(
#     6 - timesheet_df['TS_Start_Date'].dt.weekday, unit='d'
# )



# 2 Weeks Ending (Sunday)
timesheet_df['Roster Ending'] = timesheet_df['TS_Start_Date'] + pd.to_timedelta(
    13 - timesheet_df['TS_Start_Date'].dt.weekday, unit='d'
)

# 2 Weeks Starting (Monday)
timesheet_df['Roster Starting'] = timesheet_df['Roster Ending'] - pd.Timedelta(days=13)


# Week 1 Ending (Sunday of week 1)
timesheet_df['Week 1 Ending'] = timesheet_df['Roster Starting'] + pd.Timedelta(days=6)

# Week 2 Starting (Monday of week 2)
timesheet_df['Week 2 Starting'] = timesheet_df['Week 1 Ending'] + pd.Timedelta(days=1)


# Step 1: Always move forward to the Wednesday after Week 1 Ending
timesheet_df['Estimated Pay Date'] = timesheet_df['Week 1 Ending'] + pd.to_timedelta(
    (2 - timesheet_df['Week 1 Ending'].dt.weekday + 7) % 7, unit="d"
)

# Step 2: Apply Tuesday exceptions (move back 1 day)
exceptions = [pd.Timestamp('2024-12-24'), pd.Timestamp('2024-12-31')]
timesheet_df.loc[timesheet_df['Estimated Pay Date'].isin(exceptions), 'Estimated Pay Date'] -= pd.Timedelta(days=1)





timesheet_df['TS_Start_Date'] = timesheet_df['Timesheet Start Time'].dt.date


# Aggregate weekly totals per team member
weekly_df = timesheet_df.groupby(['Team member', 'Roster Ending'], as_index=False)['Total Shift Hours'].sum()
weekly_df.rename(columns={'Total Shift Hours': 'weekly total hours'}, inplace=True)
weekly_df = weekly_df.sort_values(['Team member', 'Roster Ending'])


# Step 4: Group by Team Member and Roster Ending, then sum total shift hours 
timesheet_df['Roster Period Cumulative Total Hours'] = timesheet_df.groupby( ['Employee ID Consolidated', 'Roster Ending'] )['Total Shift Hours'].transform('cumsum')






#Function to calculate rolling totals for any week window
def add_rolling_weeks(df, weeks=4):
    df = df.sort_values(['Team member', 'Roster Ending'])
    df[f'rolling_{weeks}_weeks_hours'] = (
        df.groupby('Team member')['weekly total hours']
          .rolling(window=weeks, min_periods=1)
          .sum()
          .reset_index(level=0, drop=True)
    )
    df[f'Roster Ending ({weeks}w)'] = df['Roster Ending']
    return df

# Example: 2, 3, 4, 8-week rolling totals
# Commented out due to 1 week roster being used
#for w in [1, 2, 3, 4, 8]:
for w in [1, 2]:
    weekly_df = add_rolling_weeks(weekly_df, weeks=w)

# Optional: merge rolling totals back to original timesheet_df if needed
timesheet_df = timesheet_df.merge(
    weekly_df.drop(columns=['weekly total hours']),
    on=['Team member', 'Roster Ending'],
    how='left'
)



# Create 'EmpID_key'
timesheet_df['EmpID_key'] = timesheet_df['Employee ID Consolidated'].astype(str) + '_' + timesheet_df['Roster Ending (1w)'].astype(str)

print('columns as per line 235')
print(timesheet_df.columns)


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





timesheet_df_weekly_for_Leave = timesheet_df_weekly_for_Leave.groupby('EmpID_key').agg({
    'EmpID_PayDay_Key' : 'first',
    'Estimated Pay Date' : 'first',
    'Roster Ending' : 'first',
    'Roster Starting' : 'first',
    'Week 1 Ending' : 'first',
    'Week 2 Starting' : 'first',
    'Team member' : 'first', 
    # 'Timesheet Start Time', 'Timesheet End Time',
    #    'Timesheet Total Time', 'Shift Start Time', 'Shift End Time',
    #    'Shift Total Time', 'Timesheet location', 'Timesheet area',
       #'Timesheet leave policy', 'Timesheet Employee Comment',
       
       #'Timesheet Cost',
    #      'TS_Start_Date', 'TS_End_Date', 'TS_TimeOnly_Start',
    #    'TS_TimeOnly_End', 'Employee ID Consolidated', 'Difference in Hours',
       'Day Shift Hours' : 'sum',
       'Night Shift Hours' : 'sum', 
    #    'DOTW', 'Weekday',
    #    'Saturday_Penality_flag', 'Sunday_Penality_flag', 
       'Total Shift Hours' : 'sum',
       # 'Roster Ending' : 'first', 
      # 'Roster Period Cumulative Total Hours' : 'first',

       #'rolling_1_weeks_hours', 
       'Roster Ending (1w)' : 'last', 




       #'rolling_2_weeks_hours',
       #'Roster Ending (2w)' : 'last'



})

payroll_data = pd.read_excel(payroll_data)

timesheet_df_weekly_for_Leave = timesheet_df_weekly_for_Leave.merge(payroll_data,
                                   on=['EmpID_PayDay_Key'],
                                   how='left')


# Drop unneed columns and keep only Leave related ones

columns_to_drop = [
    'Rate_BACK PAY',
'Current_BACK PAY',
'Rate_Bereavement',
'Current_Bereavement',
'Rate_Extra Payment',
'Qty_Extra Payment',
'Current_Extra Payment',
'Rate_First Aid Allowance',
'Qty_First Aid Allowance',
'Current_First Aid Allowance',
'Current_Gross Pay',
'Rate_Hourly Day',
'Current_Hourly Day',
'Rate_Hourly Night',
'Current_Hourly Night',
'Rate_Hourly Public Holiday',
'Current_Hourly Public Holiday',
'Rate_Hourly Saturday',
'Current_Hourly Saturday',
'Rate_Hourly Sunday',
'Current_Hourly Sunday',
'Rate_Net Pay',
'Qty_Net Pay',
'Current_Net Pay',
'Rate_PAYG Tax',
'Qty_PAYG Tax',
'Current_PAYG Tax',
'Rate_Personal Hourly',
'Current_Personal Hourly',
'Rate_Personal Salary',
'Current_Personal Salary',
'Rate_Public Holiday Hourly',
'Current_Public Holiday Hourly',
'Rate_Public Holiday Not W...',
'Current_Public Holiday Not W...',
'Current_Reimbursement',
'Rate_Salary',
'Current_Salary',
'Rate_Sick Leave Hourly',
'Current_Sick Leave Hourly',
'Rate_Sick Leave Salary',
'Current_Sick Leave Salary',
'Rate_Super',
'Qty_Super',
'Current_Super',
'Rate_Supervisor Allowance',
'Qty_Supervisor Allowance',
'Current_Supervisor Allowance',
'Rate_Annual Holiday Loadi...',
'Current_Annual Holiday Loadi...',
'Rate_Annual Leave',
'Current_Annual Leave',
'Rate_Holiday Hourly',
'Current_Holiday Hourly',
'Rate_Holiday Loading',
'Current_Holiday Loading',
'Rate_Holiday Salary',
'Current_Holiday Salary'

]

# Annual Leave QTY gets lost in data process due to be null. Create column using Rate and Current columns

timesheet_df_weekly_for_Leave['Current_Annual Leave'] = (
    timesheet_df_weekly_for_Leave['Current_Annual Leave']
    .fillna(0)
    .astype(float)
)

timesheet_df_weekly_for_Leave['Rate_Annual Leave'] = (
    timesheet_df_weekly_for_Leave['Rate_Annual Leave']
    .fillna(0)
    .astype(float)
)

timesheet_df_weekly_for_Leave['Rate_Holiday Hourly'] = (
    timesheet_df_weekly_for_Leave['Rate_Holiday Hourly']
    .fillna(0)
    .astype(float)
)



timesheet_df_weekly_for_Leave['Current_Holiday Hourly'] = (
    timesheet_df_weekly_for_Leave['Current_Holiday Hourly']
    .fillna(0)
    .astype(float)
)



timesheet_df_weekly_for_Leave['Rate_Holiday Salary'] = (
    timesheet_df_weekly_for_Leave['Rate_Holiday Salary']
    .fillna(0)
    .astype(float)
)


timesheet_df_weekly_for_Leave['Current_Holiday Salary'] = (
    timesheet_df_weekly_for_Leave['Current_Holiday Salary']
    .fillna(0)
    .astype(float)
)


# Can pick out leave loading here if we wish


timesheet_df_weekly_for_Leave['Qty_Annual_Leave'] = timesheet_df_weekly_for_Leave['Current_Annual Leave'] / timesheet_df_weekly_for_Leave['Rate_Annual Leave']

timesheet_df_weekly_for_Leave['Qty_Holiday Hourly'] = timesheet_df_weekly_for_Leave['Current_Holiday Hourly'] / timesheet_df_weekly_for_Leave['Rate_Holiday Hourly']

timesheet_df_weekly_for_Leave['Qty_Holiday Salary'] = timesheet_df_weekly_for_Leave['Current_Holiday Salary'] / timesheet_df_weekly_for_Leave['Rate_Holiday Salary']


 #timesheet_df_weekly_for_Leave['Total Leave Hours'] = timesheet_df_weekly_for_Leave['Qty_Holiday Salary'] + timesheet_df_weekly_for_Leave['Qty_Holiday Hourly'] + timesheet_df_weekly_for_Leave['Qty_Annual_Leave'] 

timesheet_df_weekly_for_Leave['Total Leave Hours'] = (
    timesheet_df_weekly_for_Leave[['Qty_Holiday Salary', 'Qty_Holiday Hourly', 'Qty_Annual_Leave']]
    .fillna(0)
    .sum(axis=1)
)

# Drop only if the columns exist in your DataFrame
timesheet_df_weekly_for_Leave = timesheet_df_weekly_for_Leave.drop(columns=[col for col in columns_to_drop if col in timesheet_df_weekly_for_Leave.columns])







timesheet_df_weekly_for_Leave.to_csv('timesheet_df_weekly_for_Leave.csv')

# Ensure date columns are datetime.date and time columns are datetime.time

# timesheet_df['TS_TimeOnly_Start'] = pd.to_datetime(timesheet_df['TS_TimeOnly_Start'], format='%H:%M:%S').dt.time
# timesheet_df['TS_TimeOnly_End'] = pd.to_datetime(timesheet_df['TS_TimeOnly_End'], format='%H:%M:%S').dt.time

# Create full datetime columns using combine
timesheet_df['Start_dt'] = timesheet_df.apply(
    lambda row: pd.Timestamp.combine(row['TS_Start_Date'], row['TS_TimeOnly_Start']), axis=1
)
timesheet_df['End_dt'] = timesheet_df.apply(
    lambda row: pd.Timestamp.combine(row['TS_End_Date'], row['TS_TimeOnly_End']), axis=1
)


# Sort by employee and start datetime


timesheet_df = timesheet_df.sort_values(by=['Employee ID Consolidated', 'Shift Start Time']).reset_index(drop=True)


timesheet_df = timesheet_df.drop_duplicates(
    subset=['Employee ID Consolidated', 'Shift Start Time']
).sort_values(
    by=['Employee ID Consolidated', 'Shift Start Time']
).reset_index(drop=True)

timesheet_df['Next_Start_dt'] = (
    timesheet_df.groupby('Employee ID Consolidated')['Shift Start Time'].shift(-1)
)


# Calculate gap in hours between current end and next start
timesheet_df['Gap_to_Next_Shift_Hours'] = (
    (timesheet_df['Next_Start_dt'] - timesheet_df['End_dt']).dt.total_seconds() / 3600
)

# Optional: filter or flag gaps
# timesheet_df['Flag_Short_Gap'] = timesheet_df['Gap_to_Next_Shift_Hours'] < 12

# Display or export
print(timesheet_df[['Employee ID Consolidated', 'Start_dt', 'End_dt', 'Gap_to_Next_Shift_Hours']])


timesheet_df['Daily_Ordinary_Hours'] = 7.6





# 1 week roster so Weekly Ordinary Hours is 38 hours --


Max_Ord_Hrs = 76
First_2_Hrs_OT_Cutoff = 78

timesheet_df['Weekly OT Flag'] = np.where(
    timesheet_df['Roster Period Cumulative Total Hours'] > Max_Ord_Hrs,
    'Y',
    'N'
)

# Condition: OT flag is Y and cumulative hours *before* this shift exceed 38
condition1 = (timesheet_df['Weekly OT Flag'] == 'Y') & \
             ((timesheet_df['Roster Period Cumulative Total Hours'] - timesheet_df['Total Shift Hours']) > Max_Ord_Hrs)

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
            Max_Ord_Hrs - (timesheet_df['Roster Period Cumulative Total Hours'] - timesheet_df['Total Shift Hours'])
        ),
        0
    )
)

# Ensure OT hours don't go negative
timesheet_df['Weekly OT Hours'] = timesheet_df['Weekly OT Hours'].clip(lower=0)




# First two hours will be on the weekly OT hours basis until told otherwise by CU or VU - 14.08.25
# Condition: weekly cumulative hours > 38 but <= 40



mask_first_2_ot = (
    (timesheet_df['Roster Period Cumulative Total Hours'] > Max_Ord_Hrs) &
    (timesheet_df['Roster Period Cumulative Total Hours'] <= First_2_Hrs_OT_Cutoff)
)

# Amount of shift hours that fall in the 38–40 window
first_2_hours_calc = np.minimum(
    timesheet_df['Total Shift Hours'],
    First_2_Hrs_OT_Cutoff - (timesheet_df['Roster Period Cumulative Total Hours'] - timesheet_df['Total Shift Hours'])
)



# Step 1 – calculate candidate first 2 hours
timesheet_df['OT First 2 Hours'] = np.where(
    (timesheet_df['Weekly OT Flag'] == 'Y') & (timesheet_df['Sunday_Penality_flag'] == 'N'),
    np.clip(timesheet_df['Weekly OT Hours'], 0, 2),
    0
)

# Step 2 – create pre-shift cumulative hours
timesheet_df['pre_shift_cumulative'] = (
    timesheet_df['Roster Period Cumulative Total Hours'] - timesheet_df['Weekly OT Hours']
)

# Step 3 – zero out if cumulative already ≥ 40 before the shift
timesheet_df.loc[timesheet_df['pre_shift_cumulative'] >= First_2_Hrs_OT_Cutoff, 'OT First 2 Hours'] = 0

# Step 4 – ensure only first occurrence in week gets the "first 2 hours"
# Assuming you have a 'Week' column or can group by year-week
timesheet_df['OT First 2 Hours'] = (
    timesheet_df
    .groupby(['Team member', 'Roster Ending'])['OT First 2 Hours']
    .transform(lambda x: x.where(x.cumsum() <= 2, 0))
)

timesheet_df['OT Post 2 Hours'] = (
    timesheet_df['Weekly OT Hours'] - timesheet_df['OT First 2 Hours']

)

timesheet_df = timesheet_df.drop_duplicates(subset=['Timesheet ID', 'Team member'])


# Use 10 hours for daily overtime 



#timesheet_df['OT200']



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