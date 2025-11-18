import pandas as pd
import numpy as np
import os
from typing import Optional

def calculate_cv2(file_path: str) -> Optional[pd.DataFrame]:
    """
    Tính CV² (Squared Coefficient of Variation) của khối lượng nhu cầu (demand volume)
    cho từng cặp (shop_id, item_id).

    CV² = (Độ lệch chuẩn của nhu cầu / Giá trị trung bình của nhu cầu)^2
    Chỉ xét những ngày có nhu cầu (sales > 0).
    """
    print("--- Bắt đầu tính toán CV² (Squared Coefficient of Variation) ---")
    
    try:
        df_sales = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp tại đường dẫn: {file_path}")
        return None

    # 1. Lọc nhu cầu thực tế (loại bỏ hàng trả lại hoặc giao dịch bằng 0)
    df_demand = df_sales[df_sales['item_cnt_day'] > 0].copy()

    # 2. Tổng hợp khối lượng nhu cầu hàng ngày (Demand Volume)
    df_daily_demand = df_demand.groupby(['shop_id', 'item_id', 'date'])['item_cnt_day'].sum().reset_index(name='demand_volume')

    # 3. Tính toán Thống kê (Mean và Standard Deviation) của khối lượng nhu cầu
    demand_stats = df_daily_demand.groupby(['shop_id', 'item_id'])['demand_volume'].agg(
        mean_demand=('mean'),
        std_dev_demand=('std')
    ).reset_index()

    # Xử lý trường hợp std_dev là NaN (chỉ có 1 lần bán hàng) bằng cách điền 0
    demand_stats['std_dev_demand'] = demand_stats['std_dev_demand'].fillna(0)

    # 4. Tính CV và CV²
    demand_stats['CV'] = demand_stats['std_dev_demand'] / demand_stats['mean_demand']
    demand_stats['CV2'] = demand_stats['CV'] ** 2

    # In kết quả thống kê
    print("\n--- Thống kê CV² (Squared Coefficient of Variation) ---")
    print(demand_stats['CV2'].describe())
    
    print("\n--- 5 cặp item/shop có CV² cao nhất (nhu cầu biến động mạnh) ---")
    top_cv2 = demand_stats.sort_values(by='CV2', ascending=False).head(5)
    
    # --- DÒNG ĐÃ SỬA LỖI ---
    # Thay thế .to_markdown(index=False) bằng print() thông thường
    print(top_cv2)

    return demand_stats

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sales_path = os.path.join(current_dir, 'data', 'raw', 'sales_train.csv')
    
    if not os.path.exists(sales_path):
        print(f"Lỗi: Không tìm thấy tệp {sales_path} khi chạy độc lập.")
    else:
        print(f"Chạy độc lập: Đang phân tích dữ liệu từ: {sales_path}")
        calculate_cv2(sales_path)