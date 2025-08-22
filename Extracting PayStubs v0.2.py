import pandas as pd
import numpy as np
import re
from datetime import time

import os

# File path for testing, later we will use the folder

# paystub_test_filepath = r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Files Provided by DB 20 July 25\PayStubs Excel\ANUJ BHALLA 1.xlsx"

# import pandas as pd

# # ---------- Step 1: Load data ----------
# # Replace with your file path and sheet name if Excel
# df = pd.read_excel(paystub_test_filepath, sheet_name="Sheet1")

# # ---------- Step 2+: Power Query step equivalents ----------


# -*- coding: utf-8 -*-
"""
Replicates the full Power Query pipeline in pandas (fast + vectorised).

PQ steps covered:
  1. Load Excel, promote headers
  2. Change types (lightly), remove blank rows
  3. Add EmployeeNumber from the next row after "Employee No."
  4. Rename columns
  5. Extract Pay Date (and fill down)
  6. Extract Super Pay Date
  7. Add MatchFound ("Employer Contributions")
  8. Add SuperFundName (row after MatchFound)
  9. Add ContributionAmount (next row's Column8 when current row is "Employer Contributions" & Column8 == "Current")
 10. Fill down SuperFundName
 11. Rename "Anuj A Bhalla" -> "Earnings and Hours"
 12. Fast vectorised "next row" check to set "Super" for missing E&H when next row is "Taxes"
 13. Update "Current" when E&H == "Super"
 14. Fill down ContributionAmount
 15. Final update to "Current" for Super rows
 16. Drop extra columns

Author: (you + ChatGPT)
"""






def process_payroll_data(directory, sheet_name="Sheet1"):
    """
    Reads and processes payroll data from multiple Excel files in the given directory.

    Args:
        directory (str): Path to the directory containing payroll Excel files.
        sheet_name (str): Name of the sheet to read from each Excel file.

    Returns:
        pd.DataFrame: Combined payroll data from all files.
    """
    all_years_pay = pd.DataFrame()

    # List all Excel files in the directory
    files = [file for file in os.listdir(directory) if file.endswith('.xlsx')]

    for file in files:
        file_path = os.path.join(directory, file)
        try:
            temp_df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
            temp_df['Source File'] = file  # Optional: track source file
            all_years_pay = pd.concat([all_years_pay, temp_df], ignore_index=True)
        except Exception as e:
            print(f"Error reading {file}: {e}")

    return all_years_pay









# ------------- CONFIG -------------
INPUT_PATH  = r"C:/Users/smits/OneDrive - SW Accountants & Advisors Pty Ltd\Desktop/Client Projects/Project Royal/Files Provided by DB 20 July 25/PayStubs Excel/all staff - Excel (Word to Excel)/"




#r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Files Provided by DB 20 July 25\PayStubs Excel\ANUJ BHALLA 1.xlsx"



# r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Files Provided by DB 20 July 25\Collated data\B1.xlsx"
SHEET_NAME  = "Sheet1"
OUTPUT_PATH = r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Payroll_Output.xlsx"
OUTPUT_PATH_1 = r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Super_Output.xlsx"




# ----------------------------------





def _to_str(x):
    """Safe string cast; returns '' for NaN/None."""
    if pd.isna(x):
        return ""
    return str(x)

def _extract_date_after_key(text, key):
    """
    Extracts the first token after 'key' and parses as date (AU format).
    E.g., "... Pay Date: 1/07/2023 ..." -> 2023-07-01
    """
    s = _to_str(text)
    if not key.lower() in s.lower():
        return pd.NaT
    # get substring after the key (case-insensitive)
    try:
        # split once on key (ignore case)
        # simple approach: find index ignoring case
        idx = s.lower().find(key.lower())
        after = s[idx + len(key):]
        after = after.strip()
        # first token
        token = after.split()[0] if after else ""
        if not token:
            return pd.NaT
        # parse with AU day-first
        dt = pd.to_datetime(token, dayfirst=True, errors="coerce")
        return dt
    except Exception:
        return pd.NaT

