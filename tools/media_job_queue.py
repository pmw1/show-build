"""
Media Job Queue Tool

This tool allows you to queue media processing jobs (e.g., video/audio tasks) to be handled by FFmpeg running in a Docker container. Jobs are published to an MQTT topic for processing by the FFmpeg builder Docker. Status and telemetry can be extended for frontend integration.
"""

import json
import time
import uuid
import paho.mqtt.client as mqtt
from pathlib import Path

# MQTT Configuration
MQTT_BROKER = 'localhost'  # Update if needed
MQTT_PORT = 1883
MQTT_TOPIC = 'media/jobs/queue'

# Job queue file (for persistence/logging)
QUEUE_FILE = Path('media_job_queue.json')


def queue_job(file_path, operation, options=None):
    job_id = str(uuid.uuid4())
    job = {
        'id': job_id,
        'file_path': file_path,
        'operation': operation,
        'options': options or {},
        'status': 'queued',
        'timestamp': time.time()
    }
    # Save to queue file
    jobs = []
    if QUEUE_FILE.exists():
        with open(QUEUE_FILE, 'r') as f:
            jobs = json.load(f)
    jobs.append(job)
    with open(QUEUE_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)
    # Publish to MQTT
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.publish(MQTT_TOPIC, json.dumps(job))
    client.disconnect()
    print(f"Queued job {job_id} for {file_path} ({operation})")
    return job_id


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Queue a media processing job.')
    parser.add_argument('file_path', help='Path to the media file')
    parser.add_argument('operation', help='Operation to perform (e.g., trim, convert, preview)')
    parser.add_argument('--options', help='JSON string of additional options', default='{}')
    args = parser.parse_args()
    options = json.loads(args.options)
    queue_job(args.file_path, args.operation, options)

if __name__ == '__main__':
    main()
