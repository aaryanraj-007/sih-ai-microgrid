import pymongo
import pandas as pd

def fetch_real_antaws_data(limit=24):
    """
    Connects to the cloud MongoDB Atlas cluster (Mainland Data Lake) 
    and fetches real AntAWS telemetry for the RL agent and simulation.
    """
    uri = "mongodb+srv://aaryanrajschooling_db_user:FkbeB8WC3ggGDs87@cluster0.kgcufqo.mongodb.net/"
    
    print("Connecting to MongoDB Atlas Cluster...")
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client["sih_microgrid_db"]
    weather_col = db["antaws_weather"]
    
    # We fetch a 24-hour block of data to feed the daily simulation
    cursor = weather_col.find().limit(limit)
    
    df = pd.DataFrame(list(cursor))
    
    if df.empty:
        print("[Error] No data found in the collection.")
        return None
        
    # Standardize the messy MongoDB column names by finding substrings
    # (This prevents encoding crashes from the degree symbol)
    temp_col = [c for c in df.columns if "Temperature" in c][0]
    press_col = [c for c in df.columns if "Pressure" in c][0]
    wind_col = [c for c in df.columns if "Wind Speed" in c][0]
    
    df = df.rename(columns={
        temp_col: "temperature_c",
        press_col: "pressure_hpa",
        wind_col: "wind_speed_ms"
    })
    
    # The AntAWS dataset often omits solar irradiance, so we add a placeholder 
    # (In reality, you'd calculate this based on the 'Month' and latitude for polar day/night)
    df['solar_irradiance_w_m2'] = 0.0
    
    return df

if __name__ == "__main__":
    print("--- Fetching Real AntAWS Weather Data from Cloud Data Lake ---")
    df = fetch_real_antaws_data()
    
    if df is not None:
        print(f"\nSuccessfully downloaded {len(df)} records! Here is a sample:")
        # Displaying the cleaned data
        print(df[['Year', 'Month', 'Day', 'temperature_c', 'wind_speed_ms', 'pressure_hpa']].head(5))
        
        print("\n[Integration Ready]: This DataFrame can now be directly injected into `simulate_dataset.py`!")
