# Media Upload

Upload media files before attaching them to tweets.

---

## Simple Upload

### POST /2/media/upload — Upload Media (Simple)

**URL**: `https://api.x.com/2/media/upload`

**Auth**: OAuth 2.0 User Token (scope: `media.write`) or OAuth 1.0a

**Content-Type**: `application/json` or `multipart/form-data`

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `media` | binary | Yes | File to upload |
| `media_category` | string | Yes | `tweet_image`, `dm_image`, `subtitles` |
| `media_type` | string | No | MIME type |
| `additional_owners` | array | No | User IDs for co-ownership |
| `shared` | boolean | No | Default: `false` |

### Supported Image Types

- `image/jpeg`
- `image/png`
- `image/bmp`
- `image/webp`
- `image/pjpeg`
- `image/tiff`

### Response

```json
{
  "data": {
    "id": "1455952740635586573",
    "media_key": "3_1455952740635586573",
    "size": 245678,
    "expires_after_secs": 86400,
    "processing_info": {
      "state": "succeeded",
      "progress_percent": 100
    }
  }
}
```

---

## Chunked Upload (Large Files)

For videos and large files, use the 3-step chunked upload process.

### Step 1: POST /2/media/upload/initialize — Initialize Upload

**URL**: `https://api.x.com/2/media/upload/initialize`

**Auth**: OAuth 2.0 User Token (scope: `media.write`)

```json
{
  "media_type": "video/mp4",
  "total_bytes": 5242880,
  "media_category": "amplify_video"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `media_type` | string | Yes | MIME type of the file |
| `total_bytes` | integer | Yes | File size in bytes (max 17,179,869,184 = ~17 GB) |
| `media_category` | string | No | `amplify_video`, `tweet_video`, `tweet_image`, `tweet_gif`, `dm_video`, `dm_image`, `dm_gif`, `subtitles` |
| `shared` | boolean | No | Allow other users to attach |
| `additional_owners` | array | No | Co-owner user IDs |

### Supported Video Types

- `video/mp4`
- `video/webm`
- `video/mp2t`
- `video/quicktime`

### Supported Subtitle Types

- `text/srt`
- `text/vtt`

### Supported 3D Model Types

- `model/gltf-binary`
- `model/usdz+zip`

### Response

```json
{
  "data": {
    "id": "1455952740635586573",
    "media_key": "13_1455952740635586573",
    "expires_after_secs": 86400
  }
}
```

### Step 2: POST /2/media/upload/append — Upload Chunks

**URL**: `https://api.x.com/2/media/upload/append`

Upload the file in chunks (recommended 5 MB per chunk).

| Field | Type | Description |
|-------|------|-------------|
| `media_id` | string | ID from initialize step |
| `segment_index` | integer | 0-based chunk index |
| `media` | binary | Chunk data |

### Step 3: POST /2/media/upload/finalize — Finalize Upload

**URL**: `https://api.x.com/2/media/upload/finalize`

```json
{
  "media_id": "1455952740635586573"
}
```

### Processing Status Check

### GET /2/media/upload/status — Check Processing

**URL**: `https://api.x.com/2/media/upload/status?media_id=...`

**Processing States:**

| State | Description |
|-------|-------------|
| `pending` | Upload received, not yet processing |
| `in_progress` | Currently processing |
| `succeeded` | Ready to attach to tweet |
| `failed` | Processing failed |

```json
{
  "data": {
    "id": "1455952740635586573",
    "processing_info": {
      "state": "in_progress",
      "progress_percent": 45,
      "check_after_secs": 5
    }
  }
}
```

---

## Media Size Limits

| Type | Max Size |
|------|----------|
| Images (simple upload) | 5 MB |
| GIFs | 15 MB |
| Video (chunked upload) | 512 MB (tweet), ~17 GB (amplify) |
| Subtitles | 1 MB |

## Usage: Attach Media to Tweet

```bash
# 1. Upload media
MEDIA_ID=$(curl -X POST "https://api.x.com/2/media/upload" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -F "media=@photo.jpg" \
  -F "media_category=tweet_image" | jq -r '.data.id')

# 2. Create tweet with media
curl -X POST "https://api.x.com/2/tweets" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"Check this out!\", \"media\": {\"media_ids\": [\"$MEDIA_ID\"]}}"
```
