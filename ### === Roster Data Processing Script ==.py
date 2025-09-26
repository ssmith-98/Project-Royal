### === Roster Data Processing Script === ###
# This script processes a CSV file containing roster data,
# extracts relevant fields, and outputs a cleaned CSV file.

import pandas as pd
import numpy as np


Roster_file_path = r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Condensed Roster Data Transformed - Review Employees Only.xlsx"
timesheet_file_path = r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Timesheet detail 1 Nov 2023 to 30 June 2025.xlsx"
emplids_mapping = pd.read_excel(r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Employee IDs.xlsx", sheet_name='EMPLIDS')




def load_and_clean_Roster(file_path):
    # Load the Excel file
    df = pd.read_excel(file_path, sheet_name='Condensed', engine='openpyxl')

    # Drop completely empty columns
    df = df.dropna(axis=1, how='all')

    # Strip whitespace from string columns only
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.strip()

    # Convert Employee Number to integer safely
    df['Employee Number'] = pd.to_numeric(df['Employee Number'], errors='coerce').astype('Int64')

    # Convert date columns to datetime with dayfirst=True to ensure dd/mm/yyyy format
    df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce', dayfirst=True)
    df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce', dayfirst=True)

    # Convert time columns to datetime.time
    df['Start Time'] = pd.to_datetime(df['Start Time'], errors='coerce').dt.time
    df['End Time'] = pd.to_datetime(df['End Time'], errors='coerce').dt.time

    # Create Start DateTime and End DateTime
    df['Start DateTime'] = pd.to_datetime(df['Start Date'].astype(str) + ' ' + df['Start Time'].astype(str), errors='coerce')

    # Adjust End Date if shift crosses midnight
    df['End Date'] = df['Start Date']
    df.loc[df['Start Time'] > df['End Time'], 'End Date'] = df['Start Date'] + pd.Timedelta(days=1)

    df['End DateTime'] = pd.to_datetime(df['End Date'].astype(str) + ' ' + df['End Time'].astype(str), errors='coerce')

    # Drop rows with missing Start DateTime or Employee Number
    df = df[pd.notnull(df['Start DateTime']) & pd.notnull(df['Employee Number'])]

    # Generate unit_id using Employee ID + Start Date and End Date
    # df['unit_id'] = df.apply(
    #     lambda row: str(row['Employee Number']) + '_' + row['Start Date'].strftime('%Y%m%d') + '_' + row['End Date'].strftime('%Y%m%d')
    #     if pd.notnull(row['Start DateTime']) else None,
    #     axis=1
    # )

    # Amended Unit ID to match on datetime format
    df['unit_id'] = df.apply(
        lambda row: str(row['Employee Number']) + '_' + row['Start DateTime'].strftime('%Y-%m-%d %H:%M:%S') + '_' + row['End DateTime'].strftime('%Y-%m-%d %H:%M:%S')
        if pd.notnull(row['Start DateTime']) and pd.notnull(row['End DateTime']) else None,
        axis=1
    )
    return df






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


# Load data
timesheet_df = load_and_clean_timesheet(timesheet_file_path)
roster_df = load_and_clean_Roster(Roster_file_path)


roster_df['Total_Hours'] = (roster_df['End DateTime'] - roster_df['Start DateTime']).dt.total_seconds() / 3600.0




# Ensure datetime
roster_df['Start Date'] = pd.to_datetime(roster_df['Start Date'], errors='coerce')


# === Set your roster cycle anchor (a Monday that began a known roster fortnight) ===
CYCLE_ANCHOR = pd.Timestamp('2023-10-30')  # <- adjust to your real cycle start
if CYCLE_ANCHOR.weekday() != 0:
    raise ValueError("CYCLE_ANCHOR must be a Monday")

# Monday of the week that contains TS_Start_Date
monday_of_week = roster_df['Start Date'] - pd.to_timedelta(roster_df['Start Date'].dt.weekday, unit='D')

# Whole weeks since anchor
weeks_since_anchor = ((monday_of_week - CYCLE_ANCHOR) // pd.Timedelta(days=7)).astype(int)

# Roster week number: Week 1 (even), Week 2 (odd)
roster_df['Week Number'] = np.where(weeks_since_anchor % 2 == 0, 1, 2)

# Roster Starting = Monday of the Week 1 in this cycle
roster_df['Roster Starting'] = np.where(
    roster_df['Week Number'] == 1,
    monday_of_week,
    monday_of_week - pd.Timedelta(days=7)
)
roster_df['Roster Starting'] = pd.to_datetime(roster_df['Roster Starting'])

# Roster markers
roster_df['Week 1 Ending']   = roster_df['Roster Starting'] + pd.Timedelta(days=6)   # Sun of Week 1
roster_df['Week 2 Starting'] = roster_df['Roster Starting'] + pd.Timedelta(days=7)   # Mon of Week 2
roster_df['Roster Ending']   = roster_df['Roster Starting'] + pd.Timedelta(days=13)  # Sun of Week 2

# Per-row Week Ending (Sun)
roster_df['Week Ending'] = np.where(
    roster_df['Week Number'] == 1,
    roster_df['Week 1 Ending'],
    roster_df['Roster Ending']
)



roster_df.to_csv(r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Processed_Roster.csv", index=False)


emplids_mapping['Team member'] = emplids_mapping['Team member'].astype(str)

# Merge to get Employee ID Consolidated
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

# Drop rows where Team member is 'Anthony Knight' as not in consent list
timesheet_df = timesheet_df[timesheet_df['Team member'] != 'Anthony Knight']

# Drop rows where Team member is 'Grahame Corbett' as Salary not shift worker
timesheet_df = timesheet_df[timesheet_df['Team member'] != 'Grahame Corbett']


# (Optional) Reset the index if you want a clean index after dropping
timesheet_df = timesheet_df.reset_index(drop=True)


timesheet_df['unit_id'] = timesheet_df.apply(
        lambda row: str(row['Employee ID Consolidated']) + '_' + row['Timesheet Start Time'].strftime('%Y-%m-%d %H:%M:%S') + '_' + row['Timesheet End Time'].strftime('%Y-%m-%d %H:%M:%S')
        if pd.notnull(row['Timesheet Start Time']) else None,
        axis=1
    )




# Create relaxed keys
timesheet_df['relaxed_key'] = timesheet_df['Employee ID Consolidated'].astype(str) + '_' + timesheet_df['Timesheet Start Time'].dt.date.astype(str)
roster_df['relaxed_key'] = roster_df['Employee Number'].astype(str) + '_' + roster_df['Start DateTime'].dt.date.astype(str)



merged_df = timesheet_df.merge(
    roster_df,
    on='unit_id',
    how='left',
    suffixes=('_timesheet', '_roster')
)



merged_df['Shift_Match'] = np.where(
    (merged_df['TS_TimeOnly_Start'] == merged_df['Start Time']) &
    (merged_df['TS_TimeOnly_End'] == merged_df['End Time']),
    'Yes', 'No'
)





# Calculate Timesheet hours
merged_df['Timesheet_Hours'] = (merged_df['Timesheet End Time'] - merged_df['Timesheet Start Time']).dt.total_seconds() / 3600.0

# Calculate Roster hours
merged_df['Roster_Hours'] = (merged_df['End DateTime'] - merged_df['Start DateTime']).dt.total_seconds() / 3600.0

# Calculate the difference
merged_df['Hours_Difference'] = merged_df['Timesheet_Hours'] - merged_df['Roster_Hours']


merged_df['relaxed_key'] = timesheet_df['relaxed_key']

unmatched_df = merged_df[merged_df['Start DateTime'].isna()]


# Merge unmatched rows using relaxed key
second_merge = unmatched_df.merge(
    roster_df[['relaxed_key', 'Start DateTime', 'End DateTime']],  # include only necessary columns
    left_on='relaxed_key',
    right_on='relaxed_key',
    how='left'
)

# Calculate Roster hours
second_merge['Roster_Hours_2'] = (second_merge['End DateTime_y'] - second_merge['Start DateTime_y']).dt.total_seconds() / 3600.0


second_merge.to_csv(r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Second_Merge_Unmatched.csv", index=False)


part_time_employees = [543, 41, 356, 429]

parttime_df = second_merge[second_merge['Employee ID Consolidated'].astype(int).isin(part_time_employees)]

parttime_df['Hours_Difference'] = parttime_df['Timesheet_Hours'] - parttime_df['Roster_Hours_2']


# Drop rows where Hours_Difference is negative
parttime_df = parttime_df[parttime_df['Hours_Difference'] >= 0]

parttime_df['Hours_Difference'] = parttime_df['Hours_Difference'].round(2)

columns_to_keep = [
    'Timesheet ID',
    'Team member',
    'Employee ID Consolidated',
    'Timesheet Start Time',
    'Timesheet End Time',
    'Timesheet_Hours',
    'Start DateTime_y',
    'Start DateTime_y',
    'Roster_Hours_2',
    'Hours_Difference'
]

parttime_df = parttime_df[columns_to_keep]


parttime_df.drop_duplicates(inplace=True)

parttime_df.to_csv(r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Parttime_Employees_Unmatched.csv", index=False)

# Flag part-time OT
timesheet_df['part_time_OT'] = np.where(
    timesheet_df['Timesheet ID'].isin(parttime_df['Timesheet ID']),
    'Yes', 
    'No'
)

hours_diff_map = (
    parttime_df.groupby('Timesheet ID')['Hours_Difference']
    .sum()   # or .mean(), .max(), etc.
)

timesheet_df['part_time_OT_hours'] = (
    timesheet_df['Timesheet ID'].map(hours_diff_map).fillna(0)
)

timesheet_df.drop_duplicates(inplace=True)


timesheet_df.to_csv(r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Processed_Timesheet.csv", index=False)


Timesheet_with_Roster = timesheet_df.merge(
    roster_df,
    on='unit_id',
    how='left',
    suffixes=('_timesheet', '_roster')
)

Timesheet_with_Roster['Comments_Roster'] = Timesheet_with_Roster['Comments']


columns_to_keep = [
    'Timesheet ID',
    'Team member',
    'Employee ID Consolidated',
    'Timesheet Start Time',
    'Timesheet End Time',
    'Start DateTime',
    'End DateTime',
    'part_time_OT',
    'part_time_OT_hours',
    'Timesheet ID',
    'Team member',
    'Timesheet Status',
    'Timesheet Start Time',
    'Timesheet End Time',
    'Timesheet Total Time',
    'Shift Start Time',
    'Shift End Time',
    'Shift Total Time',
    'Diff',
    'Timesheet location',
    'Timesheet area',
    'Timesheet leave policy',
    'Timesheet Employee Comment',
    'Comments_Roster',
    'Timesheet Cost',
    'TS_Start_Date',
    'TS_End_Date',
    'TS_TimeOnly_Start',
    'TS_TimeOnly_End',
    'Employee ID Consolidated',
    'part_time_OT',
    'part_time_OT_hours',
    'Location',
    'Employee Name',
    'Employee Number',
    'Start DateTime',
    'End DateTime',
    'Total_Hours'
]

Timesheet_with_Roster = Timesheet_with_Roster[columns_to_keep]

Timesheet_with_Roster.to_csv(r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Timesheet_with_Roster.csv", index=False)

















# sort by Employee and Start DateTime
merged_df = merged_df.sort_values(by=['Employee ID Consolidated', 'Timesheet Start Time'])


day_mapping = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7}  # Monday=1, Sunday=7

# # Create the DOTW column and apply the mapping
merged_df['DOTW'] = merged_df['Timesheet Start Time'].dt.weekday.map(day_mapping)
# Included Endshift to cover nightshift hours that go into Sat or Sunday
merged_df['DOTW_ENDShift'] = merged_df['Timesheet End Time'].dt.weekday.map(day_mapping)
# Custom numeric mapping: Saturday = 1, Sunday = 2, ..., Friday = 7
# Add Day of the Week as text (e.g. Monday, Tuesday, etc.)
merged_df['Weekday'] = pd.to_datetime(merged_df['TS_Start_Date']).dt.day_name()




# Ensure datetime
merged_df['TS_Start_Date'] = pd.to_datetime(merged_df['TS_Start_Date'], errors='coerce')


# === Set your roster cycle anchor (a Monday that began a known roster fortnight) ===
CYCLE_ANCHOR = pd.Timestamp('2023-10-30')  # <- adjust to your real cycle start
if CYCLE_ANCHOR.weekday() != 0:
    raise ValueError("CYCLE_ANCHOR must be a Monday")

# Monday of the week that contains TS_Start_Date
monday_of_week = merged_df['TS_Start_Date'] - pd.to_timedelta(merged_df['TS_Start_Date'].dt.weekday, unit='D')

# Whole weeks since anchor
weeks_since_anchor = ((monday_of_week - CYCLE_ANCHOR) // pd.Timedelta(days=7)).astype(int)

# Roster week number: Week 1 (even), Week 2 (odd)
merged_df['Week Number'] = np.where(weeks_since_anchor % 2 == 0, 1, 2)

# Roster Starting = Monday of the Week 1 in this cycle
merged_df['Roster Starting'] = np.where(
    merged_df['Week Number'] == 1,
    monday_of_week,
    monday_of_week - pd.Timedelta(days=7)
)
merged_df['Roster Starting'] = pd.to_datetime(merged_df['Roster Starting'])

# Roster markers
merged_df['Week 1 Ending']   = merged_df['Roster Starting'] + pd.Timedelta(days=6)   # Sun of Week 1
merged_df['Week 2 Starting'] = merged_df['Roster Starting'] + pd.Timedelta(days=7)   # Mon of Week 2
merged_df['Roster Ending']   = merged_df['Roster Starting'] + pd.Timedelta(days=13)  # Sun of Week 2

# Per-row Week Ending (Sun)
merged_df['Week Ending'] = np.where(
    merged_df['Week Number'] == 1,
    merged_df['Week 1 Ending'],
    merged_df['Roster Ending']
)



merged_df.to_csv(r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Processed_Timesheet_Roster_Merged.csv", index=False)

condensed_comparison = merged_df


condensed_comparison['EmpID_Week_Key'] = (
    condensed_comparison['Employee ID Consolidated'].astype(str) + "_" +
    condensed_comparison['Roster Ending'].dt.strftime("%Y-%m-%d") + "_W" +
    condensed_comparison['Week Number'].astype(str)
)



agg_dict = {
    # identifiers / dates (use first_nonnull)
    'Timesheet ID' : 'first',
    'Employee ID Consolidated': 'first',
    'Team member': 'first',
    'Week Ending': 'first',
    # numeric columns (sum them up)
    'Timesheet_Hours': 'sum',
    'Roster_Hours': 'sum'
   
    
}

condensed_comparison = (
    condensed_comparison
      .groupby('EmpID_Week_Key', as_index=False)
      .agg(agg_dict)
)

# Calculate the difference
condensed_comparison['Hours_Difference'] = condensed_comparison['Timesheet_Hours'] - condensed_comparison['Roster_Hours']
condensed_comparison = condensed_comparison.sort_values(by=['Employee ID Consolidated', 'Week Ending'])

condensed_comparison.to_csv(r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Condensed_Timesheet_Roster_Comparison.csv", index=False)