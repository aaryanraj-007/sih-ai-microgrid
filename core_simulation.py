import math

class EnvironmentalModel:
    """
    Handles atmospheric and environmental calculations, specific to extreme polar conditions.
    """
    
    @staticmethod
    def calculate_air_density_direct(pressure_hpa: float, temp_c: float) -> float:
        """
        Direct Method: Calculates air density at sensor height using the Ideal Gas Law.
        Since polar air holds almost zero moisture, it's treated as a dry gas.
        
        Args:
            pressure_hpa: Absolute local barometric pressure in hPa (millibars).
            temp_c: Temperature in Celsius.
            
        Returns:
            Air density in kg/m^3
        """
        p_pa = pressure_hpa * 100 # Convert hPa to Pascals
        t_k = temp_c + 273.15 # Convert C to Kelvin
        r_specific = 287.058 # Specific gas constant for dry air (J/(kg*K))
        
        return p_pa / (r_specific * t_k)

    @staticmethod
    def calculate_air_density_barometric(pressure_sea_level_hpa: float, temp_ground_c: float, altitude_m: float) -> float:
        """
        Barometric Method: Corrects for altitude if sensors are at sea level.
        
        Args:
            pressure_sea_level_hpa: Sea-level pressure in hPa.
            temp_ground_c: Ground-level temperature in Celsius.
            altitude_m: Altitude of the turbine hub in meters.
            
        Returns:
            Air density in kg/m^3 at the specified altitude.
        """
        p0_pa = pressure_sea_level_hpa * 100
        t0_k = temp_ground_c + 273.15
        lapse_rate = 0.0065 # Standard temperature lapse rate (K/m)
        
        # Step A: Temp at altitude (T_h)
        t_h = t0_k - (lapse_rate * altitude_m)
        
        # Step B: Pressure at altitude (P_h)
        # using the exponent constant 5.255 derived from (g*M)/(R*L)
        exponent = 5.255
        p_h = p0_pa * math.pow((1 - (lapse_rate * altitude_m) / t0_k), exponent)
        
        # Step C: Final density
        r_specific = 287.058
        return p_h / (r_specific * t_h)


class WindTurbineModel:
    """
    Simulates the electrical power output of a wind turbine.
    """
    def __init__(self, swept_area_m2: float, power_coefficient: float = 0.4, 
                 electrical_efficiency: float = 0.9, cut_in_speed: float = 3.0, 
                 rated_speed: float = 12.0, cut_out_speed: float = 25.0, 
                 rated_capacity_kw: float = 100.0):
        self.A = swept_area_m2 # Swept Area (m^2)
        self.Cp = power_coefficient # Aerodynamic efficiency
        self.eta = electrical_efficiency # Electrical efficiency
        self.v_cut_in = cut_in_speed # m/s
        self.v_rated = rated_speed # m/s
        self.v_cut_out = cut_out_speed # m/s
        self.rated_capacity_kw = rated_capacity_kw

    def calculate_power_kw(self, wind_speed_m_s: float, air_density_kg_m3: float) -> float:
        """
        Calculates output power in kW given wind speed and air density.
        Applies the power curve constraints.
        """
        v = wind_speed_m_s
        
        if v < self.v_cut_in:
            # Wind too weak to overcome friction
            return 0.0
        elif v >= self.v_cut_out:
            # Turbine brakes to survive storm-force winds
            return 0.0
        elif v >= self.v_rated:
            # Power = Rated Capacity (pitching blades to spill excess wind)
            return self.rated_capacity_kw
        else:
            # V_cut-in <= V < V_rated: Follows the cubic equation
            # P_wind = 1/2 * rho * A * V^3 * Cp * eta (in Watts)
            power_watts = 0.5 * air_density_kg_m3 * self.A * math.pow(v, 3) * self.Cp * self.eta
            power_kw = power_watts / 1000.0
            
            # Ensure we don't accidentally exceed rated capacity before rated wind speed
            return min(power_kw, self.rated_capacity_kw)


class SolarPVModel:
    """
    Simulates the electrical power output of a Solar Photovoltaic array.
    Accounts for temperature coefficients which are highly relevant in polar regions.
    """
    def __init__(self, rated_capacity_kw: float, temp_coefficient: float = -0.0035):
        self.P_rated = rated_capacity_kw # Nameplate capacity under STC
        self.alpha = temp_coefficient # Rate at which efficiency drops per degree of heat
        self.G_ref = 1000.0 # Reference irradiance at STC (W/m^2)
        self.T_ref = 25.0 # Reference temperature at STC (C)
        
    def calculate_power_kw(self, irradiance_w_m2: float, temp_cell_c: float) -> float:
        """
        Calculates output power in kW given solar irradiance and actual physical cell temperature.
        """
        if irradiance_w_m2 <= 0:
            return 0.0
            
        g_ratio = irradiance_w_m2 / self.G_ref
        temp_diff = temp_cell_c - self.T_ref
        
        # P_solar = P_rated * (G/G_ref) * [1 + alpha * (T_cell - T_ref)]
        power_kw = self.P_rated * g_ratio * (1 + (self.alpha * temp_diff))
        
        # Prevent negative power in extreme anomalies
        return max(0.0, power_kw)


if __name__ == "__main__":
    print("--- Testing Polar Microgrid Physics Engine ---")
    
    # 1. Test Environmental Model (Air Density in Antarctica)
    # Average summer temp at Maitri Station is around -5C, pressure around 980 hPa
    temp_c = -10.0
    pressure_hpa = 980.0
    rho = EnvironmentalModel.calculate_air_density_direct(pressure_hpa, temp_c)
    print(f"\n[Environment] Temp: {temp_c}C, Pressure: {pressure_hpa} hPa -> Air Density: {rho:.3f} kg/m^3")
    
    # For comparison, standard sea level density at 15C is ~1.225 kg/m^3
    # The polar air is significantly denser!
    
    # 2. Test Wind Turbine Model
    # Example: 100kW turbine with 20m blade radius (A = pi * r^2 = ~1256 m^2)
    radius = 20.0
    swept_area = math.pi * (radius ** 2)
    wind_turbine = WindTurbineModel(swept_area_m2=swept_area, rated_capacity_kw=100.0)
    
    wind_speed = 8.0 # m/s
    wind_power = wind_turbine.calculate_power_kw(wind_speed, rho)
    print(f"[Wind Power] Speed: {wind_speed} m/s, Density: {rho:.3f} kg/m^3 -> Output: {wind_power:.2f} kW")
    
    # 3. Test Solar PV Model
    # Example: 50kW array
    solar_array = SolarPVModel(rated_capacity_kw=50.0, temp_coefficient=-0.0035)
    
    # Summer day in Antarctica: Irradiance ~800 W/m^2, Cell Temp ~ -5C
    irradiance = 800.0
    cell_temp = -5.0
    solar_power = solar_array.calculate_power_kw(irradiance, cell_temp)
    print(f"[Solar Power] Irradiance: {irradiance} W/m^2, Cell Temp: {cell_temp}C -> Output: {solar_power:.2f} kW")
    
    # Notice how the cold temperature boosts the solar efficiency!
    # Expected power at 800W/m2 without temp coefficient would be 50 * (800/1000) = 40kW.
    # With -5C (which is 30 degrees below the 25C reference), the output should increase by roughly 10.5%.
