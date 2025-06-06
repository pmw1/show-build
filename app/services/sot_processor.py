import paho.mqtt.client as mqtt
import json
from pathlib import Path
import logging
import time

# Version: 1.0.1
# Date: May 21, 2025

logging.basicConfig(
    filename='/home/logs/sot_processor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# MQTT configuration
MQTT_BROKER = "192.168.51.210"
MQTT_PORT = 1883
MQTT_TASK_TOPIC = "ffmpeg/tasks"
MQTT_RESULT_TOPIC = "ffmpeg/results"
MQTT_CLIENT_ID = "sot_processor"

mqtt_results = {}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT broker")
        client.subscribe(MQTT_RESULT_TOPIC)
    else:
        logging.error(f"Failed to connect to MQTT broker with code {rc}")

def on_message(client, userdata, msg):
    try:
        result = json.loads(msg.payload.decode())
        task_id = result.get("task_id")
        mqtt_results[task_id] = result
        logging.info(f"Received MQTT result for task {task_id}: {result}")
    except Exception as e:
        logging.error(f"Error processing MQTT message: {e}")

mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

def process_sot(video_path, markdown_file, asset_id, slug, description, trim_start, trim_end):
    try:
        video_path = Path(f"/mnt/sync/disaffected/{video_path}")
        markdown_path = Path(markdown_file)
        episode = video_path.parts[3]  # /mnt/sync/disaffected/episodes/EPISODE/...
        output_dir = Path(f"/shared_media/{episode}/assets")

        # Ensure output directories
        (output_dir / "audio/sots").mkdir(parents=True, exist_ok=True)
        (output_dir / "videos/previews").mkdir(parents=True, exist_ok=True)
        (output_dir / "images/sots/thumbnails").mkdir(parents=True, exist_ok=True)

        task_id = f"{asset_id}_{int(time.time())}"

        # MP3 conversion
        mp3_path = output_dir / "audio/sots" / f"{slug}.mp3"
        mqtt_client.publish(MQTT_TASK_TOPIC, json.dumps({
            "task_id": task_id,
            "type": "convert_to_mp3",
            "input": str(video_path),
            "output": str(mp3_path),
            "params": ["-vn", "-acodec", "mp3", "-ar", "16000"]
        }))
        logging.info(f"Published MP3 task {task_id}")

        # Preview video
        preview_path = output_dir / "videos/previews" / f"{slug}-preview.mp4"
        mqtt_client.publish(MQTT_TASK_TOPIC, json.dumps({
            "task_id": task_id,
            "type": "generate_preview",
            "input": str(video_path),
            "output": str(preview_path),
            "params": [
                "-vf", "drawtext=text='%{pts\\:hms}':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:x=10:y=10",
                "-c:v", "libx264", "-c:a", "copy"
            ]
        }))
        logging.info(f"Published preview task {task_id}")

        # Duration extraction
        mqtt_client.publish(MQTT_TASK_TOPIC, json.dumps({
            "task_id": task_id,
            "type": "extract_duration",
            "input": str(video_path),
            "params": [
                "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1"
            ]
        }))
        logging.info(f"Published duration task {task_id}")

        # Thumbnail
        thumb_path = output_dir / "images/sots/thumbnails" / f"thumb-{slug}.png"
        mqtt_client.publish(MQTT_TASK_TOPIC, json.dumps({
            "task_id": task_id,
            "type": "generate_thumbnail",
            "input": str(video_path),
            "output": str(thumb_path),
            "params": ["-ss", "1", "-vframes", "1"]
        }))
        logging.info(f"Published thumbnail task {task_id}")

        # Trim video
        trimmed_path = video_path
        if trim_start and trim_end:
            trimmed_path = output_dir / "videos" / f"{slug}-trimmed.{video_path.suffix}"
            mqtt_client.publish(MQTT_TASK_TOPIC, json.dumps({
                "task_id": task_id,
                "type": "trim_video",
                "input": str(video_path),
                "output": str(trimmed_path),
                "params": ["-ss", trim_start, "-to", trim_end, "-c", "copy"]
            }))
            logging.info(f"Published trim task {task_id}")

        # Wait for results
        timeout = 60
        start_time = time.time()
        duration_str = "00:00:00"
        while time.time() - start_time < timeout:
            if task_id in mqtt_results and mqtt_results[task_id].get("status") == "success":
                if "duration" in mqtt_results[task_id]:
                    duration = float(mqtt_results[task_id]["duration"])
                    duration_str = f"{int(duration // 3600):02d}:{int((duration % 3600) // 60):02d}:{int(duration % 60):02d}"
                break
            time.sleep(1)
        else:
            logging.error(f"Timeout waiting for MQTT results for task {task_id}")
            raise TimeoutError(f"FFmpeg processing timed out for task {task_id}")

        # Stub transcription
        transcription = "Transcription pending"

        # Update markdown
        with open(markdown_path, 'r') as f:
            content = f.read()
        cue_block = f"""<<!-- Begin Cue -->>
[Type:SOT]
[AssetID:{asset_id}]
[Slug:{slug}]
[Description:{description}]
[MediaURL:../assets/videos/{trimmed_path.name}]
[Duration:{duration_str}]
[TrimStart:{trim_start}]
[TrimEnd:{trim_end}]
[Transcription:{transcription}]
[Status:Processed]
<img src="../assets/images/sots/thumbnails/thumb-{slug}.png"/>
<<!-- End Cue -->>
"""
        new_content = content.replace(f"[AssetID:{asset_id}]", cue_block, 1)
        with open(markdown_path, 'w') as f:
            f.write(new_content)

        logging.info(f"Processed SOT for {video_path}")
        return {
            "duration": duration_str,
            "transcription": transcription,
            "thumbnail": str(thumb_path),
            "preview": str(preview_path),
            "mp3": str(mp3_path)
        }
    except Exception as e:
        logging.error(f"Error processing SOT {video_path}: {e}")
        raise