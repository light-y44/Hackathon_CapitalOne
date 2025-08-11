import ee
import pandas as pd
from gee import gee_client
from models import yield_model
from config import settings

def main():
    gee_client.init_gee()
    print("Fetching indices from GEE...")
    fc = gee_client.get_index_timeseries()
    # Download small data directly to local
    df = pd.DataFrame(fc.getInfo()['features'])
    # Flatten properties
    df = pd.json_normalize(df['properties'])
    print(df.head())
    df.to_csv("data/processed/indices_timeseries.csv", index=False)

    # Suppose we already have ground truth yield column
    if 'yield' in df.columns:
        feature_cols = ['GNDVI','NDVI']  # choose best features later
        yield_model.train_model(df, feature_cols, 'yield')
    else:
        print("No yield column found — skipping model training.")

if __name__ == "__main__":
    main()
