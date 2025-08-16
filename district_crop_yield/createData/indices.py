import ee
import pandas as pd
import os

# Initialize Earth Engine

ee.Initialize(project='concise-complex-428704-s9')


# ---- Step 1: Load shapefile ----
districts = ee.FeatureCollection("projects/concise-complex-428704-s9/assets/india_districts")
coord_df = pd.read_csv("./../data/district wise centroids.csv")
coord_df_mp = coord_df[coord_df['State'] == "Madhya Pradesh"]
new_district = coord_df['District'].tolist()
district_names = new_district

OUTPUT_dir = './../data/mp_indicies_data'
if not os.path.exists(OUTPUT_dir):
    os.makedirs(OUTPUT_dir)

# ---- Step 2: Define Rabi season range and processing logic ----
def get_rabi_indices_for_year(year, district_name):
    start_date = ee.Date.fromYMD(year, 11, 1)   # Nov 1
    end_date = ee.Date.fromYMD(year + 1, 2, 28) # Feb 28

    # Load Sentinel-2 SR
    s2 = ee.ImageCollection("COPERNICUS/S2_SR") \
        .filterBounds(district_name) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))

    # Cloud masking using QA60
    def mask_clouds(image):
        cloud_prob = image.select('MSK_CLDPRB')
        mask = cloud_prob.lt(20)  # keep pixels with <20% cloud probability
        return image.updateMask(mask)

    s2_clean = s2.map(mask_clouds)

    # Calculate indices
    def add_indices(image):
        nir = image.select('B8')
        red = image.select('B4')
        green = image.select('B3')
        swir = image.select('B11')
        blue = image.select('B2')

        ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
        evi = nir.subtract(red).multiply(2.5) \
              .divide(nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)) \
              .rename('EVI')
        ndwi = nir.subtract(swir).divide(nir.add(swir)).rename('NDWI')

        return image.addBands([ndvi, evi, ndwi])

    s2_indices = s2_clean.map(add_indices)

    # Mean over season
    mean_indices = s2_indices.select(['NDVI', 'EVI', 'NDWI']) \
                              .mean() \
                              .reduceRegion(
                                  reducer=ee.Reducer.mean(),
                                  geometry=district_name.geometry(),
                                  scale=10,
                                  maxPixels=1e13
                              )
    return ee.Dictionary(mean_indices).set('year', year)

for district in district_names:
    print(f"Processing for {district}")
    district_name = districts.filter(ee.Filter.eq("NAME_2", district))

    # ---- Step 3: Loop through years and build a list of EE Dictionaries ----
    years = list(range(2018, 2023))
    results_list = [get_rabi_indices_for_year(y, district_name) for y in years]

    # ---- Step 4: Convert to a FeatureCollection and get results with a single call ----
    results_collection = ee.FeatureCollection(
        [ee.Feature(None, item) for item in results_list]
    )
    print(f"Fetching information")
    all_results = results_collection.getInfo()
    data = [f['properties'] for f in all_results['features']]
    df = pd.DataFrame(data)
    df = df[['year', 'NDVI', 'EVI', 'NDWI']]
    df['district'] = district

    filename = os.path.join(OUTPUT_dir, f"{district.lower().replace(' ', '_')}_indicies_2018_2023.csv")

    # Save CSV
    df.to_csv(filename, index=False)

input_folder = './../data/mp_indicies_data'
output_file = './../data/mp_all_district_indicies.csv'
all_dataframes = []
csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
for filename in csv_files:
        file_path = os.path.join(input_folder, filename)
        try:
            df = pd.read_csv(file_path)
            all_dataframes.append(df)
            print(f"  - Successfully read '{filename}'")
        except Exception as e:
            print(f"❌ Error reading '{filename}': {e}")
combined_df = pd.concat(all_dataframes, ignore_index=True)
        
# Save the combined DataFrame to a new CSV file
combined_df.to_csv(output_file, index=False)     
