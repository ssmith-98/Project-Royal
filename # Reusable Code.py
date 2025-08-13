# Reusable Code

# Code Snippets we need
import pandas as pd
import numpy as np

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

# Save cleaned file
timesheet_df.to_excel("Timesheet_clean.xlsx", sheet_name='timesheet', index=False)





# Step 1: Add `DOTW` (Day of the Week) where Saturday is 1 and Friday is 7
# Step 1: Map days of the week using the desired mapping
day_mapping = {0: 3, 1: 4, 2: 5, 3: 6, 4: 7, 5: 1, 6: 2}

# Create the DOTW column and apply the mapping
timesheet_df['DOTW'] = timesheet_df['TS_Start_Date'].dt.weekday.map(day_mapping)


# Span Hours



# Step 2: Calculate `cal_ot_span_weekend_hours`
timesheet_df['cal_ot_span_weekend_hours'] = np.where(
    (timesheet_df['DOTW'] < 3),  # Saturday or Sunday
    timesheet_df['Timesheet Total Time'],  # Return total_hours if conditions met
    0  # Otherwise, set to 0
)

# Helper function to calculate the time difference in hours
def calculate_time_difference_in_hours(start_time, rule_time):
    datetime_start = pd.to_datetime(start_time, format='%H:%M:%S')
    datetime_rule = pd.to_datetime(rule_time, format='%H:%M:%S')
    time_difference = (datetime_start - datetime_rule).total_seconds()  # Subtract start from rule for positive time
    return time_difference / 3600  # Convert seconds to hours

# Step 1: Update cal_ot_span_as_hours
timesheet_df['cal_ot_span_as_hours'] = np.where(
    
    (timesheet_df['DOTW'] > 2)  # Weekday: Monday-Friday
    (timesheet_df['datetime_endwork'].dt.time > timesheet_df['Rule - less than time']) &  # Time comparison
    (~timesheet_df['Grade-Step OR Course Code'].str.contains('L8|L9|L10', na=False)),  # Exclude L8, L9, L10
    # Calculate the difference in hours (positive subtraction)
    timesheet_df.apply(lambda row: calculate_time_difference_in_hours(row['datetime_endwork'].time(), row['Rule - less than time']), axis=1),
    np.where(
        (timesheet_df['DATE WORKED'] > comparison_date) &  # Condition for DATE WORKED
        (timesheet_df['Exclude weekends'] == 'n') &  # Exclude weekends == 'n'
        (timesheet_df['datetime_endwork'].dt.time > timesheet_df['Rule - less than time']) &  # Time comparison
        (~timesheet_df['Grade-Step OR Course Code'].str.contains('L8|L9|L10', na=False)),  # Exclude L8, L9, L10
        # Calculate the difference in hours (positive subtraction)
        timesheet_df.apply(lambda row: calculate_time_difference_in_hours(row['datetime_endwork'].time(), row['Rule - less than time']), axis=1),
        0  # Set to 0 if no conditions met
    )
)
print('step 3 done')
# Step 2: Cap cal_ot_span_as_hours to total_hours
timesheet_df['cal_ot_span_as_hours'] = np.where(
    timesheet_df['cal_ot_span_as_hours'] > timesheet_df['total_hours'],
    timesheet_df['total_hours'],  # Cap at total_hours
    timesheet_df['cal_ot_span_as_hours']  # Otherwise keep the calculated value
)
print('step 4 done')
# Step 3: Update cal_ot_span_bs_hours
timesheet_df['cal_ot_span_bs_hours'] = np.where(
    (timesheet_df['DATE WORKED'] > comparison_date) &  # Condition for DATE WORKED
    (timesheet_df['DOTW'] > 2) &  # Weekday: Monday-Friday
    (timesheet_df['Exclude weekends'] == 'y') &  # Exclude weekends == 'y'
    (timesheet_df['datetime_startwork'].dt.time < timesheet_df['Rule - greater than time']) &  # Time comparison
    (~timesheet_df['Grade-Step OR Course Code'].str.contains('L8|L9|L10', na=False)),  # Exclude L8, L9, L10
    # Calculate the difference in hours
    timesheet_df.apply(lambda row: calculate_time_difference_in_hours(row['Rule - greater than time'], row['datetime_startwork'].time()), axis=1),
    np.where(
        (timesheet_df['DATE WORKED'] > comparison_date) &  # Condition for DATE WORKED
        (timesheet_df['Exclude weekends'] == 'n') &  # Exclude weekends == 'n'
        (timesheet_df['datetime_startwork'].dt.time < timesheet_df['Rule - greater than time']) &  # Time comparison
        (~timesheet_df['Grade-Step OR Course Code'].str.contains('L8|L9|L10', na=False)),  # Exclude L8, L9, L10
        # Calculate the difference in hours
        timesheet_df.apply(lambda row: calculate_time_difference_in_hours(row['Rule - greater than time'], row['datetime_startwork'].time()), axis=1),
        0  # Set to 0 if no conditions met
    )
)

