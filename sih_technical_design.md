# System Architecture & Technical Design
**Smart India Hackathon (SIH 26051 / 26061)**
**Project:** Predictive, AI-Driven Hierarchical Microgrid for Polar Extreme Environments
**Target Deployments:** Maitri & Bharati Stations (Antarctica), Himadri Station (Arctic), Ladakh (High Altitude)

---

## 1. Executive Summary
Standard programmable logic controllers (PLCs) in isolated polar microgrids operate on **reactive** logic—responding to voltage drops only after they happen, heavily relying on polluting diesel generators. 

This solution replaces static PLCs with an **AI-Driven Hierarchical Microgrid**. By utilizing deep learning for weather/load forecasting and edge-deployed Reinforcement Learning for dynamic load balancing, the system shifts energy management from reactive to **predictive**. It calculates real-time extreme-weather physics (dense polar air, severe battery capacity degradation in sub-zero temperatures) to optimize renewable efficiency and preemptively manage storage thermal states.

---

## 2. Hierarchical Edge-Native Deployment Architecture
Because polar stations face severe internet disruptions and life-critical environmental threats, the system relies on an **Offline-First, Edge-Native Architecture**.

```mermaid
graph TD
    subgraph "Mainland (India Supercomputers)"
        Cloud[MongoDB Data Lake / AI Training]
        Data[NCPOR / AntAWS Historical Data]
        Data --> Cloud
        Cloud -.->|ONNX Model Weights (Low Bandwidth Sat-Link)| Central
    end

    subgraph "Polar Research Station (On-Premise)"
        Central[Central Brain - React Dashboard & FastAPI]
        
        Central <-->|MQTT Telemetry| Edge1
        Central <-->|MQTT Telemetry| Edge2
        Central <-->|MQTT Telemetry| Edge3
        
        subgraph "Local Edge Nodes (Ruggedized IPCs)"
            Edge1[Edge Node 1: Wind Arrays]
            Edge2[Edge Node 2: Solar PV]
            Edge3[Edge Node 3: Battery Bank & Diesel]
        end
        
        Edge3 -.->|Hardware Failsafe| PLC[Hardcoded PLCs]
    end
```

---

## 3. The 11-Pillar Software Stack (Full-Stack IoT)
The architecture is split into 11 distinct modules simulating a true production environment, spanning from the Cloud Data Lake to the Edge Microcontrollers.

### Pillar 1: Mainland Cloud Data Lake (`fetch_cloud_data.py`)
Securely connects to a MongoDB Atlas cluster to ingest and clean raw AntAWS weather telemetry, acting as the ground-truth provider for the AI pipeline.

### Pillar 2: The Physics Engine (`core_simulation.py`)
Calculates dynamic air density using the Ideal Gas Law to prove that extreme cold boosts wind turbine kinetic yield. It also calculates Solar PV temperature coefficients.

### Pillar 3: Battery Intelligence (`bems_logic.py`)
Tracks dynamic, temperature-derated State of Charge (SOC). If the battery is freezing, it shrinks the usable capacity algorithmically. 

### Pillar 4: AI Forecasting Layer (`ai_forecaster.py`)
A PyTorch Long Short-Term Memory (LSTM) network that trains on the MongoDB cloud data to predict future solar and wind yields. It exports to an **ONNX** file for low-power edge execution.

### Pillar 5: The Central Brain / RL Agent (`rl_agent.py`)
A Deep Reinforcement Learning model (Proximal Policy Optimization via Stable Baselines3) that makes millisecond decisions to shed non-essential loads to prevent catastrophic battery death.

### Pillar 6: IoT Telemetry Simulator (`telemetry_broker.py`)
Utilizes `paho-mqtt` to simulate edge sensors publishing raw data over the local LAN, mimicking real-world hardware communication.

### Pillar 7: State Management (`state_manager.py`)
A time-series **SQLite** database that prevents in-memory data loss. It stores the live telemetry stream and system state for the AI to query.

### Pillar 8: API Gateway (`api_gateway.py`)
A highly performant **FastAPI** server that exposes the SQLite database to the frontend dashboard.

