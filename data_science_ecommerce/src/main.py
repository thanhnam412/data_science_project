import os
from pathlib import Path

# Import các hàm phân tích mà chúng ta đã tạo
from analysis_demand_interval import calculate_adi
from analysis_demand_cv2 import calculate_cv2

# (Bạn có thể giữ CSVCrud nếu bạn cần dùng nó sau)
# from utils.crud import CSVCrud

def run_all_analyses():
    """
    Hàm chính để chạy tất cả các phân tích dữ liệu.
    """
    
    # Xác định đường dẫn đến tệp dữ liệu
    # Tệp main.py nằm trong 'src/'
    # Tệp dữ liệu nằm trong 'src/data/raw/sales_train.csv'
    current_dir = Path(__file__).resolve().parent
    sales_path = current_dir / "data" / "raw" / "sales_train.csv"

    # Kiểm tra xem tệp có tồn tại không
    if not sales_path.exists():
        print(f"Lỗi: Không tìm thấy tệp dữ liệu tại: {sales_path}")
        print("Vui lòng đảm bảo tệp 'sales_train.csv' nằm trong 'src/data/raw/'")
        return

    print(f"--- Bắt đầu phân tích dữ liệu từ: {sales_path} ---")

    # --- 1. Chạy Phân tích ADI ---
    # (Hàm này sẽ tự in kết quả)
    calculate_adi(sales_path)
    
    print("\n" + "="*50 + "\n") # Thêm dấu phân cách

    # --- 2. Chạy Phân tích CV² ---
    # (Hàm này cũng sẽ tự in kết quả)
    calculate_cv2(sales_path)
    
    print("\n--- Hoàn tất tất cả phân tích ---")

if __name__ == "__main__":
    run_all_analyses()
