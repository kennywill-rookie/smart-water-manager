import paho.mqtt.client as mqtt
import json
import requests
from datetime import datetime
import time
from dotenv import load_dotenv
load_dotenv()
from config import SUPABASE_URL, SUPABASE_KEY, TABLE_NAME, BROKER, PORT, TOPIC, TANK_HEIGHT

# --- Configuration ---
# MQTT Broker Settings

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ Connected to MQTT Broker: {BROKER}")
        client.subscribe(TOPIC)
        print(f"📡 Subscribed to topic: {TOPIC}")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"📥 Received data: {payload}")
        
        # New Payload Format:
        # dist : distance in Cm from the top of the tank to the water level.
        # p_10 : volume of used water during last incoming data
        # p_day : cumulative volume of used water in 24 hours duration
        # time : timezone time of sending the data
        
        dist = payload.get("dist")
        p_10 = payload.get("p_10")
        p_day = payload.get("p_day")
        data_time_str = payload.get("time")

        # Handle time format: "MM/DD HH:MM"
        try:
            if data_time_str:
                # Add current year to the date string
                current_year = datetime.now().year
                full_time_str = f"{current_year}/{data_time_str}"
                # Parse "YYYY/MM/DD HH:MM"
                parsed_time = datetime.strptime(full_time_str, "%Y/%m/%d %H:%M")
                created_at = parsed_time.isoformat()
            else:
                created_at = datetime.now().isoformat()
        except Exception as e:
            print(f"⚠️ Time parsing error: {e}. Using current time.")
            created_at = datetime.now().isoformat()

        # Calculate water level percentage
        # level (%) = (TANK_HEIGHT - dist) / TANK_HEIGHT * 100
        if dist is not None:
            water_level = max(0, min(100, ((TANK_HEIGHT - dist) / TANK_HEIGHT) * 100))
        else:
            water_level = 0

        # Mapping incoming data to Supabase table
        data = {
            "created_at": created_at,
            "water_level": round(water_level, 2),
            "usage_volume": p_day,  # Using p_day as total usage volume for the dashboard
            "node_id": payload.get("node_id", "default_node")
        }
        
        # Save to Supabase
        response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}", headers=headers, json=data)
        if response.status_code == 201:
            print("💾 Data saved to Supabase successfully.")
        else:
            print(f"⚠️ Failed to save data: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error processing message: {e}")

def run_subscriber():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    # Port 8883 is usually TLS/SSL
    client.tls_set() 
    
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"❌ MQTT Connection Error: {e}")
        time.sleep(5)
        run_subscriber()

if __name__ == "__main__":
    print("🚀 Starting Water Management MQTT Subscriber...")
    run_subscriber()
1