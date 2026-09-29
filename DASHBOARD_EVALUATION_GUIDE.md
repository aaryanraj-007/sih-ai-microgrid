# 🧊 Microgrid Edge Command: Evaluator's Dashboard Guide

This guide is designed for hackathon judges, evaluators, and team members to understand exactly how to read the Next.js Command Dashboard and what the various symbols and panels represent during a live pitch.

---

## 1. The Global Header
*   **📍 Location Badge:** Shows *Station: Zhongshan AWS (Telemetry Proxy for Bharati Station)*. This sets our narrative context—proving we are using highly accurate coastal Antarctic data from a neighboring international station to protect India's Bharati Station.
*   **🟢 EDGE AIR-GAPPED Badge:** The green pulsing badge indicates that the dashboard and the AI model are running entirely on the local Edge PC. It proves the system does not require an active satellite internet connection to make life-saving decisions.

## 2. Telemetry Panel (AntAWS Data)
*   **Wind Speed (m/s):** The raw kinetic input. If this spikes above 30 m/s, it turns red, indicating dangerous conditions.
*   **Solar Irradiance (W/m²):** The sun's energy hitting the solar panels. 
    *   *Note:* If this drops to 0, a yellow `Polar Night` badge appears, showing the system recognizes prolonged darkness.
*   **Air Density (ρ):** Antarctic air is extremely cold and dense (around 1.42 kg/m³ compared to 1.22 kg/m³ at room temperature). Dense air produces significantly more wind power. The physics engine tracks this to optimize predictions.

## 3. Live Power Flow (Single-Line Diagram)
This is the visual topology of the microgrid.
*   **The Nodes (Icons):**
    *   🌬️ **Wind Array:** Blue indicates it is actively generating power.
    *   🛢️ **Diesel Genset:** Red indicates the diesel generator is burning fuel (polluting). The goal is to keep this at 0 kW.
    *   🔋 **BESS Storage:** Orange indicates the Battery Energy Storage System.
    *   ⚡ **Base Load:** The total power requirement of the science station.
*   **The Arrows (Dynamic Power Flow):**
    *   Green arrows moving *right* indicate power flowing from generators to the station.
    *   If the battery is **Discharging**, the arrow points right (supplying the station).
    *   If the battery is **Charging**, the arrow reverses direction (pointing left) and turns orange, absorbing excess wind or diesel power.

## 4. Deep RL Agent & Explainable AI (XAI)
This panel proves that an Artificial Intelligence is actively flying the ship.
*   **Current Action Badge:** Shows what the AI is prioritizing right now (e.g., *Monitoring*, *Load Shedding*, *Pre-Ramping Diesel*).
*   **Explainable AI (XAI) Rationale:** This blue box is critical for judges. Deep Learning is often a "black box," but this text explicitly explains *why* the AI made a decision (e.g., *Why did it turn on the diesel before the battery died? Because it saw a storm coming in the forecast.*)

## 5. Interactive Simulation Controls (The Pitch Tool)
During the presentation, click these buttons to instantly stress-test the AI in front of the judges:
*   **Toggle Switch (PPO AI vs. Legacy):** Switch to Legacy mode to show how a "dumb" thermostat waits for the battery to die before turning on the diesel. Switch to AI mode to show predictive intelligence.
*   **Katabatic Storm (35 m/s Auto-Brake):** Simulates an extreme weather event. The turbines lock up for safety (0 kW). Watch the AI instantly reroute battery and diesel power.
*   **Deep Polar Night:** Kills the sun for 14 days. Watch the AI switch to strict cycle management.
*   **Critical BESS Heating Failure:** Freezing batteries lose capacity. Watch the AI instantly execute "Load Shedding" (cutting power to non-essential science labs) to heat the battery core.
*   **Simulate AI Crash (PLC Failsafe):** Proves Pillar 10 of your architecture. It simulates a Watchdog Timeout where the AI dies. The UI turns red, the Edge badge says `PLC OVERRIDE`, and the hardcoded PLC instantly fires the diesel generator to protect human life.

## 6. Microgrid Impact & Economics KPIs
*   **Diesel Conserved (L/day):** Ticks up live as long as the AI is keeping the diesel generator turned off.
*   **Carbon Offset (kg):** The environmental impact of keeping the station green.
*   **Renewable Fraction:** The percentage of the station powered purely by wind/solar. The goal is to keep this near 100%.

---
**💡 Pitch Strategy:** Start the demo in "Normal Operations" with the AI enabled. Let the judges see the green arrows. Then, hit the "Katabatic Storm" button and narrate how the XAI box updates and the power flows safely reroute to protect the station!
