curl -X POST "http://localhost:8888/publish/" \
     -H "Content-Type: application/json" \
     -d '{
           "topic": "ffmpeg/command",
           "message": "ffmpeg -version"
         }'
