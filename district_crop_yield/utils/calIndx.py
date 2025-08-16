import ee


ee.Initialize(project='concise-complex-428704-s9')

# ---- Step 1: Load shapefile ----
districts = ee.FeatureCollection("projects/concise-complex-428704-s9/assets/india_districts")

def calculate_indices_data(year, district):
    """
    Fetch MODIS indices data for given district/year
    and aggregate into a single yearly record for model prediction.
    
    Returns:
        dict: aggregated features ( yearly averages / totals )
    """
    # Get lat/lon for district

    start_date = ee.Date.fromYMD(year, 11, 1)   # Nov 1
    end_date = ee.Date.fromYMD(year + 1, 2, 28) # Feb 28

    district = districts.filter(ee.Filter.eq("NAME_2", district))

    # Load Sentinel-2 SR
    s2 = ee.ImageCollection("COPERNICUS/S2_SR") \
        .filterBounds(district) \
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
                                  geometry=district.geometry(),
                                  scale=10,
                                  maxPixels=1e13
                              )
    result =  ee.Dictionary(mean_indices).set('year', year)
    result = result.getInfo()  # Convert to Python dict
    final_result = {
        "year": year,
        "district": district,
        "ndvi": result.get('NDVI'),
        "evi": result.get('EVI'),
        "ndwi": result.get('NDWI')
    }

    return final_result