print('step 5 done')
# Step 4: Cap cal_ot_span_bs_hours to total_hours
timesheet_df['cal_ot_span_bs_hours'] = np.where(
    timesheet_df['cal_ot_span_bs_hours'] > timesheet_df['total_hours'],
    timesheet_df['total_hours'],  # Cap at total_hours
    timesheet_df['cal_ot_span_bs_hours']  # Otherwise keep the calculated value
)

print('step 6 done')

if test_on == 1:
    # Step 1: Filter transactions where 'DATE WORKED' > 22/11/2023
    sample_test = timesheet_df[
        timesheet_df['DATE WORKED'] > comparison_date
    ]

    # Step 2: Output the filtered rows to an Excel file
    sample_test_file = os.path.join(output_tests, 'sample_test_transactions_after_22_11_2023_span.xlsx')
    sample_test.to_excel(sample_test_file, index=False)

    print(f"Sample test saved to {sample_test_file}")
else:
    print("Test is turned off. Skipping sample test for transactions after 22/11/2023.")

print('step 7 done')

# Step 11: Output the final table to Parquet and Excel
timesheet_df.to_parquet(output_cleaned_data + 'timesheet_df.parquet', index=False)
timesheet_df.head(2000).to_excel(output_cleaned_data + 'timesheet_df_sample.xlsx', index=False)
print("Final table saved to Parquet and Excel.")


















# # OT - 1	Daily Overtime


# #Ordinary hours worked above 10 each day are treated as Overtime hours (OT) unless by agreement with the majority of affected employees 
# # at a particular establishment, an employee may be rostered to work up to 12 ordinary hours per shift.    
# #  An agreement under clause 13.3(c) must be recorded in writing and kept by the employer as a time and wages record.



# # # DAILY CALCULATION
# # # Step 4: Create a conditional cumulative sum of total hours for daily thresholds
# # # Use groupby on EMPLID and the date part of datetime_startwork to get daily cumulative total hours


# Will have to create our own tag for OT

df['Destinated OT'] = np.where(
    df['daily_hours'] >
)




# daily hours count 




# need two because unclear if 10 or 12 hours is agreed as oridnary hours

df['Destinated OT 10 hours'] = np.where(
    df['daily_hrs_count'] > 10,
    df['daily_hrs_count'] - 10,
    0
)


df['Destinated OT 12 hours'] = np.where(
    df['daily_hrs_count'] > 12,
    df['daily_hrs_count'] - 12,
    0
)






# Apply the conditional logic: If PIN_NM equals 0 then adjusted_daily_hours = total_hours otherwise calculate as before
df['adjusted_daily_hours'] = np.where(
    df['PIN_NM'] == 'OT',
    0,
    df['total_hours'] - 
    df['cal_ot_span_weekend_hours'] - 
    df['cal_ot_span_as_hours'] - 
    df['cal_ot_span_bs_hours']
)

