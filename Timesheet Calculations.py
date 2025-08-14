
# Code Snippets we need
import pandas as pd
import numpy as np
from datetime import time
from datetime import datetime, time, timedelta


timesheet_file_path = r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Timesheet detail 1 Nov 2023 to 30 June 2025.xlsx"

def load_and_clean_timesheet(file_path):
    # Load worksheet
    df1 = pd.read_excel(file_path, sheet_name='Timesheet details')

    # Remove completely empty columns
    df1_cleaned = df1.dropna(axis=1, how='all')

    # Data type conversions
    df1_cleaned['Timesheet ID'] = df1_cleaned['Timesheet ID'].astype(int)

    datetime_cols = [
        'Timesheet Start Time',
        'Timesheet End Time',
        'Shift Start Time',
        'Shift End Time'
    ]
    for col in datetime_cols:
        df1_cleaned[col] = pd.to_datetime(df1_cleaned[col], errors='coerce')

    # Create derived columns
    df1_cleaned['TS_Start_Date'] = df1_cleaned['Timesheet Start Time'].dt.date
    df1_cleaned['TS_End_Date'] = df1_cleaned['Timesheet End Time'].dt.date
    df1_cleaned['TS_TimeOnly_Start'] = df1_cleaned['Timesheet Start Time'].dt.time
    df1_cleaned['TS_TimeOnly_End'] = df1_cleaned['Timesheet End Time'].dt.time  # adjusted

    return df1_cleaned

timesheet_df = load_and_clean_timesheet(timesheet_file_path)






# Step 1: Add `DOTW` (Day of the Week) where Saturday is 1 and Friday is 7
# Step 1: Map days of the week using the desired mapping
# day_mapping = {0: 3, 1: 4, 2: 5, 3: 6, 4: 7, 5: 1, 6: 2}

# # Create the DOTW column and apply the mapping
# timesheet_df['DOTW'] = timesheet_df['TS_Start_Date'].dt.weekday.map(day_mapping)


# Ordinary Hours
# Daily Ordinary Hours


# Helper function to calculate the time difference in hours
def calculate_time_difference_in_hours(date_series, time_series_start, time_series_end):
    start_dt = pd.to_datetime(date_series.astype(str) + ' ' + time_series_start.astype(str), errors='coerce')
    end_dt = pd.to_datetime(date_series.astype(str) + ' ' + time_series_end.astype(str), errors='coerce')

    # Handle night shifts — if end is earlier than start, add 1 day
    end_dt = end_dt.where(end_dt >= start_dt, end_dt + pd.Timedelta(days=1))

    return (end_dt - start_dt).dt.total_seconds() / 3600



timesheet_df['Difference in Hours'] = calculate_time_difference_in_hours(
    timesheet_df['TS_Start_Date'],
    timesheet_df['TS_TimeOnly_Start'],
    timesheet_df['TS_TimeOnly_End']
)




start_dates = pd.to_datetime(timesheet_df['TS_Start_Date'])
end_dates = pd.to_datetime(timesheet_df['TS_End_Date'])

(end_dates - start_dates).dt.days



# Convert back to datetime64[ns] before doing .dt operations
start_dates = pd.to_datetime(timesheet_df['TS_Start_Date'])
end_dates = pd.to_datetime(timesheet_df['TS_End_Date'])







def calculate_night_shift_hours(start_time, end_time):
    night_start = time(18, 0)
    night_end = time(6, 0)

    start_dt = datetime.combine(datetime.today(), start_time)
    end_dt = datetime.combine(datetime.today(), end_time)

    # Handle overnight shifts
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)

    total_night_hours = 0
    current_time = start_dt

    while current_time < end_dt:
        current_hour = current_time.time()
        if current_hour >= night_start or current_hour < night_end:
            total_night_hours += 1
        current_time += timedelta(hours=1)

    return total_night_hours

# Apply the function to each row
timesheet_df['Night Shift Hours'] = timesheet_df.apply(
    lambda row: calculate_night_shift_hours(row['TS_TimeOnly_Start'], row['TS_TimeOnly_End']),
    axis=1
)



import pandas as pd
from datetime import datetime, time, timedelta

# Example DataFrame (replace with your actual data)
timesheet_df = pd.DataFrame({
    'TS_TimeOnly_Start': [time(17, 0), time(19, 0), time(23, 0), time(5, 0)],
    'TS_TimeOnly_End': [time(19, 0), time(23, 0), time(5, 0), time(7, 0)],
    'TS_Start_Date': [datetime(2023, 1, 1)] * 4
})

def calculate_shift_hours(start_time, end_time, shift_start, shift_end):
    start_dt = datetime.combine(datetime.today(), start_time)
    end_dt = datetime.combine(datetime.today(), end_time)

    # Handle overnight shifts
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

# Apply functions for night and day shifts
timesheet_df['Night Shift Hours'] = timesheet_df.apply(
    lambda row: calculate_shift_hours(row['TS_TimeOnly_Start'], row['TS_TimeOnly_End'], time(18, 0), time(6, 0)),
    axis=1
)

timesheet_df['Day Shift Hours'] = timesheet_df.apply(
    lambda row: calculate_shift_hours(row['TS_TimeOnly_Start'], row['TS_TimeOnly_End'], time(6, 0), time(18, 0)),
    axis=1
)




# Cumsum daily hours

# timesheet_df['daily_hrs_count'] = timesheet_df.groupby(
# ['Team member', 'TS_Start_Date'])['Timesheet Total Time'].cumsum()





# timesheet_df['Daily Ordinary Hours'] = np.where(
    
#     (timesheet_df['DOTW'] > 2)  # Weekday: Monday-Friday
#     (timesheet_df['datetime_endwork'].dt.time > timesheet_df['Rule - less than time']) &  # Time comparison
#     (~timesheet_df['Grade-Step OR Course Code'].str.contains('L8|L9|L10', na=False)),  # Exclude L8, L9, L10
#     # Calculate the difference in hours (positive subtraction)
#     timesheet_df.apply(lambda row: calculate_time_difference_in_hours(row['datetime_endwork'].time(), row['Rule - less than time']), axis=1),
#     np.where(
#         (timesheet_df['DATE WORKED'] > comparison_date) &  # Condition for DATE WORKED
#         (timesheet_df['Exclude weekends'] == 'n') &  # Exclude weekends == 'n'
#         (timesheet_df['datetime_endwork'].dt.time > timesheet_df['Rule - less than time']) &  # Time comparison
#         (~timesheet_df['Grade-Step OR Course Code'].str.contains('L8|L9|L10', na=False)),  # Exclude L8, L9, L10
#         # Calculate the difference in hours (positive subtraction)
#         timesheet_df.apply(lambda row: calculate_time_difference_in_hours(row['datetime_endwork'].time(), row['Rule - less than time']), axis=1),
#         0  # Set to 0 if no conditions met
#     )
# )



# Save cleaned file
timesheet_df.to_excel("Timesheet_clean.xlsx", sheet_name='timesheet', index=False)
