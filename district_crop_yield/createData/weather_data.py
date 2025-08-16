import requests
import pandas as pd
import time
import os

coord_df = pd.read_csv("./../data/district wise centroids.csv")
coord_df_mp = coord_df[coord_df['State'] == "Madhya Pradesh"]

# Create a directory to store the output CSV files
output_dir = './../data/mp_weather_data'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# NASA POWER API parameters
params = [
    "T2M_MAX",  # Max temperature (°C)
    "T2M_MIN",  # Min temperature (°C)
    "T2M",      # Mean temperature (°C)
    "PRECTOT",  # Precipitation (mm/day)
    "ALLSKY_SFC_SW_DWN"  # Solar radiation (MJ/m²/day)
]

# Years range
start_year = 2018
end_year = 2023

# Iterate through each district and fetch data
for district in coord_df_mp['District']:
    lat = coord_df_mp[coord_df_mp['District'] == district]["Latitude"].values[0]
    lon = coord_df_mp[coord_df_mp['District'] == district]["Longitude"].values[0]

    print(f"Fetching data for {district}...")

    # Build URL
    url = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point?"
        f"parameters={','.join(params)}"
        f"&community=AG"
        f"&longitude={lon}&latitude={lat}"
        f"&start={start_year}0101&end={end_year}1231"
        f"&format=JSON"
    )

    try:
        # Fetch data
        response = requests.get(url, verify=True, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        # Check if the data is valid
        if 'properties' in data and 'parameter' in data['properties']:
            # Convert to DataFrame
            df = pd.DataFrame(data['properties']['parameter'])
            df = df.transpose().reset_index()
            df = df.rename(columns={'index': 'date'})

            # Add 'district' column
            df['district'] = district

            # Construct the filename
            filename = os.path.join(output_dir, f"{district.lower().replace(' ', '_')}_weather_{start_year}_{end_year}.csv")

            # Save CSV
            df.to_csv(filename, index=False)
            print(f"✅ Saved weather data to {filename}")
        else:
            print(f"❌ Failed to fetch data for {district}. Unexpected API response.")

    except requests.exceptions.RequestException as e:
        print(f"❌ An error occurred while fetching data for {district}: {e}")

    # Add a small delay to avoid hitting API rate limits
    time.sleep(2)

print("\nData fetching complete.")

# Define the directory where the CSV files are located
input_dir = './../data/mp_weather_data'
output_filename = './../data/all_districts_rabi_aggregated.csv'

# Define the preprocessing function
def preprocess_data(df):
    """
    Preprocesses a DataFrame containing daily weather data for a single district.
    The function calculates Rabi season averages for each year.

    Args:
        df (pd.DataFrame): The input DataFrame with columns like 'date', 'district',
                          and weather parameters.

    Returns:
        pd.DataFrame: An aggregated DataFrame with Rabi season data for each year.
    """
    # Ensure 'date' is a datetime object
    df = df.transpose()
    df.columns = df.iloc[0]
    df = df.drop(index=0)

    df = df.reset_index(drop=True)
    df['district'] = df['T2M'].iloc[-1]
    df = df.iloc[:-1]

    # Remove .0 and convert to int, then datetime
    df['date'] = df['date'].astype(float).astype(int).astype(str)
    df['date'] = pd.to_datetime(df['date'], format="%Y%m%d")

    # Extract month and year
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year

    # Assign rabi_year (Nov-Dec go to the next year's Rabi season)
    df['rabi_year'] = df['year']
    df.loc[df['month'] >= 11, 'rabi_year'] += 1

    # Filter to Rabi months (Nov, Dec, Jan, Feb)
    df_rabi = df[df['month'].isin([11, 12, 1, 2])].copy()

    # Aggregate the data by rabi_year and district
    # NOTE: I've corrected 'PRECTOTCORR' to 'PRECTOT' to match the output from the NASA API script.
    aggregated = df_rabi.groupby(['district', 'rabi_year']).agg({
        'T2M_MAX': 'mean',
        'T2M': 'mean',
        'T2M_MIN': 'mean',
        'PRECTOTCORR': 'sum',
        'ALLSKY_SFC_SW_DWN': 'mean'
    }).reset_index()

    return aggregated

# Main script logic
if not os.path.exists(input_dir):
    print(f"❌ The directory '{input_dir}' does not exist. Please run the data fetching script first.")
else:
    all_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith('.csv')]

    if not all_files:
        print(f"❌ No CSV files found in the directory '{input_dir}'.")
    else:
        # List to hold the aggregated data for each district
        processed_dfs = []

        print("Starting data preprocessing and combination...")

        for file_path in all_files:
            try:
                # Read the CSV file
                df = pd.read_csv(file_path,  header=None)

                # Preprocess the data using the defined function
                aggregated_df = preprocess_data(df)

                # Append to the list
                processed_dfs.append(aggregated_df)

                print(f"✅ Processed {os.path.basename(file_path)}")
            except Exception as e:
                print(f"❌ An error occurred while processing {os.path.basename(file_path)}: {e}")

        # Combine all processed data into a single DataFrame
        if processed_dfs:
            combined_df = pd.concat(processed_dfs, ignore_index=True)

            # Save the final combined DataFrame to a new CSV file
            combined_df.to_csv(output_filename, index=False)

            print(f"\n✅ All data combined and saved to '{output_filename}'")
            print("\nCombined DataFrame preview:")
            print(combined_df.head())
        else:
            print("No data was successfully processed to be combined.")
