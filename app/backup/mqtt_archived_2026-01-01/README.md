# MQTT Files Archive

**Date Archived**: 2026-01-01
**Reason**: Removed MQTT infrastructure in favor of Celery + Redis for all async task processing

## Archived Files

1. **preproc_mqtt_listen.py** - Legacy MQTT listener for preprocessing commands
2. **preproc_mqtt_pub.py** - Legacy MQTT publisher for preprocessing tasks
3. **mqttcurl.sh** - MQTT utility script
4. **testboot.mqtt.py** - Test file for MQTT functionality

## Context

These files were part of an earlier preprocessing/job coordination system that used MQTT (eclipse-mosquitto broker). The system has been migrated to use Celery + Redis for all async task processing, which provides:

- Better task queuing and priority management
- Built-in result tracking
- Retry logic and error handling
- Task monitoring via Flower
- Worker pool management

## MQTT Broker Status

- **Container**: `mqtt-broker` (eclipse-mosquitto)
- **Status**: Stopped and removed from docker-compose.yml
- **Last Active**: 2026-01-01 (only health check connections, no actual message traffic)

## Restoration Instructions

If MQTT functionality needs to be restored:

1. Move these files back to their original locations:
   - `preproc_mqtt_listen.py` → `/app/`
   - `preproc_mqtt_pub.py` → `/app/`
   - `mqttcurl.sh` → `/app/`
   - `testboot.mqtt.py` → `/app/services/`

2. Restore MQTT imports in `app/main.py`:
   ```python
   from preproc_mqtt_pub import publish_message
   from preproc_mqtt_listen import MQTTListener
   ```

3. Restore `/publish/` endpoint in `app/main.py` (around line 325)

4. Add back to `app/requirements.txt`:
   ```
   paho-mqtt>=1.6.1
   ```

5. Restore MQTT service in `docker-compose.yml`:
   ```yaml
   mqtt-broker:
     image: eclipse-mosquitto
     container_name: mqtt-broker
     networks:
       - video-post
     ports:
       - "1883:1883"
       - "9001:9001"
     restart: unless-stopped
   ```

6. Add `mqtt-broker` to server `depends_on` in docker-compose.yml

7. Rebuild Docker images and restart services

## References

- **Architecture Decision**: See `docs/ARCHITECTURE_DECISIONS.md#decision-2`
- **Migration Checklist**: See `ACTIVE_WORK_QUEUE.md` Priority 1 tasks
- **Celery Configuration**: See `app/celery_app.py` for current async task system

## Notes

- MQTT was determined to be unnecessary overhead for Show-Build's requirements
- All async tasks (script compilation, asset processing, FSQ generation, etc.) now handled by Celery
- Celery provides superior capabilities for task queuing, results, retries, and monitoring
- No functionality was lost in this migration
