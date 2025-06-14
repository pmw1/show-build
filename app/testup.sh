curl -X POST "http://localhost:8000/preproc_sot" \
     -F "file=@/home/user/videos/sample.mp4" \
     -F "type=sampleType" \
     -F "assetID=123456" \
     -F "episode=01" \
     -F "slug=example-slug"