# !!!! Need to understand the purpose of Span hours !!!


# Step 5: Apply cumsum() on the adjusted hours for daily thresholds
df['daily_hrs_count'] = df.groupby(
    ['EMPLID', 'date_only']
)['adjusted_daily_hours'].cumsum()


# Step 5: Create the new field cal_daily_ot_hours (where daily_hrs_count > 10)
df['cal_daily_ot_hours'] = np.where(
    df['daily_hrs_count'] > 10,
    df['daily_hrs_count'] - 10,
    0
)

# Step 6: Calculate incremental daily OT hours
# Group by EMPLID and date, and subtract the prior row's cal_daily_ot_hours to get the incremental increase
df['incremental_daily_ot_hours'] = df.groupby(
    ['EMPLID', 'date_only']
)['cal_daily_ot_hours'].diff().fillna(df['cal_daily_ot_hours'])




# # OT - 2	Weekly Overtime


# # WEEKLY CALCULATION


# # Step 1: Ensure 'datetime_startwork' is in datetime format if not already
# df['datetime_startwork'] = pd.to_datetime(df['datetime_startwork'])

# # Step 2: Determine the week start date (Saturday) for each transaction
# # If DOTW == 1 (Saturday), it's the start of the week. Subtract DOTW - 1 to get the start of the week.
# df['week_start_date'] = df['datetime_startwork'] - pd.to_timedelta(
#     df['DOTW'] - 1, unit='D'
# )

# # Step 3: Create a unique week ID by concatenating 'EMPLID' and the 'week_start_date'
# # This will act as the unique identifier for each employee's work week
# df['EMPLID_week_id'] = (
#     df['EMPLID'].astype(str) + '_' + df['week_start_date'].dt.strftime('%Y-%m-%d')
# )

# # # Step 4: Calculate the weekly cumulative sum of total hours using 'EMPLID_week_id'
# # # We group by 'EMPLID_week_id' to ensure the cumulative sum is calculated within the same week for each employee
# # df['weekly_hrs_count'] = df.groupby('EMPLID_week_id')['total_hours'].cumsum()



# # Revised code for Step 4 Weekly Calc - Query DQ11
# # Apply the conditional logic: If PIN_NM equals 0 then adjusted_daily_hours = total_hours otherwise calculate as before
# df['adjusted_weekly_hours'] = np.where(
#     df['PIN_NM'] == 'OT',
#     0,
#     df['total_hours'] - 
#     df['cal_ot_span_weekend_hours'] - 
#     df['cal_ot_span_as_hours'] - 
#     df['cal_ot_span_bs_hours'] -
#     df['incremental_daily_ot_hours']
# )








# # Step 5: Apply cumsum() on the adjusted hours for weekly thresholds
# df['weekly_hrs_count'] = df.groupby('EMPLID_week_id')[
#     'adjusted_weekly_hours'
# ].cumsum()




# # Might need to create weekly overtime amounts for 1, 2,3,4 and 8 weeks. But the rosters are on a 1 week cycle 

# # Where a roster is operated the average of 38 Ordinary hours per week  may be worked in any of the following ways:
# # 76 hours over a roster cycle of up to 2 weeks;
# # 114 hours over a roster cycle of up to 3 weeks;
# # 152 hours over a roster cycle of up to 4 weeks; 
# # 304 hours over a roster cycle of up to 8 weeks. 


# # Step 5: Create the new field cal_weekly_ot_hours where the weekly cumulative hours exceed the threshold (38 hours)
# df['cal_weekly_ot_hours'] = np.where(
#     df['weekly_hrs_count'] > 38,
#     df['weekly_hrs_count'] - 38,
#     0
# )

# # Step 6: Calculate incremental weekly OT hours
# # Group by EMPLID_week_id, and subtract the prior row's cal_weekly_ot_hours to get the incremental increase
# df['incremental_weekly_ot_hours'] = df.groupby(
#     ['EMPLID_week_id']
# )['cal_weekly_ot_hours'].diff().fillna(df['cal_weekly_ot_hours'])


