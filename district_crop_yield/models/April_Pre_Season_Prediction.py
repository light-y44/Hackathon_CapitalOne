import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error

def forecast_april_price_with_accuracy(district_name ="Ashoknagar", date_col="Price Date", price_col="Modal Price (Rs./Quintal)", district_col="District Name", test_years=1):
    """
    Forecasts next April's price for a given district using SARIMA,
    splits data into train/test, and reports accuracy metrics.

    Parameters:
        file_path (str): Path to Excel file
        district_name (str): District name
        date_col (str): Date column name
        price_col (str): Price column name
        district_col (str): District column name
        test_years (int): Number of years to keep for testing

    Returns:
        dict: Forecast point estimate, confidence intervals, and accuracy metrics
    """

    # Load and preprocess
    df = pd.read_excel('C:\Users\naiti\OneDrive\Desktop\Dataset\Ashoknagar\filtered_April_Ashoknagar.xlsx')
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col, price_col, district_col])

    # Keep April only
    df = df[df[date_col].dt.month == 4]

    # Filter district
    df = df[df[district_col].str.strip().str.lower() == district_name.strip().lower()]
    if df.empty:
        raise ValueError(f"No April data for district '{district_name}'")

    # Aggregate to yearly April mean price
    df = df.groupby(df[date_col].dt.year)[price_col].mean().reset_index()
    df.columns = ["Year", "Price"]

    # Convert to time series
    df_ts = pd.Series(df["Price"].values, index=pd.PeriodIndex(df["Year"], freq='Y'))

    # Split train/test
    train = df_ts.iloc[:-test_years]
    test = df_ts.iloc[-test_years:]

    # Fit SARIMA model
    model = ARIMA(train, order=(1, 1, 1))
    model_fit = model.fit()

    # Forecast for test years
    forecast_test = model_fit.forecast(steps=test_years)
    rmse = np.sqrt(mean_squared_error(test, forecast_test))
    mae = mean_absolute_error(test, forecast_test)
    mape = np.mean(np.abs((test - forecast_test) / test)) * 100

    # Retrain on full data for next April
    model_full = ARIMA(df_ts, order=(1, 1, 1))
    model_full_fit = model_full.fit()
    forecast_next = model_full_fit.get_forecast(steps=1)

    mean_forecast = forecast_next.predicted_mean.iloc[0]
    conf_int_80 = forecast_next.conf_int(alpha=0.20).iloc[0]
    conf_int_95 = forecast_next.conf_int(alpha=0.05).iloc[0]

    result = {
        "district": district_name,
        "forecast_price": round(mean_forecast, 2),
        "80%_range": (round(conf_int_80.iloc[0], 2), round(conf_int_80.iloc[1], 2)),
        "95%_range": (round(conf_int_95.iloc[0], 2), round(conf_int_95.iloc[1], 2)),
        "accuracy": {
            "RMSE": round(rmse, 2),
            "MAE": round(mae, 2),
            "MAPE (%)": round(mape, 2)
        }
    }

    return result


forecast_result = forecast_april_price_with_accuracy( test_years=1)
print(forecast_result)