curl -X POST http://192.168.51.210:8080/write \
  -H "Content-Type: application/json" \
  -d '{
    "path":"/tmp/remote-test.txt",
    "content":"Hello from AgentIO!",
    "overwrite":true
  }'

