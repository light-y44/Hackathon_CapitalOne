import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error

# ---------------------------
# 1. Load datasets
# ---------------------------
nov_feb_df = pd.read_excel("/content/All_Combined.xlsx")  # Nov-Feb prices
april_df = pd.read_excel("/content/All_Combined_April.xlsx")  # April prices

# Rename columns for easier access
nov_feb_df = nov_feb_df.rename(columns={
    'Market Name': 'Market',
    'Price Date': 'Date',
    'Modal Price (Rs./Quintal)': 'Price'
})

april_df = april_df.rename(columns={
    'Market Name': 'Market',
    'Price Date': 'Date',
    'Modal Price (Rs./Quintal)': 'Price'
})

# Ensure Date column is datetime
nov_feb_df['Date'] = pd.to_datetime(nov_feb_df['Date'], errors='coerce')
april_df['Date'] = pd.to_datetime(april_df['Date'], errors='coerce')

# ---------------------------
# 2. Prepare features and targets
# ---------------------------
X = []
y = []

years = sorted(nov_feb_df['Date'].dt.year.unique())
markets = nov_feb_df['Market'].unique()

for year in years:
    for market in markets:
        mask_features = (((nov_feb_df['Date'].dt.year == year-1) & (nov_feb_df['Date'].dt.month >= 11)) |
                         ((nov_feb_df['Date'].dt.year == year) & (nov_feb_df['Date'].dt.month <= 2))) & \
                        (nov_feb_df['Market'] == market)
        
        X_seq = nov_feb_df.loc[mask_features, 'Price'].values
        if len(X_seq) == 0:
            continue
        
        mask_target = (april_df['Date'].dt.year == year) & (april_df['Market'] == market)
        y_val = april_df.loc[mask_target, 'Price'].mean()
        if np.isnan(y_val):
            continue
        
        X.append(X_seq)
        y.append(y_val)

# ---------------------------
# 3. Align sequence lengths
# ---------------------------
max_len = max([len(seq) for seq in X])
X_padded = np.array([np.pad(seq, (0, max_len-len(seq)), mode='edge') for seq in X])
y = np.array(y)

# ---------------------------
# 4. Train-test split
# ---------------------------
X_train, X_test, y_train, y_test = train_test_split(X_padded, y, test_size=0.2, random_state=42)

# ---------------------------
# 5. Train model
# ---------------------------
model = RandomForestRegressor(n_estimators=300, random_state=42)
model.fit(X_train, y_train)

# ---------------------------
# 6. Evaluate
# ---------------------------
y_pred = model.predict(X_test)
print(y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae = mean_absolute_error(y_test, y_pred)
mape = np.mean(np.abs((y_test - y_pred)/y_test)) * 100

print(f"Test RMSE: {rmse:.2f}, MAE: {mae:.2f}, MAPE: {mape:.2f}%")

# ---------------------------
# 7. Predict next year April mean price per market
# ---------------------------
forecast_next = {}
latest_year = nov_feb_df['Date'].dt.year.max()+ 1

for market in markets:
    mask_next = (((nov_feb_df['Date'].dt.year == latest_year-1) & (nov_feb_df['Date'].dt.month >= 11)) |
                 ((nov_feb_df['Date'].dt.year == latest_year) & (nov_feb_df['Date'].dt.month <= 2))) & \
                (nov_feb_df['Market'] == market)
    X_next_seq = nov_feb_df.loc[mask_next, 'Price'].values
    if len(X_next_seq) == 0:
        continue
    if len(X_next_seq) < max_len:
        X_next_seq = np.pad(X_next_seq, (0, max_len-len(X_next_seq)), mode='edge')
    forecast_next[market] = model.predict(X_next_seq.reshape(1,-1))[0]

print("Predicted April mean prices for next year:")
for market, price in forecast_next.items():
    print(f"{market}: {price:.2f}")