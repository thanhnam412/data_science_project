import pandas as pd
import numpy as np


# 1. Chuyển tất cả ngày sang datetime ngay từ đầu
def list_to_datetime(dates):
    """Convert list of strings to sorted pd.DatetimeIndex"""
    return pd.to_datetime(dates, dayfirst=True).sort_values()


# 2. Vectorized interarrival computation
def compute_interarrival(dates_list):
    if len(dates_list) < 2:
        return np.array([], dtype=int)
    dates = list_to_datetime(dates_list)
    return np.diff(dates.values).astype("timedelta64[D]").astype(int)