# # Step 7: Calculate cal_OT_hours as the sum of all overtime fields
# df['cal_OT_hours'] = (
#     df['incremental_daily_ot_hours'] +
#     df['incremental_weekly_ot_hours'] +
#     df['cal_ot_span_weekend_hours'] +
#     df['cal_ot_span_as_hours'] +
#     df['cal_ot_span_bs_hours']
# )










# # OT - 3	First two hours Overtime
# # Step 4: Logic for the first 3 OT hours
# df['cal_first_3_ot'] = np.select(
#     [
#         df['cummulative_cal_OT_hours'] <= 3,
#         (df['cummulative_cal_OT_hours'] > 3) & (df['prior_cummulative_cal_OT_hours'] > 3),
#         (df['cummulative_cal_OT_hours'] > 3) & (df['prior_cummulative_cal_OT_hours'] < 3)
#     ],
#     [
#         df['cummulative_cal_OT_hours'] - df['prior_cummulative_cal_OT_hours'],
#         0,
#         3 - df['prior_cummulative_cal_OT_hours']
#     ],
#     default=0
# )







# # OT - 4	Overtime after the first two hours



# # New Field: cal_post_3_ot
# # Step 5: Calculate post-3 OT hours for non-Sundays
# df['cal_post_3_ot'] = np.where(
#     (df['DOTW'] != 2) & (df['Holiday'] == 'Not a Holiday'),
#     df['cal_OT_hours'] - df['cal_first_3_ot'],
#     0
# )





# # OT - 5	Overtime on a Sunday

# # New Field: cal_sunday_ot
# # Step 1: Set `cal_sunday_ot` where DOTW == 2 (Sunday)
# df['cal_sunday_ot'] = np.where(
#     df['DOTW'] == 2,
#     df['cal_OT_hours'],
#     0
# )





# # OT - 6	Overtime on a Public Holiday



# # New Field: cal_PH_ot
# # Step 1: Set `cal_PH_ot` where Holiday != Not a Holiday
# df['cal_PH_ot'] = np.where(
#     df['Holiday'] != 'Not a Holiday',
#     df['cal_OT_hours'],
#     0
# )




# # OT - 7	Restriction on amount of overtime






# # WP - 1	Penality rates inside span of hours

# # Calculate Ordinary Hours

# # Ordinary hours worked between 6.00 to 18:00 Monday to Friday (excluding Public Holiday) is paid at 100%



# # WP - 2	Penality rates outside span of hours (Night Shift)

# # Ordinary hours worked between 0:00 - 06:00 and 18:00 - 23:59 (excluding Public Holiday) are paid at 121.7% of minimum hourly rate.  unless the employee is on permanent night work then it is 130% of minimum hourly rate. 
# # An employee is on permanent night work over the whole period of a roster cycle if more than two-thirds of the employee’s ordinary shifts comprise or include the period between midnight and 6.00 am.



# # WP - 3	Saturday Penality


# # New Field: cal_wknd_penalty_sat
# # Step 6: Calculate weekend penalty for Saturday (DOTW == 1, Rule - Weekend Penalty == 'y', and DATE WORKED >= Rule - greater than date)
# df['cal_wknd_penalty_sat'] = np.where(
#     (df['DOTW'] == 1) &
#     (df['Rule - Weekend Penalty'] == 'y') &
#     (df['DATE WORKED'] >= df['Rule - greater than date']),
#     df['total_hours'] - df['cal_OT_hours'],
#     0
# )


# # WP - 4	Sunday Penality


# # New Field: cal_wknd_penalty_sun
# # Step 7: Calculate weekend penalty for Sunday (DOTW == 2, Rule - Weekend Penalty == 'y', and DATE WORKED >= Rule - greater than date)
# df['cal_wknd_penalty_sun'] = np.where(
#     (df['DOTW'] == 2) &
#     (df['Rule - Weekend Penalty'] == 'y') &
#     (df['DATE WORKED'] >= df['Rule - greater than date']),
#     df['total_hours'] - df['cal_OT_hours'],
#     0
# )