# ------------- STEP 1: Load -------------
# Headers are promoted by default with read_excel.
df = process_payroll_data(INPUT_PATH)

print("columns")
print(df.columns)


df.to_excel('test123.xlsx')

#pd.read_excel(INPUT_PATH, sheet_name=SHEET_NAME, header=None)



df = df.iloc[:, :10]  # Keep only the first 10 columns
df.columns = [
    'Earnings and Hours', 'Column2', 'Column3', 'Column4', 'Column5',
    'Column6', 'Column7', 'Column8', 'Column9', 'Source File'
]

# df.columns = [
#     "Earnings and Hours", "Column2", "Column3", "Column4", "Column5",
#     "Column6", "Column7", "Column8", "Column9", "Unwanted 10", "Unwanted 11"
# ]

# df = df.drop['Unwanted 10', 'Unwanted 11']

# ------------- STEP 2: Remove blank rows (PQ-style) -------------
# Treat empty strings as NaN across the board
df = df.replace("", np.nan)
# Drop rows where ALL values are blank/NaN
df = df.dropna(how="all").reset_index(drop=True)

# ------------- STEP 3: Add EmployeeNumber (from next row after "Employee No.") -------------
# We look for "Employee No." in Column8; then take next row's Column8, trim, first 4 chars
col8_str = df.get("Column8", pd.Series(index=df.index, dtype="object")).astype("string")
mask_empno = col8_str.str.contains("Employee No.", case=False, na=False)
next_col8  = col8_str.shift(-1).fillna("").str.strip()
emp_num    = np.where(mask_empno, next_col8.str[:4], None)
df["EmployeeNumber"] = emp_num

# ------------- STEP 4: Rename columns -------------
rename_map = {"Column2": "Qty", "Column3": "Rate", "Column4": "Current", "Column5": "YTD Amount"}
df = df.rename(columns=rename_map)

df.to_csv('linr186.csv')

# ------------- STEP 5: Extract Pay Date from Column8 + fill down -------------
df["Pay Date"] = col8_str.apply(lambda s: _extract_date_after_key(s, "Pay Date:"))
df["Pay Date"] = df["Pay Date"].ffill()

# ------------- STEP 6: Extract Super Pay Date from Qty -------------
qty_str = df.get("Qty", pd.Series(index=df.index, dtype="object")).astype(str)
df["Super Pay Date"] = qty_str.apply(lambda s: _extract_date_after_key(s, "Super Payment Date:"))




print(df.columns)

col6_str = df["Column6"].fillna("").astype(str)

# Create a boolean mask
mask = col6_str.str.contains("Employer Contributions", case=False, na=False)

# Use pandas native assignment to avoid dtype promotion issues
df["MatchFound"] = pd.Series(np.nan, index=df.index, dtype=object)
df.loc[mask, "MatchFound"] = "Match Found"





# ------------- STEP 8: SuperFundName from the row AFTER MatchFound -------------
prev_match = df["MatchFound"].shift(1)
df["SuperFundName"] = np.where(prev_match.eq("Match Found"), col6_str, np.nan)

# ------------- STEP 9: ContributionAmount from NEXT row's Column8 -------------
# Condition: current row Column6 == "Employer Contributions" and Column8 == "Current"
# Careful: PQ checks Column8 textual equals "Current" (your sheet uses "Current" as a header elsewhere too)
col8_raw = df.get("Column8", pd.Series(index=df.index))  # keep raw values for amounts
col8_text = col8_str.fillna("")
cond_contrib = (col6_str.eq("Employer Contributions")) & (col8_text.eq("Current"))
df["ContributionAmount"] = np.where(cond_contrib, df.get("Column8", pd.Series(index=df.index)).shift(-1), np.nan)

# ------------- STEP 10: Fill down SuperFundName -------------
df["SuperFundName"] = df["SuperFundName"].ffill()

