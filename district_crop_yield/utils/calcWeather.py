import requests
import pandas as pd
import os

current_dir = os.path.dirname(__file__)   # The folder this script is in
target_path = os.path.join(current_dir, "../data/district_wise_centroids.csv")

def calculate_weather_data(year, district):
    """
    Fetch NASA POWER daily weather data for given district/year
    and aggregate into a single yearly record for model prediction.
    
    Returns:
        dict: aggregated features ( yearly averages / totals )
    """
    # Load district coordinates
    coord_df = pd.read_csv(target_path)
    coord_df_mp = coord_df[coord_df['State'] == "Madhya Pradesh"]

    # Get lat/lon for district
    lat = coord_df_mp.loc[coord_df_mp['District'] == district, "Latitude"].values[0]
    lon = coord_df_mp.loc[coord_df_mp['District'] == district, "Longitude"].values[0]

    print(lat, lon)

    params = [
        "T2M_MAX", "T2M_MIN", "T2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN"
    ]

    url = (
        "https://power.larc.nasa.gov/api/temporal/daily/point?"
        f"parameters={','.join(params)}"
        f"&community=AG"
        f"&longitude={lon}&latitude={lat}"
        f"&start={year}1101&end={year+1}0228"
        f"&format=JSON"
    )

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        if 'properties' in data and 'parameter' in data['properties']:
            df = pd.DataFrame(data['properties']['parameter'])
            df.index.name = "date"
            df.reset_index(inplace=True)

            # Aggregate
            aggregated = {
                "year": year,
                "district": district,
                "avg_temp": df["T2M"].mean(),
                "avg_max_temp": df["T2M_MAX"].mean(),
                "avg_min_temp": df["T2M_MIN"].mean(),
                "total_rainfall": df["PRECTOTCORR"].sum(),
                "avg_solar_radiation": df["ALLSKY_SFC_SW_DWN"].mean()
            }

            return aggregated
        else:
            print(f"❌ Unexpected API response format for {district}.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch data for {district}: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    year = 2025
    district = "Bhopal"
    weather_data = calculate_weather_data(year, district)
    if weather_data:
        print(f"Weather data for {district} in {year}: {weather_data}")
    else:
        print("Failed to fetch weather data.")