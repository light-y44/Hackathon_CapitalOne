import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error


# ---------------------------
# 1. Data loading & cleaning
# ---------------------------
def load_and_clean(filepath: str) -> pd.DataFrame:
    df = pd.read_excel(filepath)
    df = df.rename(columns={
        'Market Name': 'Market',
        'Price Date': 'Date',
        'Modal Price (Rs./Quintal)': 'Price'
    })
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    return df


# ---------------------------
# 2. Dataset builder
# ---------------------------
def build_dataset(nov_feb_df: pd.DataFrame, april_df: pd.DataFrame) -> tuple:
    """Build (X, y) dataset: Nov–Feb sequence → April average."""
    X, y = [], []
    years = sorted(nov_feb_df['Date'].dt.year.unique())
    markets = nov_feb_df['Market'].unique()

    for year in years:
        for market in markets:
            # Nov (previous year) – Feb (current year)
            mask_features = (
                (((nov_feb_df['Date'].dt.year == year-1) & (nov_feb_df['Date'].dt.month >= 11)) |
                 ((nov_feb_df['Date'].dt.year == year) & (nov_feb_df['Date'].dt.month <= 2)))
                & (nov_feb_df['Market'] == market)
            )
            X_seq = nov_feb_df.loc[mask_features, 'Price'].values
            if len(X_seq) == 0:
                continue

            # April of same year
            mask_target = (april_df['Date'].dt.year == year) & (april_df['Market'] == market)
            y_val = april_df.loc[mask_target, 'Price'].mean()
            if np.isnan(y_val):
                continue

            X.append(X_seq)
            y.append(y_val)

    return X, y


# ---------------------------
# 3. Padding helper
# ---------------------------
def pad_sequences(X_list, max_len: int) -> np.ndarray:
    return np.array([np.pad(seq, (0, max_len-len(seq)), mode='edge') for seq in X_list])


# ---------------------------
# 4. Training & evaluation
# ---------------------------
def train_model(X_train: np.ndarray, y_train: np.ndarray) -> RandomForestRegressor:
    model = RandomForestRegressor(n_estimators=300, random_state=42)
    model.fit(X_train, y_train)
    return model


def load_and_preprocess_price_model(X_test_df):
    pass


def evaluate_model(model, X_test):
    y_pred = model.predict(X_test)

    # rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    # mae = mean_absolute_error(y_test, y_pred)
    # mape = np.mean(np.abs((y_test - y_pred)/y_test)) * 100
    return np.mean(y_pred)


# ---------------------------
# 5. Wrapper function
# ---------------------------
def run_pipeline(train_novfeb_path, train_april_path,
                 test_novfeb_path, test_april_path):

    # Load datasets
    nov_feb_train = load_and_clean(train_novfeb_path)
    april_train   = load_and_clean(train_april_path)
    nov_feb_test  = load_and_clean(test_novfeb_path)
    april_test    = load_and_clean(test_april_path)

    # Build train/test datasets
    X_train, y_train = build_dataset(nov_feb_train, april_train)
    X_test, y_test   = build_dataset(nov_feb_test, april_test)

    # Align sequence lengths
    max_len = max(max(len(seq) for seq in X_train), max(len(seq) for seq in X_test))
    X_train = pad_sequences(X_train, max_len)
    X_test  = pad_sequences(X_test, max_len)
    y_train, y_test = np.array(y_train), np.array(y_test)

    # Train model
    model = train_model(X_train, y_train)

    # Evaluate
    y_pred, rmse, mae, mape = evaluate_model(model, X_test, y_test)
    avg_pred = np.mean(y_pred)

    return {
        "model": model,
        "y_pred": y_pred,
        "y_test": y_test,
        "rmse": rmse,
        "mae": mae,
        "mape": mape,
        "avg_pred": avg_pred
    }