# ------------- STEP 11: Rename "Anuj A Bhalla" -> "Earnings and Hours" -------------
df = df.rename(columns={"Anuj A Bhalla": "Earnings and Hours"})

# ------------- STEP 12: Vectorised "next row" logic to set Super -------------
eah = df.get("Earnings and Hours", pd.Series(index=df.index, dtype="object")).astype("string")
next_eah = eah.shift(-1)
make_super_mask = eah.isna() & next_eah.eq("Taxes")
df.loc[make_super_mask, "Earnings and Hours"] = "Super"

# ------------- STEP 13: Update 'Current' where E&H == "Super" and Current is null -------------
# First ensure we have a 'Current' column (was Column4)
if "Current" not in df.columns:
    df["Current"] = np.nan
current_series = df["Current"]
df["Current"] = np.where(current_series.isna() & (df["Earnings and Hours"] == "Super"),
                         df["ContributionAmount"],
                         current_series)

# ------------- STEP 14: Fill down ContributionAmount -------------
df["ContributionAmount"] = df["ContributionAmount"].ffill()

# ------------- STEP 15: Final update to 'Current' for Super rows (overwrite) -------------
df["Current"] = np.where(df["Earnings and Hours"].eq("Super"),
                         df["ContributionAmount"],
                         df["Current"])

# ------------- STEP 16: Drop extra columns -------------
cols_to_drop = ["ContributionAmount", "YTD Amount", "Column6", "Column7", "Column8", "Column9", "MatchFound"]
cols_to_drop = [c for c in cols_to_drop if c in df.columns]
df.drop(columns=cols_to_drop, inplace=True)



emplids_mapping = pd.read_excel(r"C:\Users\smits\OneDrive - SW Accountants & Advisors Pty Ltd\Desktop\Client Projects\Project Royal\Employee IDs.xlsx", sheet_name='EMPLIDS')



df = df.merge(
    emplids_mapping[['Source File', 'Employee ID Consolidated', 'Employee Name']],
    on='Source File',
    how='left'
)



df['EmployeeNumber'] = df['Employee ID Consolidated']

df.to_csv('line272.csv')
print(df.columns)

# Create a copy of the relevant columns
super_df = df[["EmployeeNumber", "Super Pay Date", "SuperFundName"]].copy()

# Define the condition: both EmployeeNumber and Super Pay Date are null
condition = super_df["EmployeeNumber"].isnull() & super_df["Super Pay Date"].isnull()

# Get the first deduplicated SuperFundName value
first_superfund = super_df["SuperFundName"].dropna().drop_duplicates().iloc[0]

# Apply the condition
super_df.loc[condition, "SuperFundName"] = first_superfund


# Identify columns to check (excluding SuperFundName)
columns_to_check = [col for col in super_df.columns if col != "SuperFundName"]

# Drop rows where all other columns are null
super_df = super_df.dropna(subset=columns_to_check, how='all')


super_df.to_excel(OUTPUT_PATH_1, index=False)






cols_to_drop_1 = ["Super Pay Date", "SuperFundName"]
#cols_to_drop_1 = [c for c in cols_to_drop if c in df.columns]
df.drop(columns=cols_to_drop_1, inplace=True)






value_to_drop = "VicPro Security Pty Ltd,39/42 McArthurs Road,Altona North VIC 3025"

# Drop rows where this value appears in any column
df = df[~df.apply(lambda row: row.astype(str).str.contains(value_to_drop, case=False, na=False)).any(axis=1)]


# Convert the 'Earnings and Hours' column to string for safe matching
eah_col = df["Earnings and Hours"].astype(str)

# Find all indices where 'Net Pay' appears
net_pay_indices = eah_col[eah_col.str.contains("Net Pay", case=False, na=False)].index.tolist()

# Find all indices where 'Earnings and Hours' appears
eah_indices = eah_col[eah_col.str.contains("Earnings and Hours", case=False, na=False)].index.tolist()

