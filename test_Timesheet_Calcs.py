from datetime import datetime
from Timesheet Calculations v1.4 import calculate_time_difference_in_hours

date_series = datetime(2023, 11, 13)  # just the date
time_series_start = datetime(2023, 11, 13, 6, 0, 0)
time_series_end = datetime(2023, 11, 13, 18, 0, 0)

def test_calculate_time_difference_in_hours():
    assert calculate_time_difference_in_hours(date_series, time_series_start, time_series_end) == 12
