import pandas as pd
import os
from typing import Optional

def calculate_adi(file_path: str) -> Optional[pd.DataFrame]:
    """
    Tính ADI (Average Demand Interval) cho từng cặp (shop_id, item_id).

    ADI = Tổng số ngày trong khoảng thời gian phân tích / Số ngày có nhu cầu (> 0)
    """
    print("--- Bắt đầu tính toán ADI (Average Demand Interval) ---")
    
    try:
        df_sales = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp tại đường dẫn: {file_path}")
        return None

    # 1. Tiền xử lý dữ liệu
    df_sales['date'] = pd.to_datetime(df_sales['date'], format='%d.%m.%Y')

    # Tính tổng khoảng thời gian phân tích (tính theo ngày)
    min_date = df_sales['date'].min()
    max_date = df_sales['date'].max()
    TOTAL_DAYS_SPAN = (max_date - min_date).days + 1
    
    print(f"Khoảng thời gian phân tích: {TOTAL_DAYS_SPAN} ngày.")

    # 2. Lọc nhu cầu thực tế (loại bỏ hàng trả lại hoặc giao dịch bằng 0)
    df_demand = df_sales[df_sales['item_cnt_day'] > 0].copy()

    # 3. Tính số ngày có nhu cầu (> 0) cho mỗi cặp (shop, item)
    demand_periods = df_demand.groupby(['shop_id', 'item_id'])['date'].nunique().reset_index(name='demand_periods')

    # 4. Tính ADI
    demand_periods['ADI'] = TOTAL_DAYS_SPAN / demand_periods['demand_periods']

    # In kết quả thống kê
    print("\n--- Thống kê ADI (Average Demand Interval) ---")
    print(demand_periods['ADI'].describe())
    
    print("\n--- 5 cặp item/shop có ADI cao nhất (nhu cầu không liên tục) ---")
    top_adi = demand_periods.sort_values(by='ADI', ascending=False).head(5)
    
    # --- DÒNG ĐÃ SỬA LỖI ---
    # Thay thế .to_markdown(index=False) bằng print() thông thường
    print(top_adi)

    return demand_periods

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sales_path = os.path.join(current_dir, 'data', 'raw', 'sales_train.csv')
    
    if not os.path.exists(sales_path):
        print(f"Lỗi: Không tìm thấy tệp {sales_path} khi chạy độc lập.")
    else:
        print(f"Chạy độc lập: Đang phân tích dữ liệu từ: {sales_path}")
        calculate_adi(sales_path)