# Sort indices to ensure proper ordering
net_pay_indices.sort()
eah_indices.sort()

# Collect all valid indices to drop
indices_to_drop = []

for net_idx in net_pay_indices:
    # Find the next 'Earnings and Hours' index after this 'Net Pay'
    next_eah = [i for i in eah_indices if i > net_idx]
    if next_eah:
        next_eah_idx = next_eah[0]
        # Add all indices between net_idx and next_eah_idx (exclusive)
        drop_range = range(net_idx + 1, next_eah_idx)
        # Only keep indices that exist in df.index
        valid_range = [i for i in drop_range if i in df.index]
        indices_to_drop.extend(valid_range)

# Drop the identified rows safely
df.drop(index=indices_to_drop, inplace=True)



# Define regex patterns
patterns = {
    "Earnings and Hours": r"^\s*earnings\s+and\s+hours\s*$",
    "Qty": r"^\s*qty\s*$",
    "Rate": r"^\s*rate\s*$",
    "Current": r"^\s*current\s*$"
}

# Function to check if all specified columns match their respective patterns
def row_matches_all_patterns(row):
    return all(
        re.match(patterns[col], str(row[col]), re.IGNORECASE)
        for col in patterns
    )

# Apply condition and drop rows
df = df[~df.apply(row_matches_all_patterns, axis=1)]



value_to_drop = "Employee Pay Slip"

# Drop rows where this value appears in any column
df = df[~df.apply(lambda row: row.astype(str).str.contains(value_to_drop, case=False, na=False)).any(axis=1)]


value_to_drop = "Taxes"

# Drop rows where this value appears in any column
df = df[~df.apply(lambda row: row.astype(str).str.contains(value_to_drop, case=False, na=False)).any(axis=1)]



# Drop rows with nulls in specified columns
df = df.dropna(subset=['Earnings and Hours', 'Qty', 'Rate', 'Current'], how='all')

df = df.dropna(subset=['Qty','Rate', 'Current',	'EmployeeNumber','Pay Date'], how='all')




current_problemo_list = [
"Accrued",
"Current",
"MLC Super (MLC Super 29791669)",
"Australian Super (AUSSUPER 1073015888)",
"Australian Super (Australian Super 314332...",
"Essential Super (ESSENTIAL 0679790032…",
"Australian Super (Australian Super 358640…",
"Essential Super (ESSENTIAL 0679790032...",
"Australian Super (Australian Super 358640..."



]



# Need to remove Current from after these 

# -174.00 Current
# -97.00 Current"


# Cleaning function
def clean_current(value):
    if value in current_problemo_list:
        return 0
    elif isinstance(value, str) and value.endswith(" Current"):
        try:
            return float(value.replace(" Current", ""))
        except ValueError:
            return value
    else:
        return value

# Apply cleaning
df['Current'] = df['Current'].apply(clean_current)




df['Current'] = (
    pd.to_numeric(df['Current'], errors='coerce')  # Convert to numbers, NaN if invalid
    .astype(float)                                 # Ensure a float type
)


# df['Current'] = (
#     df['Current']
#     .astype(str)                                   # Convert everything to string
#     .str.replace(r'[^\d.-]', '', regex=True)       # Remove non-numeric chars except - and .
#     .replace('', pd.NA)                            # Empty strings become NA
#     .astype(float)
#     .astype('Int64')
# )




# Replace nulls with 'Gross Pay' where 'Current' > 0





# Ensure 'Current' is numeric for comparison
df['Current_num'] = pd.to_numeric(df['Current'], errors='coerce')
df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce')
df['Rate'] = pd.to_numeric(df['Rate'], errors='coerce')

df['Earnings and Hours'] = df['Earnings and Hours'].str.strip()
df['Qty'] = df['Qty'].where(df['Qty'].isnull(), df['Qty'].astype(str).str.strip())
df['Rate'] = df['Rate'].where(df['Rate'].isnull(), df['Rate'].astype(str).str.strip())


