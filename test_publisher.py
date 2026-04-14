import paho.mqtt.client as mqtt
import time
import random
import json
from datetime import datetime
from config import BROKER, PORT, TOPIC

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.tls_set() # Enable TLS for port 8883

def connect_mqtt():
    try:
        client.connect(BROKER, PORT, 60)
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    if connect_mqtt():
        print(f"Connected to MQTT Broker: {BROKER}")
        
        dist = 30.0  # Initial distance in cm from top
        p_day = 150.0 # Initial 24h usage
        
        try:
            while True:
                # Simulate data
                # Water consumption increases distance from top
                usage = random.uniform(0.1, 0.5)
                dist += usage * 0.5 
                p_day += usage
                
                if dist > 180:
                    dist = 20.0 # Refill
                
                payload = {
                    "dist": round(dist, 2),
                    "p_10": round(usage, 2),
                    "p_day": round(p_day, 2),
                    "time": datetime.now().isoformat(),
                    "node_id": "sim_node_001"
                }
                
                client.publish(TOPIC, json.dumps(payload))
                print(f"🚀 Published: {payload}")
                
                time.sleep(5)
        except KeyboardInterrupt:
            print("Simulator stopped.")
            client.disconnect()
    else:
        print("Could not start simulator.")
