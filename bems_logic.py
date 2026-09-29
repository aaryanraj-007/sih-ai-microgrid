import math

class PolarBatteryBank:
    """ Models a battery bank operating in extreme sub-zero conditions. """
    def __init__(self, nominal_capacity_kwh: float, initial_soc: float = 1.0, 
                 initial_temp_c: float = -10.0):
        self.nominal_capacity_kwh = nominal_capacity_kwh
        self.temp_c = initial_temp_c
        # Polar specific constraints
        self.t_ref = 25.0 # C
        self.k_degradation = 0.015 # Approximated capacity loss coefficient per degree below T_ref
        self.safe_charge_temp_c = 0.0 # Cannot charge if below freezing (prevents lithium plating)
        self.min_soc_limit = 0.20 # Maximum Depth of Discharge (DOD) leaves 20% floor
        
        # Heating characteristics
        self.heating_efficiency = 0.90
        # Assume it takes roughly 2kWh of energy to raise the physical battery mass by 1C
        self.energy_to_heat_1_degree_kwh = 2.0 

        # Initialize energy based on ACTUAL cold capacity, not nominal
        actual_cap = self.get_actual_capacity()
        self.current_energy_kwh = actual_cap * initial_soc

    def get_actual_capacity(self) -> float:
        """ Calculates temperature-derated capacity: C_actual(t) = C_nominal * e^(k * (T_bat - T_ref)) """
        if self.temp_c >= self.t_ref:
            return self.nominal_capacity_kwh
        
        # Exponential decay representing capacity loss in extreme cold
        capacity = self.nominal_capacity_kwh * math.exp(self.k_degradation * (self.temp_c - self.t_ref))
        return capacity

    def get_dynamic_soc(self) -> float:
        """ Calculates SOC based on the shrunken actual capacity, not nameplate. """
        actual_cap = self.get_actual_capacity()
        if actual_cap <= 0:
            return 0.0
        return self.current_energy_kwh / actual_cap

    def heat_battery(self, applied_energy_kwh: float):
        """ Converts applied electrical energy into temperature rise. """
        effective_energy = applied_energy_kwh * self.heating_efficiency
        temp_rise = effective_energy / self.energy_to_heat_1_degree_kwh
        self.temp_c += temp_rise

    def charge(self, available_energy_kwh: float) -> float:
        """ Attempts to charge the battery. Returns unused/curtailed energy. """
        if self.temp_c < self.safe_charge_temp_c:
            return available_energy_kwh # Cannot charge safely, return all energy as unused
            
        actual_cap = self.get_actual_capacity()
        space_available = actual_cap - self.current_energy_kwh
        
        if space_available <= 0:
            return available_energy_kwh # Battery is completely full
            
        if available_energy_kwh <= space_available:
            self.current_energy_kwh += available_energy_kwh
            return 0.0
        else:
            self.current_energy_kwh = actual_cap
            return available_energy_kwh - space_available

    def discharge(self, requested_energy_kwh: float) -> float:
        """ Attempts to discharge. Returns the amount of energy ACTUALLY provided. """
        actual_cap = self.get_actual_capacity()
        min_safe_energy = actual_cap * self.min_soc_limit
        
        available_to_discharge = self.current_energy_kwh - min_safe_energy
        
        if available_to_discharge <= 0:
            return 0.0 # Battery is depleted relative to its cold capacity limits
            
        if requested_energy_kwh <= available_to_discharge:
            self.current_energy_kwh -= requested_energy_kwh
            return requested_energy_kwh
        else:
            self.current_energy_kwh -= available_to_discharge
            return available_to_discharge


