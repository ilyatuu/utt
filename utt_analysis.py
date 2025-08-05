# UTT Analysis
#%%
# imports
import pandas as pd
import matplotlib.pyplot as plt
import chardet  # Detect encoding

#%%
# read data
with open('data/data.csv', 'rb') as file:
    result = chardet.detect(file.read())
    encoding = result['encoding']

df = pd.read_csv('data/data.csv',encoding = encoding,low_memory = False)

#%%
# fix column names
df.columns = df.columns.str.replace(" ", "")
df.columns = df.columns.str.replace("/", "")
df.columns = df.columns.str.replace("SalePriceperUnit", "SalePricePerUnit")
print(f"Shape of the dataframe: {df.shape}")
df.head()

#%%
# define a function to clean numbers
def clean_numeric_columns(df):
    for col in df.columns:
        if df[col].dtype == 'object':
            # Remove commas and whitespace
            cleaned = df[col].str.replace(',', '', regex=True).str.strip()
            # Attempt conversion to numeric
            converted = pd.to_numeric(cleaned, errors='coerce')
            # If conversion yields valid numbers, replace the column
            if converted.notna().sum() > 0:
                df[col] = converted
    return df

#%%
# Apply data cleaning using the defined function
df = clean_numeric_columns(df)
df = df.astype({'SalePricePerUnit': float, 'RepurchasePriceUnit': float, 'OutstandingNumberofUnits':float, 'NetAssetValue':float})
df['DateValued'] = pd.to_datetime(df['DateValued'], format='%d-%m-%Y', dayfirst=True, errors='coerce') # fix bad dates
df = df.dropna(subset=["DateValued", "NetAssetValue"])                              # drop bad dates

#%%
## clean dates
## Option 1: delete all before 2020-01-01
# df = df[df["DateValued"] >= "2020-01-01"]

# # Option 2: Use the upper bound instead
# pre_2016 = df[df["DateValued"] < "2016-01-01"]
# q1 = pre_2016["NetAssetValue"].quantile(0.25)
# q3 = pre_2016["NetAssetValue"].quantile(0.75)
# iqr = q3 - q1
# upper_bound = q3 + 1.5 * iqr
# # Cap outliers to upper bound
# df.loc[(df["DateValued"] < "2016-01-01") & (df["NetAssetValue"] > upper_bound), "NetAssetValue"] = upper_bound

# Option 2
# Replace outliers with mean of previous and next values
outlier_indices = df[(df["DateValued"] < "2016-01-01") & (df["NetAssetValue"] > upper_bound)].index

for idx in outlier_indices:
    if idx > 0 and idx < len(df) - 1:
        prev_val = df.loc[idx - 1, "NetAssetValue"]
        next_val = df.loc[idx + 1, "NetAssetValue"]
        if pd.notna(prev_val) and pd.notna(next_val):
            df.loc[idx, "NetAssetValue"] = (prev_val + next_val) / 2


#%%
# keep copy
df2 = df
# reuse the copy

#%%
## If dates are discontinuous, resample to fill gaps (e.g., weekends/holidays)
# first drop duplicates
df = df2
df = df.drop_duplicates(
    subset=["SchemeName", "DateValued"], 
    keep="last"  # or "first"
)

# then resample safely
df = (
    df.drop_duplicates(["SchemeName", "DateValued"])
    .set_index("DateValued")
    .groupby("SchemeName")
    .apply(lambda group: group.resample("D").ffill())  # Explicitly resample each group
    .reset_index(level=0, drop=True)  # Clean up index
    .reset_index()
)

#%%
# Calcualte profit
df["Profit"] = df["SalePricePerUnit"] - df["RepurchasePriceUnit"]
df["ProfitMargin"] = (df["Profit"] / df["SalePricePerUnit"]) * 100
# Group by SchemeName and calculate average profit margin
avg_profit_margin = df.groupby("SchemeName")["ProfitMargin"].mean().sort_values(ascending=False)
avg_profit_margin.plot(kind='bar', color='skyblue')


#%%
# Calculate percentage change
# the following calculations requires the dataset to be sorted
df = df.sort_values(["SchemeName", "DateValued"]).reset_index(drop=True)

df['DailyReturn'] = df.groupby('SchemeName')['NavPerUnit'].pct_change() * 100
df[df['SchemeName']=='Umoja Fund'].plot(x='DateValued', y='DailyReturn', title='DailyReturn Plot')

# Create a 7-day moving average per scheme and 7-day volatility
df["NAV_MA7"] = df.groupby("SchemeName")["NetAssetValue"].transform(lambda x: x.rolling(window=7, min_periods=1).mean())
df['7DVolatility'] = df.groupby('SchemeName')['DailyReturn'].transform(lambda x: x.rolling(window=7, min_periods=1).std())



#%%
# Plot NAV trend and moving average
plt.figure(figsize=(14, 7))
for scheme in df["SchemeName"].unique():
    scheme_data = df[df["SchemeName"] == scheme]
    plt.plot(scheme_data["DateValued"], scheme_data["NetAssetValue"], label=f"{scheme} NAV", alpha=0.4)
    plt.plot(scheme_data["DateValued"], scheme_data["NAV_MA7"], label=f"{scheme} MA7")

plt.title("NAV Trend Over Time by Scheme (with 7-Day Moving Average)")
plt.xlabel("Date")
plt.ylabel("Net Asset Value")
plt.legend(loc="upper left", fontsize=8)
plt.grid(True)
plt.tight_layout()
plt.show()

#%%
## more graphs
df[df['SchemeName']=='Umoja Fund'].plot(x='DateValued', y='NAV_MA7')


# %%
