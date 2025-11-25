import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN

# ============================================
# 1) LOAD & TIỀN XỬ LÝ DỮ LIỆU
# ============================================
df = pd.read_csv("data/raw/sales_train.csv", encoding="latin1")
# df2 = pd.read_csv("data/raw/online_retail.csv", encoding="latin1")
demand = pd.read_csv("data/features/demand_type.csv", encoding="latin1")

# df2["InvoiceDate"] = pd.to_datetime(df2["InvoiceDate"], dayfirst=True)

# df2["date_block_num"] = (df2["InvoiceDate"].dt.year - 2010) * 12 + (
#     df2["InvoiceDate"].dt.month - 1
# )

# df2["shop_id"] = 0
# df2["item_id"] = df2["StockCode"].astype("category").cat.codes

# df2_new = (
#     df2.groupby(["InvoiceDate", "date_block_num", "shop_id", "item_id"])
#     .agg({"UnitPrice": "mean", "Quantity": "sum"})
#     .reset_index()
# )

# df2_new.rename(
#     columns={
#         "InvoiceDate": "date",
#         "UnitPrice": "item_price",
#         "Quantity": "item_cnt_day",
#     },
#     inplace=True,
# )

# df2_new["date"] = df2_new["date"].dt.strftime("%d.%m.%Y")
# df = df2_new.copy()

# ============================================
# 2) TÍNH TRUNG BÌNH BÁN THEO THÁNG CHO TỪNG ITEM
# ============================================

df_sold = df[df["item_cnt_day"] > 0]  # chỉ lấy ngày có bán

item_block_df = df_sold.groupby("item_id")
list_block_num = df["date_block_num"].nunique()

# loại item không có std (ít dữ liệu → noise)
valid_mask = ~item_block_df["item_cnt_day"].std().isna()

valid_items = valid_mask[valid_mask].index

df_valid = df_sold[df_sold["item_id"].isin(valid_items)]

# tính trung bình tháng
avg_df = (
    df_valid.groupby("item_id")[["item_cnt_day", "item_price"]].sum() / list_block_num
)

avg_df.rename(
    columns={"item_cnt_day": "sell_avg_month", "item_price": "price"}, inplace=True
)


# ============================================
# 3) LOẠI OUTLIER BẰNG IQR
# ============================================


def remove_outliers_iqr(df, columns):
    df_clean = df.copy()
    for col in columns:
        Q1 = df_clean[col].quantile(0.25)
        Q3 = df_clean[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        df_clean = df_clean[(df_clean[col] >= lower) & (df_clean[col] <= upper)]
    return df_clean


numeric_cols = ["sell_avg_month", "price"]
avg_clean = remove_outliers_iqr(avg_df, numeric_cols)

# ============================================
# 4) GHÉP DEMAND TYPE
# ============================================

filter_df = pd.concat([avg_clean, demand["demand_type"]], axis=1).dropna()
# filter_df = filter_df[filter_df["demand_type"] == 1]

print(filter_df.describe())

# ============================================
# 4.1) LỌC THEO ZERO_RATIO
# ============================================

# Tính mean của zero_ratio
mean_zero_ratio = demand["zero_ratio"].quantile(0.25)

# Lọc ra các item có zero_ratio <= mean (loại item zero_ratio lớn hơn mean)
demand_filtered = demand[demand["zero_ratio"] <= mean_zero_ratio]

print("Mean zero_ratio =", mean_zero_ratio)
print("Số lượng item còn lại =", len(demand_filtered))


demand_filtered = demand_filtered.set_index("item_id")
avg_clean = avg_clean.set_index(avg_clean.index)  # đã là item_id rồi

filter_df = avg_clean.join(demand_filtered[["demand_type", "zero_ratio"]], how="inner")
filter_df = filter_df.dropna()

numeric_cols = ["zero_ratio"]
filter_df = remove_outliers_iqr(filter_df, numeric_cols)

print(filter_df.describe())

# ============================================
# 5) CHUẨN HÓA + DBSCAN
# ============================================

X = filter_df[["sell_avg_month", "price"]].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

dbscan = DBSCAN(eps=0.5, min_samples=10)
clusters = dbscan.fit_predict(X_scaled)

filter_df["demand_type_dbscan"] = clusters

from sklearn.cluster import KMeans

# ============================================
# 5) CHUẨN HÓA + KMEANS
# ============================================

X = filter_df[["sell_avg_month", "price"]].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=4, random_state=42)
clusters = kmeans.fit_predict(X_scaled)

filter_df["demand_type_kmeans"] = clusters

from sklearn.metrics import silhouette_score

score = silhouette_score(X, clusters)
print("Silhouette:", score)

# ============================================
# 6) VẼ PHÂN CỤM
# ============================================

plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=filter_df,
    x="sell_avg_month",
    y="price",
    hue="demand_type_dbscan",
    palette="deep",
    alpha=0.6,
)
plt.title("DBSCAN Demand Segmentation (Sell Avg/Month vs Price)")
plt.legend()
plt.show()