### Pillar 9: The Data Pipeline (`simulate_dataset.py`)
A Pandas-driven pipeline that feeds the cloud data through the physics engine and RL agent to simulate continuous 24-hour operation.

### Pillar 10: The PLC Failsafe (`failsafe_fallback.py`)
A background daemon that monitors the database. If the AI containers crash (Watchdog Timeout) or if the SOC drops below 20%, it issues a hard-start to the Diesel generator to protect human life.

### Pillar 11: Edge Command Dashboard (`/dashboard`)
A **Next.js React Frontend** featuring a premium glassmorphic UI. It visualizes the live AI forecasting matrix via `recharts` and tracks real-time BEMS telemetry.

---

## 4. Mathematical Core

### Wind Generation (Air Density Correction)
$$ \rho = \frac{P_h}{287.058 \cdot T_h} $$
$$ P_{wind} = \frac{1}{2} \cdot \rho \cdot A \cdot V^3 \cdot C_p \cdot \eta $$

### Solar PV Generation (Temperature Coefficient)
$$ P_{solar} = P_{rated} \cdot \left(\frac{G}{G_{ref}}\right) \cdot [1 + \alpha \cdot (T_{cell} - T_{ref})] $$

### Battery Derating Constraint
$$ C_{actual}(t) = C_{nominal} \cdot e^{k \cdot (T_{bat}(t) - T_{ref})} $$

---

## 5. Simulation Scenarios & Explainable AI (XAI) Logic

To prove the superiority of the RL Agent over traditional PLCs, the architecture is stress-tested against four domain-specific polar catastrophes. The UI implements an **Explainable AI (XAI)** layer to translate the deep learning policy into human-readable actions for the evaluators.

### 5.1 Legacy vs. AI Thresholds
*   **Legacy Rule-Based:** Hardcoded to turn on the diesel generator *only* when Battery State of Charge (SOC) drops to an absolute critical limit of **20%**. It fails to anticipate incoming weather.
*   **PPO AI Mode:** Anticipates weather via the LSTM forecast. If a storm is approaching, the AI will pre-ramp the diesel generator if the SOC is **< 40%**, preserving the battery's discharge efficiency and preventing a catastrophic drop to 0%.

### 5.2 Katabatic Storm Surge
*   **Trigger:** Wind speeds rapidly spike to **35+ m/s**.
*   **Physical Constraint:** Wind turbines automatically engage physical brakes to prevent structural destruction, dropping generation to **0.0 kW**.
*   **AI Action:** The RL Agent instantly routes 100% of the station load to the BESS. If the BESS SOC is <40%, it immediately ramps the diesel generator to cover the deficit.

### 5.3 Deep Polar Night
*   **Trigger:** The transition into the Antarctic winter, resulting in 14 days of complete darkness.
*   **Physical Constraint:** Solar Irradiance drops to **0.0 W/m²**.
*   **AI Action:** The AI engages strict battery cycle management. It prioritizes wind generation exclusively and severely limits non-essential load spikes to stretch battery autonomy to its absolute theoretical limit.

### 5.4 Critical BESS Heating Failure
*   **Trigger:** The battery core temperature drops below safe operating limits (e.g., -10.4°C).
*   **Physical Constraint:** Lithium-ion capacities plummet when frozen, risking irreversible cell damage.
*   **AI Action:** The AI instantly executes **Load Shedding**. It cuts power to non-critical zones (e.g., Science Lab 2, Entertainment) to purposefully redirect **12 kW** of power straight into the emergency thermal resistive heaters built into the battery cells.

### 5.5 PLC Hardware Failsafe (AI Crash)
*   **Trigger:** The Edge PC running the AI models freezes or crashes (Watchdog Timeout).
*   **Physical Constraint:** No software instructions are being sent to the microgrid.
*   **Action:** Demonstrates Pillar 10. The hardcoded PLC bypasses the Edge PC entirely, drops the load from the battery, and **hard-starts the diesel generator** to ensure the scientists do not freeze.
