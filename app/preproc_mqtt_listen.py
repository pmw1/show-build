import json
import subprocess
from paho.mqtt import client as mqtt_client
import paho.mqtt.client as mqtt
import threading
import time

# Constants for Mosquitto running in Docker
MQTT_BROKER = 'mqtt-broker'  # Use your broker hostname
MQTT_PORT = 1883
MQTT_TOPIC = 'preprocessing/command'
CLIENT_ID = 'Preprocessor_Listener'


class MQTTListener:
    def __init__(self):
        self.client = mqtt.Client()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code:", rc)
        self.client.subscribe("#")  # subscribe to all topics, or specific ones

    def on_message(self, client, userdata, msg):
        print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

    def start(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        connected = False
        while not connected:
            try:
                self.client.connect("mqtt-broker", 1883, 60)
                connected = True
            except ConnectionRefusedError:
                print("MQTT connection refused. Retrying in 5 seconds...")
                time.sleep(5)

        self.client.loop_forever()

    def subscribe_to_topic(self, topic):
        self.client.subscribe(topic)







def connect_mqtt():
    """Connect to the MQTT broker."""
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(MQTT_TOPIC)
        else:
            print(f"Failed to connect, return code {rc}\n")

    client = mqtt_client.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT)

    return client

def execute_command(command, tool):
    """Execute the command using the specified tool."""
    try:
        if tool == "ffmpeg":
            subprocess.run(["ffmpeg"] + command)
        elif tool == "sox":
            subprocess.run(["sox"] + command)
        elif tool == "convert":
            subprocess.run(["convert"] + command)
        elif tool == "python":
            subprocess.run(["python3"] + command)  # Assuming Python3 is the default Python interpreter
        else:
            print(f"Unknown tool: {tool}")
    except Exception as e:
        print(f"Failed to execute command with error: {e}")

def main():
    client = connect_mqtt()

    def on_message(client, userdata, msg):
        message = json.loads(msg.payload.decode())
        job_id = message["job_id"]
        command = message["command"]
        tool = message["tool"]

        print(f"Received job {job_id} for tool '{tool}' with command: {command}")
        execute_command(command, tool)

    client.on_message = on_message

    # Blocking loop to keep the listener running
    client.loop_forever()



if __name__ == '__main__':
    main()