# # WP - 5	Public Holiday Penality

# # Reset cumulative OT to 0 where it's Sunday or a public holiday
# df['cummulative_OT_hours'] = np.where(
#     (df['DOTW'] == 2) |
#     (df['Holiday'] != 'Not a Holiday'),
#     0,
#     df['cummulative_OT_hours']
# )








	
# # 	Broken Shift Minimum 3 Hours


# # Step 1: Create the "minimum_hours" column
# timesheet_min_top_up_cals['minimum_hours'] = np.where(
#     (timesheet_min_top_up_cals['POSITION_NBR'] == '1085.0') & (timesheet_min_top_up_cals['Acad/Prof'] != 'ACAD'),
#     2,  # If POSITION_NBR == '1085' and Acad/Prof is not 'ACAD', set minimum_hours to 2
#     np.where(
#         (timesheet_min_top_up_cals['Acad/Prof'] == 'ACAD') | 
#         (timesheet_min_top_up_cals['is_student']) | 
#         (timesheet_min_top_up_cals['is_perm']),  # If either Acad/Prof is 'ACAD', is_student is True, or is_perm is True
#         1,  # Set minimum_hours to 1
#         3   # Otherwise, set minimum_hours to 3
#     )
# )






# # Step 2: Calculate the gap between shifts (gap_hours) only when Start_null or End_null is FALSE
# # Get the previous shift's end time within the same EMPLID and date_only
# timesheet_min_top_up_cals['gap_hours'] = timesheet_min_top_up_cals.groupby(['EMPLID'])['datetime_endwork'].shift(1)

# # Only calculate gaps where:
# # 1. Both the current and previous rows have valid start and end times (Start_null == False, End_null == False)
# # 2. The EMPLID and date_only are the same between the current and previous rows
# timesheet_min_top_up_cals['gap_hours'] = np.where(
#     (timesheet_min_top_up_cals['Start_null'] == False) &
#     (timesheet_min_top_up_cals['End_null'].shift(1) == False) &
#     (timesheet_min_top_up_cals['EMPLID'] == timesheet_min_top_up_cals['EMPLID'].shift(1)),  # Ensure same EMPLID
#     (timesheet_min_top_up_cals['datetime_startwork'] - timesheet_min_top_up_cals['datetime_endwork'].shift(1)).dt.total_seconds() / 3600,
#     np.nan  # Set gap to NaN where we don't have valid start or end times or EMPLID/date_only changes
# )



# # Output a sample of gap_hours for testing
# sample_gap_hours = timesheet_min_top_up_cals[['EMPLID', 'date_only', 'datetime_startwork', 'datetime_endwork', 'gap_hours']].head(200)
# sample_gap_hours_output = os.path.join(output_tests, 'sample_gap_hours.xlsx')
# sample_gap_hours.to_excel(sample_gap_hours_output, index=False)
# print(f"Step 2 completed: 'gap_hours' sample saved to {sample_gap_hours_output}")


# # Step 3: Create a conditional cumulative sum of total_hours, resetting when gap_hours > 0
# def conditional_cumsum(df):
#     # Create a column for cumulative sum
#     cumsum = []
#     running_sum = 0

#     for i, row in df.iterrows():
#         # Reset cumulative sum if gap_hours is greater than 0 or NaN (i.e. first shift of the day)
#         if row['gap_hours'] > 0 or pd.isna(row['gap_hours']):
#             running_sum = row['total_hours']
#         else:
#             running_sum += row['total_hours']

#         cumsum.append(running_sum)

#     return pd.Series(cumsum, index=df.index)


# # Apply the function to each group (by EMPLID and date_only)
# timesheet_min_top_up_cals['conseq_cumul_sumhrs'] = timesheet_min_top_up_cals.groupby(['EMPLID', 'date_only']).apply(
#     conditional_cumsum, include_groups=True).reset_index(drop=True)

