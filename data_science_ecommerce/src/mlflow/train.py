import argparse
import sys
from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

# add repo src to PYTHONPATH
ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT / "src"))

from src.utils.date_caculator import compute_interarrival  # use existing util if needed


def build_samples_from_sales(df):
    """Create one sample per sale event (except last sale per item).
    Input df: columns ['date','item_id','item_cnt_day']
    Returns DataFrame of features + targets:
      - target_interval_days: days to next sale
      - target_next_qty: qty at next sale
    """
    rows = []
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    for item, g in df.sort_values(["item_id", "date"]).groupby("item_id"):
        dates = g["date"].values
        cnts = g["item_cnt_day"].values
        pos = np.where(cnts > 0)[0]
        if len(pos) < 2:
            continue
        sale_dates = dates[pos]
        sale_cnts = cnts[pos]
        # global item-level features
        total_sales = sale_cnts.sum()
        mean_size_item = sale_cnts.mean()
        var_size_item = sale_cnts.var() if len(sale_cnts) > 1 else 0.0
        interarr = np.diff(sale_dates).astype("timedelta64[D]").astype(int) if len(sale_dates) > 1 else np.array([0])
        mean_inter_item = interarr.mean() if len(interarr) > 0 else 0.0

        # create sample for each sale except last
        for i in range(len(sale_dates) - 1):
            hist_sizes = sale_cnts[: i + 1]
            hist_dates = sale_dates[: i + 1]
            last_size = hist_sizes[-1]
            mean_size_hist = hist_sizes.mean()
            var_size_hist = hist_sizes.var() if len(hist_sizes) > 1 else 0.0
            # recency from last sale to "now" is zero (we use last sale as snapshot),
            # but can add calendar features of last sale:
            last_date = pd.to_datetime(hist_dates[-1])
            dow = last_date.dayofweek
            month = last_date.month

            # historical intervals (in days)
            if len(hist_dates) > 1:
                hist_intervals = np.diff(hist_dates).astype("timedelta64[D]").astype(int)
                mean_interval_hist = hist_intervals.mean()
                var_interval_hist = hist_intervals.var()
            else:
                mean_interval_hist = mean_inter_item
                var_interval_hist = 0.0

            # targets: next sale
            next_date = pd.to_datetime(sale_dates[i + 1])
            target_interval = int((next_date - last_date).astype("timedelta64[D]"))
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


def train_and_log(X_train, X_val, y_train_interval, y_val_interval, y_train_qty, y_val_qty, args):
    mlflow.set_experiment(args.experiment_name)
    with mlflow.start_run(run_name=args.run_name):
        mlflow.log_param("model_type_interval", "RandomForestRegressor")
        mlflow.log_param("model_type_qty", "RandomForestRegressor")
        mlflow.log_param("n_estimators", args.n_estimators)
        mlflow.log_param("random_state", args.random_state)

        rf_interval = RandomForestRegressor(n_estimators=args.n_estimators, random_state=args.random_state, n_jobs=-1)
        rf_qty = RandomForestRegressor(n_estimators=args.n_estimators, random_state=args.random_state, n_jobs=-1)

        rf_interval.fit(X_train, y_train_interval)
        rf_qty.fit(X_train, y_train_qty)

        preds_interval = rf_interval.predict(X_val)
        preds_qty = rf_qty.predict(X_val)

        mae_int = mean_absolute_error(y_val_interval, preds_interval)
        rmse_int = mean_squared_error(y_val_interval, preds_interval, squared=False)
        mae_qty = mean_absolute_error(y_val_qty, preds_qty)
        rmse_qty = mean_squared_error(y_val_qty, preds_qty, squared=False)

        # accuracy-like metrics: within +/- 5 days for interval
        acc_within_5 = np.mean(np.abs(y_val_interval - preds_interval) <= 5)
        # for qty, within 50% or absolute 1 item
        acc_qty_rel50 = np.mean(np.abs(y_val_qty - preds_qty) <= 0.5 * y_val_qty.clip(min=1))

        mlflow.log_metric("mae_interval_days", float(mae_int))
        mlflow.log_metric("rmse_interval_days", float(rmse_int))
        mlflow.log_metric("mae_qty", float(mae_qty))
        mlflow.log_metric("rmse_qty", float(rmse_qty))
        mlflow.log_metric("acc_interval_within_5d", float(acc_within_5))
        mlflow.log_metric("acc_qty_within_50pct", float(acc_qty_rel50))

        # log models
        mlflow.sklearn.log_model(rf_interval, "model_interval")
        mlflow.sklearn.log_model(rf_qty, "model_qty")

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", required=True, help="CSV file with columns date,item_id,item_cnt_day")
    parser.add_argument("--experiment-name", default="restock_forecast")
    parser.add_argument("--run-name", default="run1")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    df = pd.read_csv(args.data_path)
    samples = build_samples_from_sales(df)
    if samples.empty:
        raise SystemExit("No training samples created. Check input data.")

    features = [
        "dow",
        "month",
        "last_size",
        "mean_size_hist",
        "var_size_hist",
        "mean_interval_hist",
        "var_interval_hist",
        "mean_size_item",
        "var_size_item",
        "mean_inter_item",
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