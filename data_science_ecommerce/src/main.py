# %%
import pandas as pd

# df = pd.read_csv("../data/raw/sales_train.csv") 

# %%
import pandas as pd

# Load dữ liệu
df2 = pd.read_csv("src/data/raw/online_retail.csv", encoding="latin1")

# Chuyển InvoiceDate sang datetime
df2['InvoiceDate'] = pd.to_datetime(df2['InvoiceDate'], dayfirst=True)

# Thêm date_block_num theo tháng
df2['date_block_num'] = (df2['InvoiceDate'].dt.year - 2010) * 12 + (df2['InvoiceDate'].dt.month - 1)

# Nếu chỉ có 1 shop: tạo shop_id = 0
df2['shop_id'] = 0

# Map StockCode thành item_id
df2['item_id'] = df2['StockCode'].astype('category').cat.codes

# Group theo ngày + item + shop
df2_new = df2.groupby(['InvoiceDate','date_block_num','shop_id','item_id']).agg({
    'UnitPrice':'mean',  # trung bình nếu nhiều đơn trong ngày
    'Quantity':'sum'
}).reset_index()

# Đổi tên cột và chuyển date về format DD.MM.YYYY
df2_new.rename(columns={
    'InvoiceDate':'date',
    'UnitPrice':'item_price',
    'Quantity':'item_cnt_day'
}, inplace=True)

df2_new['date'] = df2_new['date'].dt.strftime('%d.%m.%Y')

df = df2_new.copy()

print(df2_new.head())


# %%
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# %%
total_cnt_day = df['item_cnt_day'].sum()
print(total_cnt_day)

# %%
block_cnt = df['item_cnt_day'].groupby(df['date_block_num']).sum()

# %%
total_cnt = block_cnt.sum()

# %%
sold = df[df['item_cnt_day'] >= 0]
return_goods = df[df['item_cnt_day'] < 0]

# %%
print(sold['item_cnt_day'].sum())
print(return_goods['item_cnt_day'].sum())

# %%
unique_date_per_block_num = df['date'].groupby(df['date_block_num']).nunique()
print(unique_date_per_block_num)

# %% [markdown]
# ta thấy block nào cũng đủ date trong tháng -> có thể tính tổng days = nunique cột date

# %%
total_days_of_selling = unique_date_per_block_num.sum()

print(total_days_of_selling)

# %%
non_zero_demand_days = df['date'].groupby(sold['item_id']).nunique()

zero_demand_days = total_days_of_selling - non_zero_demand_days

zero_ratio = zero_demand_days / total_days_of_selling

print(non_zero_demand_days)
print(zero_demand_days)
print(zero_ratio)

# %% [markdown]
# đếm tổng string khác nhau của 1 loại item => số ngày mà sản phẩm đó được bán

# %%
print(non_zero_demand_days.describe())

# %%
zero_ratio.hist(bins=100)
plt.xlabel('Zero Ratio')
plt.ylabel('Number of items')
plt.title('Distribution of Zero Ratio per Item')
plt.show()
print(zero_ratio.describe())

# %%
day_sell_of_item = df['date'].groupby(sold['item_id']).unique()

# %%
items_df = pd.concat([zero_ratio, day_sell_of_item], axis=1)
items_df.columns = ['zero_ratio', 'days_sold']
print(items_df)

# %%
from src.utils.date_caculator import compute_interarrival
items_df['interarrival'] = items_df['days_sold'].map(compute_interarrival)


# %%
items_df['var_demand_days'] = sold['item_cnt_day'].groupby(sold['item_id']).var()
items_df['mean_demand_days'] = sold['item_cnt_day'].groupby(sold['item_id']).mean()
items_df['cv2'] = items_df['var_demand_days'] / (items_df['mean_demand_days'] ** 2)


# %%
items_df['ADI'] = items_df['interarrival'].apply(np.mean)

print(items_df['ADI'].describe())

# %%
q3_adi = items_df["ADI"].quantile(0)
q3_zero_ratio = items_df["zero_ratio"].quantile(0)
q3_cv2 = items_df["cv2"].quantile(0)


filter_items = items_df


print(filter_items.describe())

# %%
items_df.to_csv("src/data/processed/items_zero_ratio_days_sold.csv", index=True)

# %%
items_df['ADI'].hist(bins=100)
plt.xlabel('ADI')
plt.ylabel('Number of items')
plt.title(' Distribution of ADI perItem')
plt.show()


# %%
df_visual = filter_items[["ADI", "cv2", "zero_ratio"]].dropna().copy()


def label_demand(row, coe_adi=1.32, coe_cv2=0.49, coe_zero_ratio=0.6):
    # Nếu ADI cao hoặc zero_ratio lớn → Intermittent/Lumpy (Gián đoạn)
    if row["ADI"] > coe_adi or row["zero_ratio"] >= coe_zero_ratio:
        # Nếu CV² thấp → Intermittent (Gián đoạn & Ổn định)
        if row["cv2"] < coe_cv2:
            return 2  # Intermittent
        else:
            return 0  # Lumpy (Gián đoạn & Biến động)
    else:
        # Nếu ADI thấp và zero_ratio nhỏ → Smooth/Erratic (Thường xuyên)
        # Bất kể CV² cao hay thấp, trường hợp này đều được gán là Smooth
        return 1  # Smooth (Bao gồm cả Smooth và Erratic)


df_visual["demand_type"] = df_visual.apply(
    lambda x: label_demand(
        x,
        coe_adi=df_visual["ADI"].mean(),
        coe_cv2=df_visual["cv2"].mean(),
        coe_zero_ratio=df_visual["zero_ratio"].mean(),
    ),
    axis=1,
)

name_mapping = {0: "Lumpy", 1: "Smooth", 2: "Intermittent"}

print(df_visual["demand_type"].value_counts())

print(df_visual[df_visual["demand_type"] == 2].head())
print(df_visual[df_visual["demand_type"] == 2].describe())
print(df_visual[df_visual["demand_type"] == 2].sample())

# %%
df_filtered = df[df['item_id'] == 1407.0]


# %%
import plotly.express as px

df_visual["demand_type_name"] = df_visual["demand_type"].map(name_mapping)

# Vẽ 3D scatter Plotly
fig = px.scatter_3d(
    df_visual,
    x="ADI",
    y="cv2",
    z="zero_ratio",
    color="demand_type_name",  # dùng cột tên loại demand
    labels={
        "ADI": "ADI",
        "cv2": "CV²",
        "zero_ratio": "Zero Ratio",
        "demand_type_name": "Demand Type"
    },
    title="Interactive 3D Segmentation for Intermittent Demand"
)

# Không cần hover
fig.update_traces(hoverinfo="skip", hovertemplate=None)

# Marker nhỏ, trong suốt vừa phải
fig.update_traces(marker=dict(size=5, opacity=0.8))
fig.update_layout(legend_title_text="Demand Type")

fig.show()



