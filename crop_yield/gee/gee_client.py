import ee
from config import settings

def init_gee():
    """Initialize the Earth Engine API."""
    ee.Initialize()

def mask_s2_sr(image):
    cloud_prob = image.select('MSK_CLDPRB')
    mask = cloud_prob.lt(20)  # threshold %
    return image.updateMask(mask).copyProperties(image, ['system:time_start'])


def add_indices(img):
    """Add NDVI, GNDVI, EVI, WDVI, S2REP, and LAI bands."""
    nir = img.select('B8')
    red = img.select('B4')
    green = img.select('B3')
    blue = img.select('B2')
    re1 = img.select('B5')
    re2 = img.select('B6')

    ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
    gndvi = nir.subtract(green).divide(nir.add(green)).rename('GNDVI')
    evi = img.expression(
        '2.5*(NIR-RED)/(NIR+6*RED-7.5*BLUE+1)',
        {'NIR': nir, 'RED': red, 'BLUE': blue}
    ).rename('EVI')
    wdvi = nir.subtract(red.multiply(0.5)).rename('WDVI')
    s2rep = ee.Image(705).add(
        ee.Image(35).multiply(
            (nir.add(red).divide(2).subtract(re1)).divide(re2.subtract(re1))
        )
    ).rename('S2REP')
    lai = ndvi.expression('0.57 * exp(2.33 * NDVI)', {'NDVI': ndvi}).rename('LAI')

    return img.addBands([ndvi, gndvi, evi, wdvi, s2rep, lai])

def get_index_timeseries():
    """Fetch timeseries of vegetation indices for the configured ROI and dates."""
    roi = ee.Geometry.Polygon([settings.ROI_COORDS])

    s2 = (ee.ImageCollection('COPERNICUS/S2_SR')
            .filterBounds(roi)
            .filterDate(settings.START_DATE, settings.END_DATE)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', settings.CLOUD_THRESH))
            .map(mask_s2_sr)
            .map(add_indices))

    def img_to_feat(img):
        date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')
        stats = img.select(['NDVI','GNDVI','EVI','WDVI','S2REP','LAI']).reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=10,
            bestEffort=True,
            maxPixels=1e10
        )
        return ee.Feature(None, stats).set('date', date)

    fc = s2.map(img_to_feat).filter(ee.Filter.notNull(['NDVI']))
    return fc