df['Earnings and Hours'].replace(['', 'nan'], np.nan, inplace=True)

print(df['Earnings and Hours'].unique())



# Apply the overwrite logic
df['Earnings and Hours'] = np.where(
    df['Earnings and Hours'].isnull() & df['Qty'].isnull() & df['Rate'].isnull() & (df['Current_num'] > 0),
   
    'Gross Pay',
    df['Earnings and Hours']
)


# Optional: drop the helper column if you don't need it
df.drop(columns=['Current_num'], inplace=True)
 

# Drop rows with nulls in specified columns
df = df.dropna(subset=['Qty', 'Rate', 'Current'], how='all')


# Create 'EmpID_key'
df['EmpID_key'] = df['EmployeeNumber'].astype(str) + '_' + df['Pay Date'].astype(str)

df.to_csv('Test_line462.csv')

# Pivot the data
#pivot_df = df.pivot_table(index=df.index, columns='Earnings and Hours', values='Current', aggfunc='sum')


pivot_df = df.pivot_table(
    index=df.index, 
    columns='Earnings and Hours', 
    values=['Current', 'Qty', 'Rate'], 
    aggfunc='sum'
)


# Combine with original DataFrame
df_combined = pd.concat([df, pivot_df], axis=1)
print(df_combined)



print(df_combined.columns.tolist())

df_combined.columns = [
    f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col
    for col in df_combined.columns
]

# df_combined.columns = [f"{col2}_{col1}" if isinstance(col, tuple) else col
     #                  for col in df_combined.columns]



df_combined.to_csv('line_514.csv')



# Convert 'Pay Date' to date-only
df_combined['Pay Date'] = pd.to_datetime(df_combined['Pay Date']).dt.date
print('line 535')

print("df_combined columns:", df_combined.columns.tolist())


# Create 'EmpID_key'
df_combined['EmpID_key'] = df_combined['EmployeeNumber'].astype(str) + '_' + df_combined['Pay Date'].astype(str)

#df_combined = df_combined.drop(columns=['Qty', 'Rate', 'Current'])




print(df_combined.columns)





# Convert column names to a DataFrame and export to CSV
pd.DataFrame(df_combined.columns, columns=['Column Names']).to_csv('df_combined_columns.csv', index=False)

df.drop(columns=['Earnings and Hours',
                    'Qty',
                    'Rate'], inplace=True)
 


# Convert all non-key columns to numeric
for col in df_combined.columns:
    if col != "EmpID_key":
        df_combined[col] = pd.to_numeric(df_combined[col], errors="coerce")

# # Build aggregation dictionary only for valid columns
# agg_dict = {}
# for col in df_combined.columns:
#     if col == "EmpID_key":
#         continue
#     if df_combined[col].notna().any():
#         if col.startswith("Current_") or col.startswith("Qty_"):
#           agg_dict[col] = "sum"

