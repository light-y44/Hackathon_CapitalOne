import numpy as np
import os 
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
import sys
import torch
import joblib
from huggingface_hub import login
from deep_translator import GoogleTranslator
from models.Mid_season_price_prediction import evaluate_model

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),  '..')))
from models.crop_yield import YieldNN

current_dir = os.path.dirname(__file__) 
district_area_path = os.path.join(current_dir, "../data/all_crops_all_districts.csv")
scaler_path = os.path.join(current_dir, "../models/scaler.pkl")
crop_en_path = os.path.join(current_dir, "../models/crop_type_encoder.pkl")
dist_en_path = os.path.join(current_dir, "../models/district_encoder.pkl")
weights_path = os.path.join(current_dir, "../models/crop_yield_model_weights.pth")
price_weight_path = os.path.join(current_dir, "../models/midseason_predictor.pkl")
price_pred_file_path = os.path.join(current_dir, "../data/preprocessed_all_combined_novtofeb.xlsx")

area_df = pd.read_csv(district_area_path)

scaler = joblib.load(scaler_path)
crop_le = joblib.load(crop_en_path)
district_le = joblib.load(dist_en_path)

label_encoders = {'crop_type': crop_le, 'district': district_le}

price_model = joblib.load(price_weight_path)
area_df = pd.read_csv(district_area_path)
model = YieldNN(input_dim=9)
model.load_state_dict(torch.load(weights_path))
model.eval()

price_df = pd.read_excel(price_pred_file_path, header=None)
price_df = price_df.iloc[1:]
price_df.drop(price_df.columns[0], axis=1, inplace=True)

def preprocess_single_sample(input_dict, label_encoders, scaler):
    """
    Preprocess a single data point dictionary for model prediction.
    
    Args:
        input_dict (dict): Dictionary with keys:
            'T2M', 'PRECTOTCORR', 'ALLSKY_SFC_SW_DWN', 'NDVI', 'EVI', 'NDWI', 'Area', 'crop_type', 'district'
        label_encoders (dict): Pre-fitted LabelEncoders for 'crop_type' and 'district'.
        scaler (StandardScaler): Pre-fitted StandardScaler for numerical features.
        
    Returns:
        np.ndarray: Preprocessed feature array ready for model input.
    """
    feature_order = ['T2M', 'PRECTOTCORR', 'ALLSKY_SFC_SW_DWN',
                     'NDVI', 'EVI', 'NDWI', 'Area', 'crop_type', 'district']

    features = []
    for feature in feature_order:
        val = input_dict[feature]
        if feature in ['crop_type', 'district']:
            val = label_encoders[feature].transform([val])[0]
        features.append(val)
    
    features = np.array(features, dtype=float)
    
    # Scale only numerical features (first 7)
    features = scaler.transform([features])[0]
    
    return features

if __name__ == "__main__":
    input_data = {
        'T2M': 25.0,
        'PRECTOTCORR': 5.0,
        'ALLSKY_SFC_SW_DWN': 200.0,
        'NDVI': 0.5,
        'EVI': 0.6,
        'NDWI': 0.3,
        'Area': 100.0,
        'crop_type': 'Wheat',
        'district': 'District A'
    }

    # Example: load pre-fitted encoders and scaler
    crop_le = LabelEncoder()
    crop_le.classes_ = np.array(['Wheat', 'Rice', 'Maize'])
    
    district_le = LabelEncoder()
    district_le.classes_ = np.array(['District A', 'District B', 'District C'])
    
    scaler = StandardScaler()
    # Fit on some training data numerical features: example
    scaler.mean_ = np.array([20, 2, 150, 0.4, 0.5, 0.2, 80])
    scaler.scale_ = np.array([5, 1, 50, 0.1, 0.1, 0.1, 20])

    label_encoders = {'crop_type': crop_le, 'district': district_le}

    preprocessed_sample = preprocess_single_sample(input_data, label_encoders, scaler)
    print(preprocessed_sample)


def calulateArea(district, crop, year):
    """
    Calculate area for a given district, crop, and year.
    
    Args:
        district (str): Name of the district.
        crop (str): Type of crop.
        year (int): Year for which the area is calculated.
        
    Returns:
        float: Area of the farm in the specified district and crop.
    """
    filtered = area_df[
        (area_df['district'] == district) &
        (area_df['crop_type'] == crop) &
        (area_df['Year'] == year)
    ]
    
    if not filtered.empty:
        return filtered['area'].values[0]

    return None


def calculateYieldPred(weather_df, indices_df, area_district, crop, district):
    """
    Calculate yield prediction based on weather and indices data.
    
    Args:
        weather_df (pd.DataFrame): DataFrame containing weather data.
        indices_df (pd.DataFrame): DataFrame containing indices data.
        area (float): Area of the farm.
        crop (str): Type of crop.
        district (str): Name of the district.
        
    Returns:
        float: Predicted yield for the specified crop and district.
    """
    input_data = {
        'T2M': weather_df['avg_temp'],               # Example key names
        'PRECTOTCORR': weather_df['total_rainfall'],
        'ALLSKY_SFC_SW_DWN': weather_df['avg_solar_radiation'],
        'NDVI': indices_df['ndvi'],
        'EVI': indices_df['evi'],
        'NDWI': indices_df['ndwi'],
        'Area': area_district,
        'crop_type': crop,
        'district': district
    }

    print(input_data)
    # Preprocess the single sample using pre-fitted scaler and label encoders
    # Assume these are loaded globally or elsewhere

    preprocessed_sample = preprocess_single_sample(
        input_data, 
        label_encoders=label_encoders, 
        scaler=scaler
    )

    # Convert to torch tensor for model prediction
    X_tensor = torch.tensor(preprocessed_sample, dtype=torch.float32).unsqueeze(0)  # shape [1, num_features]
    # Predict crop yield
    model.eval()
    with torch.no_grad():
        predicted_yield = model(X_tensor).item()

    # Get the year from the input data
    predicted_price = evaluate_model(price_model, price_df)
    print(f"Predicted price: {predicted_price} and Predicted yield: {predicted_yield}")
    return predicted_yield, predicted_price


def huggingFaceAuth():
    """
    Authenticate with Hugging Face using the token stored in the environment variable.
    
    Returns:
        bool: True if authentication is successful, False otherwise.
    """
    try:
        token = os.getenv("HUGGINGFACE_TOKEN")
        if not token:
            raise ValueError("HUGGINGFACE_TOKEN environment variable not set.")
        login(token=token)
        return True
    except Exception as e:
        print(f"Authentication failed: {e}")
        return False




def translate_hi_to_en(text: str) -> str:
    """
    Translates Hindi text into English using Google Translator (deep-translator).
    
    Args:
        text (str): Input text in Hindi.
    
    Returns:
        str: Translated English text.
    """
    return GoogleTranslator(source="hi", target="en").translate(text)


def translate_en_to_hi(text: str) -> str:
    """
    Translates English text into Hindi using Google Translator (deep-translator).

    Args:
        text (str): Input text in English.

    Returns:
        str: Translated Hindi text.
    """
    return GoogleTranslator(source="en", target="hi").translate(text)
    