# # Output a sample to verify the results
# #Paul's file path
# #sample_cumul_sumhrs_output = r'C:\Users\zhump\Documents\Data Analytics\Project Daylight\Outputs\Tests'
# # Sam's file path
# sample_cumul_sumhrs_output = r'C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Project Daylight\Outputs\Tests\sample_conseq_cumul_sumhrs.xlsx'
# timesheet_min_top_up_cals[['EMPLID', 'date_only', 'total_hours', 'gap_hours', 'conseq_cumul_sumhrs']].head(
#     200).to_excel(sample_cumul_sumhrs_output, index=False)
# print(f"'conseq_cumul_sumhrs' sample saved to {sample_cumul_sumhrs_output}")




# # Step 4: Create EMPLID_date_only key
# timesheet_min_top_up_cals['EMPLID_date_only'] = timesheet_min_top_up_cals['EMPLID'].astype(str) + '_' + timesheet_min_top_up_cals['date_only'].astype(str)

# # Step 2: Identify EMPLID and date_only combinations for ex_1_3hrs_day
# three_hour_shifts = []

# for i in range(len(timesheet_min_top_up_cals) - 1):
#     current_row = timesheet_min_top_up_cals.iloc[i]
#     next_row = timesheet_min_top_up_cals.iloc[i + 1]

#     # Condition 1: Shift with cumulative hours >= 3 on the same day
#     if current_row['conseq_cumul_sumhrs'] >= 3:
#         three_hour_shifts.append((current_row['EMPLID'], current_row['date_only']))

#     # Condition 2: Midnight-end shift, with a consecutive shift that adds up to >= 3 hours
#     elif (
#         current_row['datetime_endwork'].time() == pd.Timestamp('00:00:00').time() and
#         current_row['EMPLID'] == next_row['EMPLID'] and
#         current_row['date_only'] == next_row['date_only'] and
#         next_row['gap_hours'] == 0 and
#         (current_row['total_hours'] + next_row['total_hours']) >= 3
#     ):
#         three_hour_shifts.append((current_row['EMPLID'], current_row['date_only']))

# # Convert list to a set of unique (EMPLID, date_only) combinations
# three_hour_shifts = set(three_hour_shifts)

# # Step 3: Flag ex_1_3hrs_day based on identified (EMPLID, date_only) combinations
# timesheet_min_top_up_cals['ex_1_3hrs_day'] = timesheet_min_top_up_cals.apply(
#     lambda row: (row['EMPLID'], row['date_only']) in three_hour_shifts, axis=1
# )

# # Output a sample to verify the results
# sample_3hrs_day_output = os.path.join(output_tests, 'sample_ex_1_3hrs_day_updated.xlsx')
# timesheet_min_top_up_cals[['EMPLID', 'date_only', 'datetime_startwork', 'datetime_endwork', 'conseq_cumul_sumhrs', 'ex_1_3hrs_day']].head(200).to_excel(sample_3hrs_day_output, index=False)
# print(f"Updated 'ex_1_3hrs_day' sample saved to {sample_3hrs_day_output}")

















# # BK - 1	Paid Rest Breaks
# # BK - 2	Breaks between work periods
# # BK - 3	Long Breaks
# # BK - 4	Meal Breaks
# # AL - 1 	Leave Loading























# # Helper function to convert 12-hour time to 24-hour format
# def convert_to_24_hour(hour, minute, am_pm):
#     # Handle NaNs by setting them to 0 and flagging the issue
#     if pd.isna(hour) or pd.isna(minute) or pd.isna(am_pm):
#         return '00:00:00'

#     hour = int(hour) if pd.notna(hour) else 0  # Convert to integer or set to 0 if NaN
#     minute = int(minute) if pd.notna(minute) else 0  # Convert to integer or set to 0 if NaN