grouped_df = df_combined.groupby('EmpID_key').agg({
'EmployeeNumber': 'first',
'Rate_Adjustments to Net Pay' : 'first',
'Rate_Annual Holiday Loadi...' : 'first',
'Rate_Annual Leave' : 'first',
'Rate_BACK PAY' : 'first',
'Rate_Bereavement' : 'first',
'Rate_Extra Payment' : 'first',
'Rate_First Aid Allowance' : 'first',
'Rate_Gross Pay' : 'first',
'Rate_Holiday Hourly' : 'first',
'Rate_Holiday Loading' : 'first',
'Rate_Holiday Salary' : 'first',
'Rate_Hourly Day' : 'first',
'Rate_Hourly Night' : 'first',
'Rate_Hourly Public Holiday' : 'first',
'Rate_Hourly Saturday' : 'first',
'Rate_Hourly Sunday' : 'first',
'Rate_Leave W/o Pay' : 'first',
'Rate_Net Pay' : 'first',
'Rate_PAYG Tax' : 'first',
'Rate_Paid Time Off' : 'first',
'Rate_Personal Hourly' : 'first',
'Rate_Personal Salary' : 'first',
'Rate_Public Holiday Hourly' : 'first',
'Rate_Public Holiday Not W...' : 'first',
'Rate_Reimbursement' : 'first',
'Rate_Salary' : 'first',
'Rate_Sick Leave Hourly' : 'first',
'Rate_Sick Leave Salary' : 'first',
'Rate_Super' : 'first',
'Rate_Supervisor Allowance' : 'first',
'Qty_Adjustments to Net Pay' : 'sum',
'Qty_Annual Holiday Loadi...' : 'sum',
'Qty_Annual Leave' : 'sum',
'Qty_BACK PAY' : 'sum',
'Qty_Bereavement' : 'sum',
'Qty_Extra Payment' : 'sum',
'Qty_First Aid Allowance' : 'sum',
'Qty_Gross Pay' : 'sum',
'Qty_Holiday Hourly' : 'sum',
'Qty_Holiday Loading' : 'sum',
'Qty_Holiday Salary' : 'sum',
'Qty_Hourly Day' : 'sum',
'Qty_Hourly Night' : 'sum',
'Qty_Hourly Public Holiday' : 'sum',
'Qty_Hourly Saturday' : 'sum',
'Qty_Hourly Sunday' : 'sum',
'Qty_Leave W/o Pay' : 'sum',
'Qty_Net Pay' : 'sum',
'Qty_PAYG Tax' : 'sum',
'Qty_Paid Time Off' : 'sum',
'Qty_Personal Hourly' : 'sum',
'Qty_Personal Salary' : 'sum',
'Qty_Public Holiday Hourly' : 'sum',
'Qty_Public Holiday Not W...' : 'sum',
'Qty_Reimbursement' : 'sum',
'Qty_Salary' : 'sum',
'Qty_Sick Leave Hourly' : 'sum',
'Qty_Sick Leave Salary' : 'sum',
'Qty_Super' : 'sum',
'Qty_Supervisor Allowance' : 'sum',

'Current_Adjustments to Net Pay' : 'sum',
'Current_Annual Holiday Loadi...' : 'sum',
'Current_Annual Leave' : 'sum',
'Current_BACK PAY' : 'sum',
'Current_Bereavement' : 'sum',
'Current_Extra Payment' : 'sum',
'Current_First Aid Allowance' : 'sum',
'Current_Gross Pay' : 'sum',
'Current_Holiday Hourly' : 'sum',
'Current_Holiday Loading' : 'sum',
'Current_Holiday Salary' : 'sum',
'Current_Hourly Day' : 'sum',
'Current_Hourly Night' : 'sum',
'Current_Hourly Public Holiday' : 'sum',
'Current_Hourly Saturday' : 'sum',
'Current_Hourly Sunday' : 'sum',
'Current_Leave W/o Pay' : 'sum',
'Current_Net Pay' : 'sum',
'Current_PAYG Tax' : 'sum',
'Current_Paid Time Off' : 'sum',
'Current_Personal Hourly' : 'sum',
'Current_Personal Salary' : 'sum',
'Current_Public Holiday Hourly' : 'sum',
'Current_Public Holiday Not W...' : 'sum',
'Current_Reimbursement' : 'sum',
'Current_Salary' : 'sum',
'Current_Sick Leave Hourly' : 'sum',
'Current_Sick Leave Salary' : 'sum',
'Current_Super' : 'sum',
'Current_Supervisor Allowance' : 'sum'




}).reset_index()




