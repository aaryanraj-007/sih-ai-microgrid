import sqlite3
import json
from datetime import datetime

class StateManager:
    """
    Handles the time-series SQLite database for the microgrid.
    Acts as the temporary storage mechanism for live system state.
    """
    def __init__(self, db_path="microgrid_state.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Creates the necessary tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for raw environmental telemetry from edge sensors
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS environment_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                temperature_c REAL,
                pressure_hpa REAL,
                wind_speed_ms REAL,
                solar_irradiance_w_m2 REAL
            )
        ''')
        
        # Table for the microgrid's internal state (Battery, Load, Generator)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                battery_temp_c REAL,
                dynamic_soc_pct REAL,
                actual_capacity_kwh REAL,
                station_load_kw REAL,
                diesel_generator_active BOOLEAN,
                load_shed_active BOOLEAN
            )
        ''')
        
        conn.commit()
        conn.close()

    def log_environment(self, temp_c, pressure, wind, solar):
        """Logs a new reading from the environmental sensors."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO environment_telemetry 
            (timestamp, temperature_c, pressure_hpa, wind_speed_ms, solar_irradiance_w_m2)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, temp_c, pressure, wind, solar))
        
        conn.commit()
        conn.close()

    def log_system_state(self, bat_temp, soc, cap, load, diesel_active, shed_active):
        """Logs the resulting state of the microgrid after BEMS/RL processing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO system_state 
            (timestamp, battery_temp_c, dynamic_soc_pct, actual_capacity_kwh, station_load_kw, diesel_generator_active, load_shed_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, bat_temp, soc, cap, load, diesel_active, shed_active))
        
        conn.commit()
        conn.close()

    def get_latest_state(self):
        """Retrieves the most recent system state and environmental reading."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get latest environment
        cursor.execute('SELECT * FROM environment_telemetry ORDER BY id DESC LIMIT 1')
        env_row = cursor.fetchone()
        
        # Get latest system state
        cursor.execute('SELECT * FROM system_state ORDER BY id DESC LIMIT 1')
        sys_row = cursor.fetchone()
        
        conn.close()
        
        return {
            "environment": env_row,
            "system": sys_row
        }

if __name__ == "__main__":
    print("--- Initializing State Manager (SQLite) ---")
    sm = StateManager()
    
    print("Logging dummy environmental data...")
    sm.log_environment(temp_c=-20.5, pressure=985.2, wind=15.4, solar=0.0)
    
    print("Logging dummy system state...")
    sm.log_system_state(bat_temp=-5.0, soc=85.5, cap=350.0, load=45.0, diesel_active=False, shed_active=False)
    
    print("\nRetrieving Latest State:")
    latest = sm.get_latest_state()
    print(json.dumps(latest, indent=2))
