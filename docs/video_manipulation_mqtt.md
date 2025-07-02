
              # Video Manipulation & MQTT Messaging System
## Overview
This document describes the architecture, workflow, and integration of the video manipulation tools and the MQTT messaging system within the Show Builder project. It includes textual flow diagrams and block representations to clarify the system’s operation.

---

## System Components

- **Watch Folder Monitor**: Observes a directory for new media files.
- **Job Publisher (Python, Dockerized)**: Publishes job requests to the MQTT broker when new files are detected.
- **MQTT Broker (Mosquitto, Dockerized)**: Routes messages between publishers and workers.
- **FFmpeg Worker (Dockerized)**: Subscribes to job topics, processes media (e.g., converts to MP3), and publishes results.
- **Result Listener/Frontend**: Optionally subscribes to result topics for status/telemetry.

---

## Workflow Diagram (Textual)

```
[Watch Folder] 
     |
     v
[Job Publisher Script] --(MQTT:ffmpeg/tasks)--> [MQTT Broker] --(MQTT:ffmpeg/tasks)--> [FFmpeg Worker]
                                                                 |
                                                                 v
                                                    (MQTT:ffmpeg/results)
                                                                 |
                                                                 v
                                                      [Result Listener/Frontend]
```

---

## Block Diagram (Textual)

```
+-------------------+      MQTT:ffmpeg/tasks      +-------------------+
|  Job Publisher    |--------------------------->|   MQTT Broker     |
|  (Python Script)  |                           |   (Mosquitto)     |
+-------------------+                           +-------------------+
         |                                               |
         |                                               |
         |      MQTT:ffmpeg/results                      |
         +-----------------------------------------------+
         |                                               |
+-------------------+      MQTT:ffmpeg/tasks      +-------------------+
|  FFmpeg Worker    |<---------------------------|   MQTT Broker     |
|  (Docker)         |                            |   (Mosquitto)     |
+-------------------+                            +-------------------+
         |
         v
   [Media Output]
```

---

## Job Payload Example

```json
{
  "task_id": "unique-task-id",
  "operation": "convert_to_mp3",
  "input_file": "/watch_folder/video.mp4",
  "output_file": "/output_folder/video.mp3",
  "options": {}
}
```

---

## Detailed Flow
1. **File Detection**: The Watch Folder Monitor detects a new file.
2. **Job Creation**: The Job Publisher creates a job payload and publishes it to `ffmpeg/tasks` via MQTT.
3. **Job Processing**: The FFmpeg Worker receives the job, processes the file (e.g., converts to MP3), and saves the output.
4. **Result Reporting**: The Worker publishes a result/status message to `ffmpeg/results`.
5. **Frontend/Listener**: Optionally, a frontend or listener script can subscribe to `ffmpeg/results` for real-time updates and display progress/status.

---

## Extensibility
- Additional operations (e.g., thumbnail generation, video trimming) can be added by defining new `operation` types in the job payload.
- Multiple workers can subscribe to the same topic for load balancing.
- The system is fully Dockerized for portability and isolation.

---

## Notes
- Ensure all paths are accessible to the relevant Docker containers (use shared volumes).
- MQTT topics should be consistent and documented for all job types.
- Security: Consider authentication for MQTT if exposed beyond localhost.

---

*This document will be updated as the system evolves. Add diagrams, payload examples, and workflow notes as new features are implemented.*