# Define ordered columns in Rate–Qty–Current trios
ordered_columns = ['EmpID_key', 'EmployeeNumber',
                   
'Rate_Adjustments to Net Pay',
'Qty_Adjustments to Net Pay',
'Current_Adjustments to Net Pay',
'Rate_Annual Holiday Loadi...',
'Qty_Annual Holiday Loadi...',
'Current_Annual Holiday Loadi...',
'Rate_Annual Leave',
'Qty_Annual Leave',
'Current_Annual Leave',
'Rate_BACK PAY',
'Qty_BACK PAY',
'Current_BACK PAY',
'Rate_Bereavement',
'Qty_Bereavement',
'Current_Bereavement',
'Rate_Extra Payment',
'Qty_Extra Payment',
'Current_Extra Payment',
'Rate_First Aid Allowance',
'Qty_First Aid Allowance',
'Current_First Aid Allowance',
'Rate_Gross Pay',
'Qty_Gross Pay',
'Current_Gross Pay',
'Rate_Holiday Hourly',
'Qty_Holiday Hourly',
'Current_Holiday Hourly',
'Rate_Holiday Loading',
'Qty_Holiday Loading',
'Current_Holiday Loading',
'Rate_Holiday Salary',
'Qty_Holiday Salary',
'Current_Holiday Salary',
'Rate_Hourly Day',
'Qty_Hourly Day',
'Current_Hourly Day',
'Rate_Hourly Night',
'Qty_Hourly Night',
'Current_Hourly Night',
'Rate_Hourly Public Holiday',
'Qty_Hourly Public Holiday',
'Current_Hourly Public Holiday',
'Rate_Hourly Saturday',
'Qty_Hourly Saturday',
'Current_Hourly Saturday',
'Rate_Hourly Sunday',
'Qty_Hourly Sunday',
'Current_Hourly Sunday',
'Rate_Leave W/o Pay',
'Qty_Leave W/o Pay',
'Current_Leave W/o Pay',
'Rate_Net Pay',
'Qty_Net Pay',
'Current_Net Pay',
'Rate_PAYG Tax',
'Qty_PAYG Tax',
'Current_PAYG Tax',
'Rate_Paid Time Off',
'Qty_Paid Time Off',
'Current_Paid Time Off',
'Rate_Personal Hourly',
'Qty_Personal Hourly',
'Current_Personal Hourly',
'Rate_Personal Salary',
'Qty_Personal Salary',
'Current_Personal Salary',
'Rate_Public Holiday Hourly',
'Qty_Public Holiday Hourly',
'Current_Public Holiday Hourly',
'Rate_Public Holiday Not W...',
'Qty_Public Holiday Not W...',
'Current_Public Holiday Not W...',
'Rate_Reimbursement',
'Qty_Reimbursement',
'Current_Reimbursement',
'Rate_Salary',
'Qty_Salary',
'Current_Salary',
'Rate_Sick Leave Hourly',
'Qty_Sick Leave Hourly',
'Current_Sick Leave Hourly',
'Rate_Sick Leave Salary',
'Qty_Sick Leave Salary',
'Current_Sick Leave Salary',
'Rate_Super',
'Qty_Super',
'Current_Super',
'Rate_Supervisor Allowance',
'Qty_Supervisor Allowance',
'Current_Supervisor Allowance'




 
]

# Reorder columns
grouped_df = grouped_df[ordered_columns]

# Drop columns where *all* values are 0
def drop_all_zero_columns(df):
    """Drop columns where all values are 0 or NaN, and print which were dropped."""
    mask = (df.fillna(0) != 0).any(axis=0)  # True = keep
    dropped_cols = df.columns[~mask]        # columns where mask = False
    
    if len(dropped_cols) > 0:
        print("Dropped columns:", list(dropped_cols))
        print("Number Dropped Columns: ", len(dropped_cols))
    else:
        print("No columns dropped (none were all zero).")
    
    return df.loc[:, mask]

# Usage
grouped_df = drop_all_zero_columns(grouped_df)



# ------------- OUTPUT -------------
# Save to Excel (change OUTPUT_PATH if you want CSV)


grouped_df.to_excel(OUTPUT_PATH, index=False)



print(f"Done. Rows: {len(df):,}. Saved to: {OUTPUT_PATH}")

