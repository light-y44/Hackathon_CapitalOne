import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

# ------------------------
# CONFIG
# ------------------------
EPOCHS = 200
PATIENCE = 15
LR = 0.001
WEIGHT_DECAY = 1e-4
DATA_PATH = "./../data/full_data_crop_yield.csv"
MODEL_PATH = "crop_yield_model_weights.pth"

# ------------------------
# DATA PREPROCESSING
# ------------------------
def preprocess_data(df):
    label_encoders = {}
    for col in ['crop_type', 'district']:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        label_encoders[col] = le

    X = df[['T2M', 'PRECTOTCORR', 'ALLSKY_SFC_SW_DWN', 
            'NDVI', 'EVI', 'NDWI', 'Area', 'crop_type', 'district']].values
    y = df['Crop_yield'].values

    scaler = StandardScaler()
    X[:, :9] = scaler.fit_transform(X[:, :9])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    X_train = torch.tensor(X_train, dtype=torch.float32)
    X_test = torch.tensor(X_test, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.float32).view(-1, 1)
    y_test = torch.tensor(y_test, dtype=torch.float32).view(-1, 1)

    return X_train, X_test, y_train, y_test, scaler, label_encoders

# ------------------------
# MODEL
# ------------------------
class YieldNN(nn.Module):
    def __init__(self, input_dim):
        super(YieldNN, self).__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(64, 32), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        return self.layers(x)

# ------------------------
# TRAINING LOOP
# ------------------------
def train_model(model, X_train, y_train, X_test, y_test):
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)

    best_val_loss = float('inf')
    counter = 0

    for epoch in range(EPOCHS):
        # Train
        model.train()
        optimizer.zero_grad()
        outputs = model(X_train)
        loss = criterion(outputs, y_train)
        loss.backward()
        optimizer.step()

        # Validate
        model.eval()
        with torch.no_grad():
            val_outputs = model(X_test)
            val_loss = criterion(val_outputs, y_test)

        # Early stopping
        if val_loss.item() < best_val_loss:
            best_val_loss = val_loss.item()
            counter = 0
        else:
            counter += 1
            if counter >= PATIENCE:
                print(f"Early stopping at epoch {epoch+1}")
                break

        if (epoch+1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{EPOCHS}] - Train Loss: {loss.item():.4f} - Val Loss: {val_loss.item():.4f}")

    return model

# ------------------------
# EVALUATION
# ------------------------
def evaluate_model(model, X_test, y_test):
    model.eval()
    with torch.no_grad():
        y_pred = model(X_test).numpy()
    mse = mean_squared_error(y_test.numpy(), y_pred)
    r2 = r2_score(y_test.numpy(), y_pred)
    print(f"Test MSE: {mse:.4f}")
    print(f"Test R²: {r2:.4f}")
    return y_pred

# ------------------------
# MAIN SCRIPT
# ------------------------
if __name__ == "__main__":
    df = pd.read_csv(DATA_PATH)
    X_train, X_test, y_train, y_test, scaler, encoders = preprocess_data(df)

    model = YieldNN(input_dim=X_train.shape[1])
    model = train_model(model, X_train, y_train, X_test, y_test)

    y_pred = evaluate_model(model, X_test, y_test)

    torch.save(model.state_dict(), MODEL_PATH)
    print(f"Model weights saved to {MODEL_PATH}")
