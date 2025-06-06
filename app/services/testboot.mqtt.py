import paho.mqtt.client as mqtt
import json
from pathlib import Path

# Configuration
VIDEO_PATH = "/mnt/sync/disaffected/episodes/S01E02/video.mp4"
THUMBNAIL_DIR = "path/to/assets/images/sots/thumbnails"
THUMBNAIL_FILE = f"{Path(VIDEO_PATH).stem}.png"
ASSET_ID = "asset_123"

# MQTT Configuration
MQTT_BROKER = "your_mqtt_broker"
MQTT_PORT = 1883
MQTT_TASK_TOPIC = "mqtt_task_topic"

def publish_thumbnail_task(video_path, thumbnail_dir, asset_id):
    task_id = f"{asset_id}-thumbnail"
    payload = {
        "task_id": task_id,
        "type": "generate_thumbnail",
        "input": video_path,
        "output": str(Path(thumbnail_dir) / THUMBNAIL_FILE)
    }

    mqtt_client = mqtt.Client()
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

    # Publish the task
    mqtt_client.publish(MQTT_TASK_TOPIC, json.dumps(payload))
    print(f"Published generate_thumbnail task for {video_path} to {THUMBNAIL_FILE}")

if __name__ == "__main__":
    publish_thumbnail_task(VIDEO_PATH, THUMBNAIL_DIR, ASSET_ID)