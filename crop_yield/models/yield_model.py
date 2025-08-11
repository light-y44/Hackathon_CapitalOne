import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
import numpy as np
import joblib
import os

MODEL_PATH = "data/models/yield_model.pkl"

def train_model(df, feature_cols, target_col):
    X = df[feature_cols].values
    y = df[target_col].values
    model = LinearRegression().fit(X, y)
    preds = model.predict(X)
    print("Training R²:", r2_score(y, preds))
    print("RMSE:", np.sqrt(mean_squared_error(y, preds)))
    joblib.dump(model, MODEL_PATH)
    return model

def load_model():
    return joblib.load(MODEL_PATH)

def predict_yield(df, feature_cols):
    model = load_model()
    return model.predict(df[feature_cols].values)
