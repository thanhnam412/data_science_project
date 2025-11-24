import sys
from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import lightgbm as lgb 
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

def build_samples_from_sales(df):
    """
    Tạo các mẫu dữ liệu (features + targets) từ các sự kiện bán hàng, 
    chỉ tập trung vào các ngày có bán hàng (sale events).
    """
    rows = []
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors='coerce').dropna() 
    
    for item, g in df.sort_values(["item_id", "date"]).groupby("item_id"):
        dates = g["date"].values
        cnts = g["item_cnt_day"].values
        pos = np.where(cnts > 0)[0]
        
        if len(pos) < 2:
            continue
        
        sale_dates = dates[pos]
        sale_cnts = cnts[pos]
        
        mean_size_item = sale_cnts.mean()
        var_size_item = sale_cnts.var() if len(sale_cnts) > 1 else 0.0
        interarr = np.diff(sale_dates).astype("timedelta64[D]").astype(int) if len(sale_dates) > 1 else np.array([0])
        mean_inter_item = interarr.mean() if len(interarr) > 0 else 0.0

        for i in range(len(sale_dates) - 1):
            hist_sizes = sale_cnts[: i + 1]
            hist_dates = sale_dates[: i + 1]
            last_size = hist_sizes[-1]
            
            mean_size_hist = hist_sizes.mean() 
            var_size_hist = hist_sizes.var() if len(hist_sizes) > 1 else 0.0
            
            last_date = pd.to_datetime(hist_dates[-1])
            dow = last_date.dayofweek
            month = last_date.month

            mean_interval_hist = mean_inter_item
            var_interval_hist = 0.0
            
            if len(hist_dates) > 1:
                hist_intervals = np.diff(hist_dates).astype("timedelta64[D]").astype(int)
                mean_interval_hist = hist_intervals.mean()
                var_interval_hist = hist_intervals.var()
            
            next_date = pd.to_datetime(sale_dates[i + 1])
            
            target_interval = int((next_date - last_date).days)
            
            target_next_qty = float(sale_cnts[i + 1])

            rows.append(
                {
                    "item_id": item,
                    "last_date": last_date,
                    "dow": dow,
                    "month": month,
                    "last_size": last_size,
                    "mean_size_hist": mean_size_hist,
                    "var_size_hist": var_size_hist,
                    "mean_interval_hist": mean_interval_hist,
                    "var_interval_hist": var_interval_hist,
                    "mean_size_item": mean_size_item,
                    "var_size_item": var_size_item if not np.isnan(var_size_item) else 0.0,
                    "mean_inter_item": mean_inter_item if not np.isnan(mean_inter_item) else 0.0,
                    "target_interval_days": target_interval,
                    "target_next_qty": target_next_qty,
                }
            )
    return pd.DataFrame(rows)

class Args:
    def __init__(self, data_path, experiment_name, run_name, test_size, n_estimators, random_state):
        self.data_path = data_path
        self.experiment_name = experiment_name
        self.run_name = run_name
        self.test_size = test_size
        self.n_estimators = n_estimators
        self.random_state = random_state

def train_and_log(X_train, X_val, y_train_interval, y_val_interval, y_train_qty, y_val_qty, args):
    """
    Huấn luyện LightGBM và ghi log vào MLflow.
    """
    mlflow.set_experiment(args.experiment_name)
    with mlflow.start_run(run_name=args.run_name):
        mlflow.log_param("model_type_interval", "LGBMRegressor")
        mlflow.log_param("model_type_qty", "LGBMRegressor")
        mlflow.log_param("n_estimators", args.n_estimators)
        mlflow.log_param("random_state", args.random_state)

        lgb_interval = lgb.LGBMRegressor(n_estimators=args.n_estimators, random_state=args.random_state, n_jobs=-1)
        lgb_qty = lgb.LGBMRegressor(n_estimators=args.n_estimators, random_state=args.random_state, n_jobs=-1)

        lgb_interval.fit(X_train, y_train_interval)
        lgb_qty.fit(X_train, y_train_qty)

        preds_interval = lgb_interval.predict(X_val)
        preds_qty = lgb_qty.predict(X_val)

        # Tính toán Accuracy (MAE và RMSE)
        mae_int = mean_absolute_error(y_val_interval, preds_interval)
        rmse_int = mean_squared_error(y_val_interval, preds_interval, squared=False)
        mae_qty = mean_absolute_error(y_val_qty, preds_qty)
        rmse_qty = mean_squared_error(y_val_qty, preds_qty, squared=False)

        # Metric phụ cho tính Accuracy
        acc_within_5 = np.mean(np.abs(y_val_interval - preds_interval) <= 5)
        acc_qty_rel50 = np.mean(np.abs(y_val_qty - preds_qty) <= 0.5 * y_val_qty.clip(min=1))

        # Ghi log Metrics
        mlflow.log_metric("mae_interval_days", float(mae_int))
        mlflow.log_metric("rmse_interval_days", float(rmse_int))
        mlflow.log_metric("mae_qty", float(mae_qty))
        mlflow.log_metric("rmse_qty", float(rmse_qty))
        mlflow.log_metric("acc_interval_within_5d", float(acc_within_5))
        mlflow.log_metric("acc_qty_within_50pct", float(acc_qty_rel50))

        # Log models
        mlflow.sklearn.log_model(lgb_interval, "model_interval")
        mlflow.sklearn.log_model(lgb_qty, "model_qty")

        print("Logged metrics and models to MLflow.")
        return {
            "mae_interval": mae_int,
            "rmse_interval": rmse_int,
            "mae_qty": mae_qty,
            "rmse_qty": rmse_qty,
            "acc_within_5d": acc_within_5,
            "acc_qty_50pct": acc_qty_rel50,
        }


def main():
    data_path = ".\\data_science_ecommerce\\src\\data\\raw\\sales_train.csv" 
    experiment_name = "restock_forecast"
    run_name = "LGBM_Run_Direct"
    test_size = 0.2
    n_estimators = 100
    random_state = 42
    
    args = Args(data_path, experiment_name, run_name, test_size, n_estimators, random_state)

    df = pd.read_csv(args.data_path)
    samples = build_samples_from_sales(df)
    
    if samples.empty:
        raise SystemExit("No training samples created. Check input data.")

    features = [
        "dow", "month", "last_size", "mean_size_hist", "var_size_hist", 
        "mean_interval_hist", "var_interval_hist", "mean_size_item", 
        "var_size_item", "mean_inter_item",
    ]
    X = samples[features].fillna(0)
    y_interval = samples["target_interval_days"].values
    y_qty = samples["target_next_qty"].values
    X_train, X_val, y_train_int, y_val_int, y_train_qty, y_val_qty = train_test_split(
        X, y_interval, y_qty, test_size=args.test_size, random_state=args.random_state
    )

    metrics = train_and_log(X_train, X_val, y_train_int, y_val_int, y_train_qty, y_val_qty, args)
    print(metrics)


if __name__ == "__main__":
    main()