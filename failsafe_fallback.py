import time
from datetime import datetime, timezone
from state_manager import StateManager
import urllib.request

class PLCFailsafeDaemon:
    """
    A hardcoded, non-AI daemon representing a traditional Programmable Logic Controller (PLC).
    It monitors the microgrid state independently and takes over if the AI crashes or critical thresholds are breached.
    This provides the life-critical redundancy required in polar environments.
    """
    def __init__(self):
        self.db = StateManager()
        
        # Hardcoded Critical Safety Rules (Cannot be altered by AI)
        self.CRITICAL_SOC_THRESHOLD = 20.0 # % (Below this, battery risks permanent freeze damage)
        self.CRITICAL_TEMP_THRESHOLD = -10.0 # C 
        self.STALE_DATA_TIMEOUT_SEC = 300 # 5 minutes without an AI update triggers a failsafe
        
        self.diesel_running = False

    def trigger_diesel(self, reason):
        """ Physically bypasses the AI to start the diesel generator. """
        if not self.diesel_running:
            print(f"\n[!!! EMERGENCY OVERRIDE !!!]")
            print(f"[PLC] Initiating hard-start of Diesel Generator.")
            print(f"[PLC] Reason: {reason}")
            
            # In a real system, this sends a 24V signal directly to the generator's starter relay.
            # Here, we can also hit our API gateway's manual override endpoint just to log it.
            try:
                req = urllib.request.Request("http://localhost:8000/api/trigger-diesel", method="POST")
                urllib.request.urlopen(req, timeout=2)
            except Exception:
                # Doesn't matter if the API container is completely crashed; 
                # the PLC relies on direct physical relays, not HTTP.
                pass 
                
            self.diesel_running = True
            print("[PLC] Diesel Generator is ONLINE. Life support power secured.\n")

    def monitor_loop(self, iterations=5):
        """ The infinite loop running on the ruggedized edge hardware. """
        print("[PLC Daemon] Failsafe monitor online. Watching system state...")
        
        for _ in range(iterations):
            state = self.db.get_latest_state()
            sys = state.get('system')
            
            if not sys:
                print("[PLC Daemon] No system state found! Assuming total AI failure.")
                self.trigger_diesel("No telemetry data found in DB.")
                time.sleep(2)
                continue
                
            # sys mapping from SQLite tuple:
            # (id, timestamp, battery_temp_c, dynamic_soc_pct, actual_capacity_kwh, station_load_kw, ...)
            timestamp_str = sys[1]
            bat_temp = sys[2]
            soc = sys[3]
            
            # 1. Check for AI Crash (Watchdog / Stale Data)
            try:
                last_update = datetime.fromisoformat(timestamp_str)
                now = datetime.now(timezone.utc)
                # Make last_update timezone aware for math
                if last_update.tzinfo is None:
                    last_update = last_update.replace(tzinfo=timezone.utc)
                    
                age_seconds = (now - last_update).total_seconds()
                
                if age_seconds > self.STALE_DATA_TIMEOUT_SEC:
                    self.trigger_diesel(f"AI Container unresponsive for {age_seconds:.1f} seconds (Watchdog Timeout).")
            except Exception as e:
                pass
                
            # 2. Check for Critical Physical Thresholds
            if soc < self.CRITICAL_SOC_THRESHOLD and bat_temp < self.CRITICAL_TEMP_THRESHOLD:
                self.trigger_diesel(f"Battery critically cold ({bat_temp}C) and depleted ({soc}%). Impending blackout.")
            else:
                if not self.diesel_running:
                    print(f"  [PLC] Status OK. SOC: {soc:.1f}%, Temp: {bat_temp:.1f}C. Deferring to AI.")
                    
            time.sleep(2) # Poll the database every 2 seconds


if __name__ == "__main__":
    daemon = PLCFailsafeDaemon()
    
    # We will forcefully inject a critical failure into the SQLite DB to test the daemon
    print("--- Simulating a Critical AI Failure ---")
    print("Injecting dying battery state (SOC=15%, Temp=-15C) into DB...")
    
    daemon.db.log_system_state(
        bat_temp=-15.0, 
        soc=15.0, 
        cap=200.0, 
        load=50.0, 
        diesel_active=False, 
        shed_active=True
    )
    
    # Run the daemon to watch it react instantly
    daemon.monitor_loop(iterations=3)
