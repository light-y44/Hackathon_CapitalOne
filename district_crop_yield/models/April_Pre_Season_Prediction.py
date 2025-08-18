import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error


# ---------------------------
# 1. Data loading & cleaning
# ---------------------------
def load_april_data(filepath: str) -> pd.DataFrame:
    df = pd.read_excel(filepath)
    df = df.rename(columns={
        'Market Name': 'Market',
        'Price Date': 'Date',
        'Modal Price (Rs./Quintal)': 'Price'
    })
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Year'] = df['Date'].dt.year
    df['Day'] = df['Date'].dt.day
    return df


# ---------------------------
# 2. Prepare features
# ---------------------------
def prepare_features(df: pd.DataFrame, train_years: list, test_year: int):
    train_df = df[df['Year'].isin(train_years)]
    test_df  = df[df['Year'] == test_year]

    # One-hot encode categorical "Market"
    X_train = pd.get_dummies(train_df[['Market','Year','Day']], drop_first=True)
    y_train = train_df['Price']

    X_test = pd.get_dummies(test_df[['Market','Year','Day']], drop_first=True)
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)  # align cols
    y_test = test_df['Price']

    return X_train, y_train, X_test, y_test


# ---------------------------
# 3. Train & Evaluate
# ---------------------------
def train_and_evaluate(X_train, y_train, X_test, y_test):
    model = RandomForestRegressor(n_estimators=300, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred)/y_test)) * 100
    
    avg_pred = np.mean(y_pred)
    avg_actual = np.mean(y_test)
    
    return model, y_pred, {
        "rmse": rmse,
        "mae": mae,
        "mape": mape,
        "avg_pred": avg_pred,
        "avg_actual": avg_actual
    }


# ---------------------------
# 4. Wrapper Pipeline
# ---------------------------
def april_forecast_pipeline(train_path, test_path, train_years, test_year):
    df_train = load_april_data(train_path)
    df_test  = load_april_data(test_path)
    df_all   = pd.concat([df_train, df_test], ignore_index=True)

    X_train, y_train, X_test, y_test = prepare_features(df_all, train_years, test_year)
    model, y_pred, metrics = train_and_evaluate(X_train, y_train, X_test, y_test)
    return model, y_pred, metrics


# ## Usuage Example
# model, y_pred, metrics = april_forecast_pipeline(
#     "/content/All_Combined_April.xlsx",      # 2020–2024
#     "/content/All_Combined_April_2025.xlsx", # 2025
#     train_years=[2020,2021,2022,2023,2024],
#     test_year=2025
# )

# print("Test RMSE:", metrics["rmse"])
# print("Test MAE:", metrics["mae"])
# print("Test MAPE:", metrics["mape"], "%")
# print("Predicted Avg April 2025 Price:", metrics["avg_pred"])
# print("Actual Avg April 2025 Price:", metrics["avg_actual"])