#     if am_pm == 'P' and hour != 12:
#         hour += 12
#     if am_pm == 'A' and hour == 12:
#         hour = 0
#     return f'{hour:02d}:{minute:02d}:00'



# # Step 12: Calculate total hours worked, only if Start_null and End_null are both False
# timesheet_cas_filtered_rules['total_hours'] = np.where(
#     (~timesheet_cas_filtered_rules['Start_null'] & ~timesheet_cas_filtered_rules['End_null']),  # Condition
#     (timesheet_cas_filtered_rules['datetime_endwork'] - timesheet_cas_filtered_rules['datetime_startwork']).dt.total_seconds() / 3600
#     - (timesheet_cas_filtered_rules['G_BREAK_MINUTES'] / 60),  # Calculate total hours if condition is True
#     timesheet_cas_filtered_rules['UNITS_CLAIMED']  # Otherwise, set total_hours to UNITS_CLAIMED
# )



#   # Filter rows where UNITS_CLAIMED is not approximately equal to total_hours
#     test_units_claimed = timesheet_cas_filtered_rules[
#         abs(timesheet_cas_filtered_rules['UNITS_CLAIMED'] - timesheet_cas_filtered_rules['total_hours']) > margin_of_error
#     ]




# pin_nm_list = ['CASUAL', 'OT', 'CALLBACK', 'SHIFT100', 'SHIFT50', 'SHIFT150', 'SATCASUAL', 'SUNCASUAL', 'SHIFT15', 'CASUAL-ORD']


# # Step 1a: Create columns for each PIN_NM value


# for pin_nm in pin_nm_list:
#     timesheet_cas_filtered_rules[f'{pin_nm}_hours'] = np.where(
#         timesheet_cas_filtered_rules['PIN_NM'] == pin_nm,  # Condition
#         timesheet_cas_filtered_rules['total_hours'],  # Set total_hours if PIN_NM matches
#         0  # Otherwise, set it to 0
#     )




# # Step 1: Add `DOTW` (Day of the Week) where Saturday is 1 and Friday is 7
# # Step 1: Map days of the week using the desired mapping
# day_mapping = {0: 3, 1: 4, 2: 5, 3: 6, 4: 7, 5: 1, 6: 2}

# # Create the DOTW column and apply the mapping
# timesheet_cas_filtered_rules['DOTW'] = timesheet_cas_filtered_rules['DATE WORKED'].dt.weekday.map(day_mapping)




# print('step 3 done')
# # Step 2: Cap cal_ot_span_as_hours to total_hours
# timesheet_df['cal_ot_span_as_hours'] = np.where(
#     timesheet_df['cal_ot_span_as_hours'] > timesheet_df['total_hours'],
#     timesheet_df['total_hours'],  # Cap at total_hours
#     timesheet_df['cal_ot_span_as_hours']  # Otherwise keep the calculated value
# )



# # Calculating Ordinary Hours


# ### 'rules - less than time' is the cut off point for Daily Oridnary Hours
# ### ''Rule - greater than time' is the starting point for Daily Oridnary Hours

# ### the below can be simplified massively



# print('step 2 done')
# # Helper function to calculate the time difference in hours
# def calculate_time_difference_in_hours(start_time, rule_time):
#     datetime_start = pd.to_datetime(start_time, format='%H:%M:%S')
#     datetime_rule = pd.to_datetime(rule_time, format='%H:%M:%S')
#     time_difference = (datetime_start - datetime_rule).total_seconds()  # Subtract start from rule for positive time
#     return time_difference / 3600  # Convert seconds to hours

# # Step 1: Update cal_ot_span_as_hours
# timesheet_df['cal_ot_span_as_hours'] = np.where(
#     (timesheet_df['DATE WORKED'] > comparison_date) &  # Condition for DATE WORKED
#     (timesheet_df['DOTW'] > 2) &  # Weekday: Monday-Friday
#     (timesheet_df['Exclude weekends'] == 'y') &  # Exclude weekends == 'y'
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
