import pandas as pd
import numpy as np
import math
from core_simulation import EnvironmentalModel, WindTurbineModel, SolarPVModel
from bems_logic import PolarBatteryBank, MicrogridBEMS
from fetch_cloud_data import fetch_real_antaws_data

def generate_ncpor_mock_data(season='summer'):
    """
    Generates a mock 24-hour dataset representing typical data 
    from NCPOR's Maitri Station in Antarctica.
    """
    hours = np.arange(24)
    df = pd.DataFrame({'Hour': hours})
    
    # Station Load (kW) - fairly constant, slight peak during waking hours
    df['Station_Load_kW'] = 50 + np.sin((hours - 6) * np.pi / 12) * 10
    
    # Pressure (hPa) - ~980hPa at Maitri
    df['Pressure_hPa'] = 980.0 + np.random.normal(0, 2, 24)
    
    if season == 'summer':
        # Summer (e.g., December) at Maitri
        # 24 hours of daylight, relatively "warm" (-5C to 2C)
        df['Temperature_C'] = -3 + np.sin((hours - 12) * np.pi / 12) * 5
        df['Wind_Speed_ms'] = 8 + np.sin(hours * np.pi / 6) * 4 # Breezy to windy
        # Midnight sun means irradiance never hits 0, peaks at midday
        df['Solar_Irradiance_W_m2'] = 400 + np.sin((hours - 6) * np.pi / 12) * 400
    else:
        # Winter (e.g., July) at Maitri
        # Polar night (0 irradiance), brutal cold (-30C to -15C)
        df['Temperature_C'] = -20 + np.sin((hours - 12) * np.pi / 12) * 8
        df['Wind_Speed_ms'] = 15 + np.random.normal(0, 3, 24) # Heavy winds/blizzards
        df['Solar_Irradiance_W_m2'] = 0.0 # Total darkness
        
    return df

def run_simulation(df):
    # Initialize physics models
    turbine = WindTurbineModel(swept_area_m2=1256.0, rated_capacity_kw=100.0) # 100kW Turbine
    solar_array = SolarPVModel(rated_capacity_kw=50.0) # 50kW Array
    
    # Initialize BEMS with a frozen battery
    initial_temp = df.iloc[0]['Temperature_C']
    battery = PolarBatteryBank(nominal_capacity_kwh=500.0, initial_soc=1.0, initial_temp_c=initial_temp)
    bems = MicrogridBEMS(battery)
    
    results = []
    
    for idx, row in df.iterrows():
        # 1. Environment Physics (Air density dynamically changing)
        rho = EnvironmentalModel.calculate_air_density_direct(row['Pressure_hPa'], row['Temperature_C'])
        
        # 2. Generation Physics
        wind_gen = turbine.calculate_power_kw(row['Wind_Speed_ms'], rho)
        solar_gen = solar_array.calculate_power_kw(row['Solar_Irradiance_W_m2'], row['Temperature_C'])
        total_gen = wind_gen + solar_gen
        
        # 3. Look-ahead logic (simple: just peek at next hour's generated total if available)
        lookahead = 0.0
        if idx < len(df) - 1:
            next_row = df.iloc[idx + 1]
            n_rho = EnvironmentalModel.calculate_air_density_direct(next_row['Pressure_hPa'], next_row['Temperature_C'])
            lookahead = turbine.calculate_power_kw(next_row['Wind_Speed_ms'], n_rho) + \
                        solar_array.calculate_power_kw(next_row['Solar_Irradiance_W_m2'], next_row['Temperature_C'])

        # 4. Execute BEMS Decision Matrix
        state = bems.step(p_gen_kw=total_gen, p_load_kw=row['Station_Load_kW'], look_ahead_gen_kw=lookahead)
        
        results.append({
            'Hr': row['Hour'],
            'Gen_kW': total_gen,
            'Load_kW': row['Station_Load_kW'],
            'Temp_C': state['battery_temp'],
            'SOC_%': state['dynamic_soc'] * 100,
            'Cap_kWh': state['actual_capacity']
        })
        
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False, float_format="%.1f"))
    print(f"\n>> Simulation Complete <<")
    print(f"Diesel Consumed: {bems.total_diesel_used_kwh:.1f} kWh")
    print(f"Load Shed (Blackout): {bems.total_load_shed_kwh:.1f} kWh")

if __name__ == "__main__":
    print("\n=======================================================")
    print("SIMULATING CLOUD DATA: LIVE MONGODB INTEGRATION (AntAWS)")
    print("=======================================================")
    real_df = fetch_real_antaws_data()
    
    if real_df is not None:
        # 1. Clean the real dataset (IoT sensors often drop data, creating 'NA' strings)
        real_df = real_df.replace('NA', np.nan)
        # Convert all to numeric so we can interpolate safely
        real_df = real_df.apply(pd.to_numeric, errors='coerce')
        # Interpolate missing values (draw a straight line between the known data points)
        real_df = real_df.interpolate(method='linear').ffill().bfill()
        
        # 2. Map columns to match what our strict physics engine expects
        real_df = real_df.rename(columns={
            'temperature_c': 'Temperature_C',
            'pressure_hpa': 'Pressure_hPa',
            'wind_speed_ms': 'Wind_Speed_ms',
            'solar_irradiance_w_m2': 'Solar_Irradiance_W_m2'
        })
        
        # 3. Add required simulation columns (Time and Human Station Load)
        real_df['Hour'] = np.arange(len(real_df))
        real_df['Station_Load_kW'] = 50 + np.sin((real_df['Hour'] - 6) * np.pi / 12) * 10
        
        # 4. Run the full BEMS Simulation!
        run_simulation(real_df)
    else:
        print("Failed to fetch cloud data. Falling back to mock data...")