class MicrogridBEMS:
    """ The Battery Energy Management System controller. """
    def __init__(self, battery_bank: PolarBatteryBank):
        self.battery = battery_bank
        self.total_diesel_used_kwh = 0.0
        self.total_load_shed_kwh = 0.0

    def step(self, p_gen_kw: float, p_load_kw: float, look_ahead_gen_kw: float = 0.0) -> dict:
        """ Executes the decision logic for a 1-hour time step. """
        
        # 1. Predictive Pre-heating Logic
        # If battery is frozen, and we expect a massive generation surplus in the next hour,
        # we pre-heat the battery NOW using a small amount of currently stored energy.
        if self.battery.temp_c < self.battery.safe_charge_temp_c and look_ahead_gen_kw > (p_load_kw * 1.5):
            pre_heat_energy = 5.0 # Expend 5kWh to warm up the battery mass
            provided = self.battery.discharge(pre_heat_energy)
            if provided > 0:
                self.battery.heat_battery(provided)

        if p_gen_kw > p_load_kw:
            # Scenario A: Energy Surplus
            surplus = p_gen_kw - p_load_kw
            
            if self.battery.temp_c < self.battery.safe_charge_temp_c:
                # Route surplus to heaters instead of charging terminals
                self.battery.heat_battery(surplus)
            else:
                # Safe to charge
                unused = self.battery.charge(surplus)
                # Unused energy would theoretically be curtailed/dumped here
                    
        else:
            # Scenario B: Energy Deficit
            deficit = p_load_kw - p_gen_kw
            provided_by_battery = self.battery.discharge(deficit)
            unmet_load = deficit - provided_by_battery
            
            if unmet_load > 0:
                # Attempt to shed non-critical loads (assume 20% of total load is non-critical)
                max_sheddable = p_load_kw * 0.20
                actually_shed = min(unmet_load, max_sheddable)
                self.total_load_shed_kwh += actually_shed
                unmet_load -= actually_shed
                
                # If critical load is still unmet, trigger the Diesel Generator
                if unmet_load > 0:
                    self.total_diesel_used_kwh += unmet_load

        return {
            'actual_capacity': self.battery.get_actual_capacity(),
            'dynamic_soc': self.battery.get_dynamic_soc(),
            'battery_temp': self.battery.temp_c
        }

if __name__ == "__main__":
    print("--- Testing Polar BEMS Simulation (6 Hour Window) ---")
    
    # 500 kWh Nameplate battery. 
    # Starts at 100% nominal charge, but frozen solid at -15C.
    battery = PolarBatteryBank(nominal_capacity_kwh=500.0, initial_soc=1.0, initial_temp_c=-15.0)
    bems = MicrogridBEMS(battery)
    
    print(f"Initial Nameplate Capacity: {battery.nominal_capacity_kwh} kWh")
    print(f"Initial Actual Capacity at {battery.temp_c}C: {battery.get_actual_capacity():.1f} kWh (Severely degraded!)\n")
    
    # Mock data: [Load_kW, Solar_Gen_kW]
    # 06:00 and 07:00 are dark and cold. At 08:00, the sun hits the panels hard.
    hourly_profile = [
        (50, 0),   # 06:00
        (50, 0),   # 07:00 -> Predictive pre-heat triggers here!
        (50, 150), # 08:00 -> 100kW surplus. Used to violently heat battery because it's still < 0C.
        (50, 250), # 09:00 -> Battery should cross 0C and start absorbing the massive charge.
        (50, 250), # 10:00 -> Battery happily charging.
        (50, 200), # 11:00
    ]
    
    for i, (load, gen) in enumerate(hourly_profile):
        hour = i + 6
        # Simple look-ahead to the next hour's expected generation
        lookahead_gen = hourly_profile[i+1][1] if i+1 < len(hourly_profile) else 0.0
        
        state = bems.step(p_gen_kw=gen, p_load_kw=load, look_ahead_gen_kw=lookahead_gen)
        
        print(f"[{hour:02d}:00] Gen: {gen:3d}kW | Load: {load}kW | Bat Temp: {state['battery_temp']:>5.1f}C | SOC: {state['dynamic_soc']*100:>5.1f}% | Actual Cap: {state['actual_capacity']:>5.1f}kWh")
        
    print(f"\nTotal Diesel Used: {bems.total_diesel_used_kwh:.1f} kWh")
    print(f"Total Load Shed: {bems.total_load_shed_kwh:.1f} kWh")
