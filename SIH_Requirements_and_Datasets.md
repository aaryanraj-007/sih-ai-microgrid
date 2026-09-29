# SIH 26051: Project Requirements & Datasets

This document outlines the software dependencies, deployment infrastructure, and the specific polar datasets required to train and deploy the AI Microgrid system.

---

## 1. Datasets & Ground Truth Data
To train the AI Forecaster (LSTM) and the Reinforcement Learning (PPO) agent, we rely on high-resolution historical telemetry specific to the polar/extreme regions:

1. **NCPOR Data Portal (Primary Source)**
   * **URL:** `data.ncpor.res.in`
   * **Usage:** Ground truth surface station meteorological observations from Maitri (Antarctica), Bharati (Antarctica), and Himadri (Arctic).
2. **AntAWS Dataset (Stored on MongoDB Cloud)**
   * **Source:** Earth System Science Data (ESSD).
   * **Usage:** Comprehensive compilation of observations from the Antarctic Automatic Weather Station network. We actively query this from our MongoDB Atlas Data Lake during simulation.
3. **PolarRES Dataset**
   * **Source:** ERA5-based regional climate model ensemble for the Antarctic.
   * **Usage:** High-resolution simulated data critical for training the AI to understand the transition between the 24-hour midnight sun (Polar Summer) and total darkness (Polar Night).

---

## 2. Software Packages & Dependencies
The architecture is split into a Python 3.11+ Backend and a React/Next.js Frontend.

### Artificial Intelligence & Machine Learning
* `torch` (PyTorch) - Building the LSTM network for weather/load forecasting (`ai_forecaster.py`).
* `onnx` & `onnxscript` - Exporting PyTorch models for lightweight Edge deployment.
* `gymnasium` & `stable-baselines3` - Implementing the Proximal Policy Optimization (PPO) load-balancing agent (`rl_agent.py`).

### IoT, Database & Backend Infrastructure
* `pymongo` & `dnspython` - Securely connecting to the MongoDB Cloud Data Lake to fetch real-world AntAWS data.
* `fastapi` & `uvicorn` - High-performance async REST API Gateway (`api_gateway.py`).
* `paho-mqtt` - Standard MQTT client for simulating Edge-to-SCADA telemetry.
* `sqlite3` - (Built-in) Time-series State Manager to persist live telemetry.

### Frontend Dashboard
* `next` (Next.js 14+) - The React framework powering the UI.
* `recharts` - High-performance SVG charting library for visualizing the AI predictions.
* `lucide-react` - Scalable iconography for the glassmorphic interface.

**Installation Commands:**
```bash
# Backend Dependencies
pip install pandas numpy torch onnx onnxscript gymnasium stable-baselines3 fastapi uvicorn paho-mqtt pymongo dnspython

# Frontend Dependencies (Run inside /dashboard)
npx create-next-app@latest
npm install recharts lucide-react
```

---

## 3. Hardware & Deployment Infrastructure Requirements

Because polar stations have limited internet access, the system is deployed using an **Edge-Native** approach.

### 1. Mainland (Supercomputers / Cloud)
* **Software:** MongoDB Atlas (Data Lake)
* **Role:** Stores the massive datasets. Used solely to train the deep learning models before deploying them to the edge via satellite link.

### 2. The Microgrid SCADA (On-Premise Server)
* **Software:** K3s (Lightweight Kubernetes), Next.js Dashboard.
* **Hardware:** Standard servers placed inside the thermally controlled research station.
* **Role:** Hosts the FastAPI gateway, local SQLite database, MQTT Broker, and the UI Command Center.

### 3. Local Microgrid Controllers (Edge Nodes)
* **Hardware:** Ruggedized Industrial PCs (IPCs).
* **Software:** **ONNX Runtime** (C++ or Rust).
* **Role:** Deployed directly at the wind turbines or battery banks. They run the highly compressed `.onnx` models locally to make microsecond hardware adjustments without pinging the central server.
* **Failsafe:** Hardcoded traditional PLCs sit directly behind these edge nodes to cut power/start diesel if the Edge PC crashes.
