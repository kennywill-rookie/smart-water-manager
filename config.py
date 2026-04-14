import os

# Shared Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
TABLE_NAME = os.environ.get("TABLE_NAME", "water_management")

# MQTT Broker Settings
BROKER = os.environ.get("MQTT_BROKER", "broker.hivemq.com")
PORT = int(os.environ.get("MQTT_PORT", "8883"))
TOPIC = os.environ.get("MQTT_TOPIC", "goshen/lora/node1")

# Tank Configuration
TANK_HEIGHT = int(os.environ.get("TANK_HEIGHT", "200"))  # cm
