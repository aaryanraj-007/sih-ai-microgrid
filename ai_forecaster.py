import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from fetch_cloud_data import fetch_real_antaws_data

class PolarMicrogridForecaster(nn.Module):
    """
    An LSTM-based neural network designed to ingest historical weather telemetry
    and predict future renewable energy generation potential.
    """
    def __init__(self, input_size=4, hidden_size=64, num_layers=2, output_size=2):
        super(PolarMicrogridForecaster, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layer
        # Inputs: 4 features [Temperature, Pressure, Wind_Speed, Solar_Irradiance]
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        
        # Fully connected layer to map LSTM outputs to the desired predictions
        # Outputs: 2 features [Predicted_Wind_Speed, Predicted_Solar_Irradiance]
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).requires_grad_()
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).requires_grad_()
        
        out, (hn, cn) = self.lstm(x, (h0.detach(), c0.detach()))
        out = self.fc(out[:, -1, :]) 
        return out

def prepare_training_data(df, seq_length=5):
    """
    Converts a raw pandas DataFrame into PyTorch tensors for sequence modeling.
    Predicts time T+1 based on the sliding window sequence of T-seq_length to T.
    """
    # 1. Clean the data (Interpolate missing MongoDB sensor values)
    df = df.replace('NA', np.nan).apply(pd.to_numeric, errors='coerce')
    df = df.interpolate(method='linear').ffill().bfill()
    
    # Extract features: Temp, Pressure, Wind, Solar
    features = df[['temperature_c', 'pressure_hpa', 'wind_speed_ms', 'solar_irradiance_w_m2']].values
    
    # We want the AI to predict Wind and Solar yields
    targets = df[['wind_speed_ms', 'solar_irradiance_w_m2']].values
    
    X, Y = [], []
    # Create sliding windows of `seq_length` hours to predict the next hour
    for i in range(len(features) - seq_length):
        X.append(features[i : i + seq_length])
        Y.append(targets[i + seq_length])
        
    return torch.tensor(X, dtype=torch.float32), torch.tensor(Y, dtype=torch.float32)

def train_model(model, X_train, Y_train, epochs=150, lr=0.01):
    """
    Standard PyTorch training loop using Backpropagation.
    """
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    print(f"Training LSTM on {len(X_train)} samples for {epochs} epochs...")
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        
        # Forward pass
        outputs = model(X_train)
        loss = criterion(outputs, Y_train)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 25 == 0:
            print(f"Epoch [{epoch+1:3d}/{epochs}], Loss (MSE): {loss.item():.4f}")
            
    print("Training Complete!\n")

def export_to_onnx(model, model_path="polar_forecaster.onnx"):
    """
    Exports the trained PyTorch model to ONNX format for Edge deployment.
    """
    model.eval() 
    # Create a dummy input matching the shape of one sequence block
    dummy_input = torch.randn(1, 5, 4) 
    
    print(f"Exporting PyTorch model to {model_path} for Edge Deployment...")
    torch.onnx.export(model, dummy_input, model_path, export_params=True, opset_version=11,          
                      do_constant_folding=True, input_names=['input_sequence'],   
                      output_names=['predicted_weather'],
                      dynamic_axes={'input_sequence' : {0 : 'batch_size'}, 'predicted_weather' : {0 : 'batch_size'}})
    print("Export complete! The ONNX model is highly optimized and ready for inference.")

if __name__ == "__main__":
    print("--- AI Forecaster: End-to-End Training Pipeline ---")
    
    # 1. Fetch live ground-truth data from the cloud
    print("\n1. Fetching historical training data from MongoDB...")
    df = fetch_real_antaws_data(limit=100) # Fetch a larger chunk for better training
    
    if df is not None and not df.empty:
        # 2. Prepare the tensors
        print("\n2. Preparing sequential PyTorch tensors...")
        X, Y = prepare_training_data(df, seq_length=5)
        
        # 3. Initialize and Train the Model
        model = PolarMicrogridForecaster(input_size=4, hidden_size=64, num_layers=2, output_size=2)
        print("\n3. Starting Deep Learning Training Phase...")
        train_model(model, X, Y, epochs=150)
        
        # 4. Make a Live Prediction
        model.eval()
        # Take the most recent 5 hours of weather data to predict the absolute future
        recent_weather = X[-1].unsqueeze(0) # Add batch dimension
        actual_future = Y[-1]
        
        with torch.no_grad():
            prediction = model(recent_weather)
            
        print("--- Prediction Results ---")
        print("The AI looked at the last 5 hours of cloud data and predicted the next hour:")
        print(f"Real Future Weather -> Wind: {actual_future[0]:.1f} m/s | Solar: {actual_future[1]:.1f} W/m2")
        print(f"AI Predicted Future -> Wind: {prediction[0][0]:.1f} m/s | Solar: {prediction[0][1]:.1f} W/m2")
        
        # 5. Export for Edge
        print("\n4. Exporting to ONNX Edge Format...")
        export_to_onnx(model)
    else:
        print("Failed to fetch data for training.")
