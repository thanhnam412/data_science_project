import pandas as pd
from itertools import product


def etl_daily_to_monthly(df):
    """
    Chuyển data bán hàng daily -> monthly demand.
    Input:
        df: pandas.DataFrame có các cột ['date','item_id','shop_id','qty','price']
            - 'date' có thể là str hoặc datetime
            - 'qty' là số lượng (demand)
    Output:
        df_monthly: pandas.DataFrame với MultiIndex (item_id, month) và 1 cột 'demand'
            - 'month' là pandas.Period (freq='M')
            - index được sort theo item_id rồi month
    """
    # 1. Sao lưu, parse ngày
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        try:
            df["date"] = pd.to_datetime(df["date"])
        except:
            df["date"] = pd.to_datetime(df["date"], dayfirst=True)

    # 2. Tạo cột month (Period)
    df["month"] = df["date"].dt.to_period("M")

    # 3. Tổng hợp demand theo item_id và month (ignore shop_id; nếu cần gộp theo shop hãy sửa)
    grouped = (
        df.groupby(["item_id", "month"], observed=True)["qty"].sum().rename("demand")
    )
    # `grouped` là Series có MultiIndex (item_id, period)

    # 4. Xác định khoảng tháng toàn cục
    min_month = df["month"].min()
    max_month = df["month"].max()
    all_months = pd.period_range(min_month, max_month, freq="M")

    # 5. Danh sách item_id xuất hiện trong input
    items = df["item_id"].unique()

    # 6. Tạo full index (cartesian product item x all_months)
    full_index = pd.MultiIndex.from_product(
        [items, all_months], names=["item_id", "month"]
    )

    # 7. Reindex grouped theo full_index và fill missing bằng 0
    #    Chuyển Series -> reindex -> DataFrame
    s_full = grouped.reindex(full_index, fill_value=0)
    df_monthly = s_full.to_frame()

    # 8. Đảm bảo kiểu dữ liệu demand là int (nếu phù hợp) hoặc numeric
    #    (nếu qty có float, bạn có thể giữ float)
    if pd.api.types.is_integer_dtype(df["qty"]) or all((df["qty"].dropna() % 1 == 0)):
        # an toàn để cast về int
        df_monthly["demand"] = df_monthly["demand"].astype(int)

    # 9. Sort index (đảm bảo thứ tự: item_id, month tăng dần)
    df_monthly = df_monthly.sort_index(level=["item_id", "month"])

    # Nếu bạn muốn month là datetime (first day of month) thay vì Period, có thể chuyển:
    # df_monthly = df_monthly.reset_index()
    # df_monthly['month'] = df_monthly['month'].dt.to_timestamp()
    # df_monthly = df_monthly.set_index(['item_id','month']).sort_index()

    return df_monthly


# ---------- Example usage ----------
if __name__ == "__main__":
    # Ví dụ data nhỏ
    data = [
        {"date": "2025-01-05", "item_id": 1, "shop_id": 10, "qty": 2, "price": 100},
        {"date": "2025-01-20", "item_id": 1, "shop_id": 10, "qty": 1, "price": 100},
        {"date": "2025-03-03", "item_id": 1, "shop_id": 11, "qty": 5, "price": 95},
        {"date": "02.01.2013", "item_id": 2, "shop_id": 12, "qty": 3, "price": 200},
    ]
    df_daily = pd.DataFrame(data)

    df_monthly = etl_daily_to_monthly(df_daily)
    print(df_monthly)
