import json
from paho.mqtt import client as mqtt_client
import paho.mqtt.client as mqtt

# Constants for Mosquitto running in Docker
MQTT_BROKER = "mqtt-broker"  # Updated to match the Docker container name
MQTT_PORT = 1883
MQTT_TOPIC = 'preprocessing/command'
CLIENT_ID = 'Preprocessor_Publisher'

def connect_mqtt():
    """Connect to the MQTT broker."""
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}\n")

    client = mqtt_client.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT)

    return client

def publish_message(client, topic, message):
    """Publish a message to the specified MQTT topic."""
    result = client.publish(topic, json.dumps(message))
    status = result[0]
    if status == 0:
        print(f"Message `{message}` sent to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")


def publish_message(topic, message):
    client = mqtt.Client(client_id="fastapi_server", clean_session=True)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker")
            result = client.publish(topic, payload=message)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                raise Exception(f"Failed to publish message: {result.rc}")
            return "Message published successfully"
        else:
            print(f"Failed to connect, return code {rc}")

    client.on_connect = on_connect
    client.connect("mqtt-broker", 1883, 60)
    return client.publish(topic, payload=message).rc == mqtt.MQTT_ERR_SUCCESS







def main():
    # Step 1: Connect to MQTT Broker
    client = connect_mqtt()

    # Read preprocessing jobs from JSON file
    with open('preprocessing_jobs.json', 'r') as file:
        jobs = json.load(file)

    for job in jobs:
        publish_message(client, MQTT_TOPIC, {
            "job_id": job["job_id"],
            "command": job["command"],
            "tool": job["tool"]
        })

if __name__ == '__main__':
    main()