import paho.mqtt.client as mqtt
import json
import time
from state_manager import StateManager

# We use a public sandbox MQTT broker to simulate the remote satellite/LAN connection
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
# Unique topic to prevent crossover with other public users
TELEMETRY_TOPIC = "sih26051/drdo/polar/telemetry"

class SCADASubscriber:
    """
    Simulates the Central Brain (On-Premise Server) listening to the Edge Nodes.
    """
    def __init__(self):
        self.db = StateManager()
        
        # Initialize MQTT client (Paho v2 spec)
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Polar_Central_SCADA")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"[SCADA] Connected to MQTT Broker. Status: {reason_code}")
        self.client.subscribe(TELEMETRY_TOPIC)
        print(f"[SCADA] Subscribed to edge topic: {TELEMETRY_TOPIC}")

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode('utf-8')
        try:
            data = json.loads(payload)
            print(f"  --> [SCADA] Intercepted telemetry from Edge: {data}")
            
            # Save the incoming edge data into the time-series SQLite database
            self.db.log_environment(
                temp_c=data.get('temperature_c', 0.0),
                pressure=data.get('pressure_hpa', 980.0),
                wind=data.get('wind_speed_ms', 0.0),
                solar=data.get('solar_irradiance_w_m2', 0.0)
            )
        except Exception as e:
            print(f"[SCADA] Error parsing message: {e}")

    def start(self):
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        # Run network loop in a background thread so it doesn't block
        self.client.loop_start()


class EdgeSensorNode:
    """
    Simulates the ruggedized Edge Node publishing sensor data over IoT protocols.
    """
    def __init__(self, node_id="Polar_Edge_01"):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, node_id)
        
    def connect(self):
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.client.loop_start()
        print(f"[Edge Node] Connected to MQTT Broker. Ready to broadcast.")

    def publish_reading(self, reading_dict):
        payload = json.dumps(reading_dict)
        self.client.publish(TELEMETRY_TOPIC, payload)
        print(f"[Edge Node] Published: {payload}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()


if __name__ == "__main__":
    print("--- Starting Polar IoT Telemetry Simulation ---")
    
    # 1. Start the SCADA Subscriber (Central Brain)
    scada = SCADASubscriber()
    scada.start()
    
    # Wait a moment for the subscriber to fully connect to the public broker
    time.sleep(2)
    
    # 2. Start the Edge Node (Sensors)
    edge_node = EdgeSensorNode()
    edge_node.connect()
    
    # 3. Simulate a sudden blizzard hitting the station in real-time
    mock_stream = [
        {"temperature_c": -12.5, "pressure_hpa": 980.1, "wind_speed_ms": 12.0, "solar_irradiance_w_m2": 0.0},
        {"temperature_c": -13.0, "pressure_hpa": 978.5, "wind_speed_ms": 14.5, "solar_irradiance_w_m2": 0.0},
        {"temperature_c": -15.5, "pressure_hpa": 975.0, "wind_speed_ms": 18.2, "solar_irradiance_w_m2": 0.0}
    ]
    
    print("\n--- Edge Node encountering a blizzard. Streaming data... ---")
    for reading in mock_stream:
        edge_node.publish_reading(reading)
        time.sleep(1.5) # Wait between readings to simulate real-time streaming
        
    # Clean up and disconnect
    time.sleep(1)
    edge_node.stop()
    scada.client.loop_stop()
    scada.client.disconnect()
    
    print("\nSimulation complete. SCADA intercepted the MQTT payloads and saved them to SQLite (state_manager.py)!")
