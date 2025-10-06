# FSQ Automatic Asset Generation System

## Overview
Automatic PNG graphic generation system for Full Screen Quote (FSQ) cues. When an FSQ is created via the modal interface, the system automatically generates a broadcast-quality PNG graphic and links it to the cue.

## System Flow

```
User Fills FSQ Modal
        ↓
Submit Button Clicked
        ↓
1. Generate AssetID (via /assetid/generate-legacy)
        ↓
2. Call /api/fsq/generate
        ↓
   - Creates temporary JSON with quote data
   - Calls render_fsq_png.py tool
   - Generates 1920x1080 PNG with transparent background
   - Saves to /episodes/{episode}/assets/quotes/
        ↓
3. Returns asset URL
        ↓
4. FSQ cue created with mediaUrl
        ↓
Ready for production use
```

## Components

### Frontend: FsqModal.vue
**Location**: `/mnt/process/show-build/disaffected-ui/src/components/modals/FsqModal.vue`

**Features**:
- Quote text input with validation (10-500 chars)
- Source/attribution field (required)
- Optional timestamp (HH:MM:SS format)
- Style selection (centered, left, right, large, elegant)
- Duration selection (3s, 5s, 7s, 10s, 15s, custom)
- Live preview of quote rendering
- Automatic AssetID generation
- **NEW**: Automatic PNG asset generation on submit

**Submit Process**:
```javascript
1. Validate form inputs
2. Generate AssetID for cue
3. Generate slug from quote text
4. Call POST /api/fsq/generate with:
   - episode_id
   - quote text
   - source/attribution
   - style
   - slug
   - asset_id
   - duration
   - timestamp (optional)
   - description (optional)
5. Receive asset URL in response
6. Emit cue data with mediaUrl
7. Parent component inserts cue into script
```

### Backend: fsq_asset_router.py
**Location**: `/mnt/process/show-build/app/fsq_asset_router.py`

**Endpoint**: `POST /api/fsq/generate`

**Request Body**:
```json
{
  "episode_id": "0241",
  "quote": "The quote text that will appear full-screen",
  "source": "John Doe, CEO of Company",
  "style": "centered",
  "slug": "quote-about-something",
  "asset_id": "FSQ12345",
  "duration": "00:00:05:00",
  "timestamp": "00:01:23:00",
  "description": "Context about this quote"
}
```

**Response**:
```json
{
  "success": true,
  "asset_path": "/mnt/sync/disaffected/episodes/0241/assets/quotes/fsq_quote-about-something.png",
  "asset_url": "/episodes/0241/assets/quotes/fsq_quote-about-something.png",
  "message": "FSQ asset generated successfully: fsq_quote-about-something.png"
}
```

**Process**:
1. Normalize episode ID (pad to 4 digits)
2. Create episode assets directory if needed
3. Build temporary JSON with quote data
4. Execute render_fsq_png.py Python tool:
   ```bash
   python3 tools/render_fsq_png.py \
     --json /tmp/quote_data.json \
     --output /episodes/{episode}/assets/quotes/ \
     --width 1920 \
     --height 1080
   ```
5. Find generated PNG file
6. Return asset path and URL

### Rendering Tool: render_fsq_png.py
**Location**: `/mnt/process/show-build/tools/render_fsq_png.py`

**Features**:
- **Resolution**: 1920x1080 (broadcast HD)
- **Background**: Transparent RGBA
- **Overlay**: 80% height black bar at 75% opacity
- **Font**: Helvetica (with fallbacks to Liberation Sans, DejaVu Sans, Arial)
- **Quote Size**: Automatically calculated to fit available space
- **Attribution Size**: 60% of quote size
- **Text Wrapping**: Smart word wrap with line break support
- **Alignment**: Supports center, left, right
- **Attribution Placement**: Fixed at bottom of black bar

**Design Specifications**:
```
┌─────────────────────────────────────┐
│                                     │ 10% transparent
│   ┌─────────────────────────────┐   │
│   │                             │   │
│   │  "Quote text appears here   │   │ 80% black overlay
│   │   with smart wrapping and   │   │ (75% opacity)
│   │   optimal font sizing"      │   │
│   │                             │   │
│   │      — Attribution Name     │   │
│   │                             │   │
│   └─────────────────────────────┘   │
│                                     │ 10% transparent
└─────────────────────────────────────┘
```

**Input JSON Format**:
```json
{
  "metadata": {
    "episode": "0241",
    "generated_at": "2025-10-03T12:34:56",
    "asset_id": "FSQ12345"
  },
  "quotes": [
    {
      "slug": "quote-about-something",
      "text": "The quote text that will appear",
      "attribution": "John Doe, CEO",
      "duration": "00:00:05:00",
      "metadata": {
        "align": "centered",
        "timestamp": "00:01:23:00",
        "description": "Context"
      }
    }
  ]
}
```

## File Storage

### Directory Structure
```
/episodes/{episode_id}/
└── assets/
    └── quotes/
        ├── fsq_quote-slug-1.png
        ├── fsq_quote-slug-2.png
        └── fsq_quote-slug-3.png
```

### Naming Convention
- Format: `fsq_{slug}.png`
- Slug: Derived from quote text (lowercase, hyphens, no special chars)
- Example: `fsq_this-is-a-quote.png`

### Asset URL
- Path: `/episodes/{episode_id}/assets/quotes/{filename}`
- Served by: FastAPI StaticFiles or nginx
- Example: `/episodes/0241/assets/quotes/fsq_quote-about-something.png`

## Integration with Cue System

### FSQ Cue Data Structure
```javascript
{
  type: 'FSQ',
  assetId: 'FSQ12345',           // Generated AssetID
  slug: 'quote-about-something',  // URL-friendly identifier
  quote: 'The quote text...',     // Original quote
  source: 'John Doe, CEO',        // Attribution
  timestamp: '00:01:23:00',       // When to show (optional)
  style: 'centered',              // Display style
  duration: '00:00:05:00',        // How long to show
  description: 'Context...',      // Optional description
  mediaUrl: '/episodes/0241/assets/quotes/fsq_quote-about-something.png'
}
```

### Cue Insertion
The FSQ cue is inserted into the script using the standard cue insertion mechanism. The `mediaUrl` field contains the path to the generated PNG graphic.

## Error Handling

### Asset Generation Errors
- **Timeout**: 30-second timeout for rendering
- **File Not Found**: Falls back to finding most recent PNG
- **Permission Errors**: Logged and returned as 500 error
- **Rendering Errors**: Captured from subprocess stderr

### User Feedback
- Loading indicator during generation
- Error message display in modal
- Console logging for debugging
- Success notification on completion

## Usage Example

### Creating an FSQ
1. Click FSQ button in cue toolbar
2. Fill in quote and attribution (required)
3. Optionally set:
   - Timestamp (when to show)
   - Style (centered, left, right)
   - Duration (3s, 5s, 7s, etc.)
   - Description
4. Click "Insert Quote"
5. System automatically:
   - Generates AssetID
   - Creates PNG graphic
   - Saves to episode assets
   - Inserts cue with media link
6. Cue appears in script with PNG ready for production

### Result
- FSQ cue in script with all metadata
- PNG graphic at 1920x1080 resolution
- Transparent background for compositing
- Optimized for broadcast quality
- Ready for video editing software

## API Endpoints

### Generate FSQ Asset
```
POST /api/fsq/generate
Content-Type: application/json
X-API-Key: {your-api-key}

Request:
{
  "episode_id": "0241",
  "quote": "Quote text here",
  "source": "Attribution",
  "style": "centered",
  "slug": "quote-slug",
  "asset_id": "FSQ12345",
  "duration": "00:00:05:00",
  "timestamp": "00:01:23:00",
  "description": "Optional context"
}

Response:
{
  "success": true,
  "asset_path": "/full/path/to/asset.png",
  "asset_url": "/episodes/0241/assets/quotes/fsq_quote-slug.png",
  "message": "FSQ asset generated successfully"
}
```

### Regenerate FSQ Asset
```
POST /api/fsq/regenerate/{asset_id}
Content-Type: application/json
X-API-Key: {your-api-key}

Same request/response as generate endpoint
Useful for updating existing FSQ graphics
```

## Future Enhancements

### Planned Features
- [ ] Multiple style templates (elegant, modern, minimal)
- [ ] Custom font selection
- [ ] Background image support (not just transparent)
- [ ] Color theme customization per quote
- [ ] Animated text reveal effects
- [ ] Video format export (not just PNG)
- [ ] Batch FSQ generation from script
- [ ] FSQ library/template system
- [ ] Preview before generate option
- [ ] Edit FSQ after creation (regenerate asset)

### Integration Opportunities
- **Media Versioning**: Use version system for FSQ variants
- **ComfyUI**: AI-enhanced background generation
- **Asset Management**: Link to unified asset tracking
- **Template System**: Reusable FSQ styles

## Troubleshooting

### Common Issues

**Issue**: "FSQ rendering failed"
- Check render_fsq_png.py is executable
- Verify Python dependencies (Pillow, ImageDraw)
- Check font availability on system
- Review subprocess stderr output

**Issue**: "Generated PNG not found"
- Check episode assets directory permissions
- Verify slug generation (may contain invalid chars)
- Look for PNG in expected location
- Check filesystem case sensitivity

**Issue**: "No episode ID available"
- Ensure currentEpisode prop is passed to modal
- Verify episode ID in route params
- Check EditorPanel provides episode context

**Issue**: "Asset generation timeout"
- Large quotes may take longer to render
- Check system resources
- Increase timeout if needed
- Optimize font loading

### Debug Steps
1. Check browser console for frontend errors
2. Check backend logs: `docker logs show-build-server`
3. Verify episode assets directory exists
4. Test render_fsq_png.py directly:
   ```bash
   python tools/render_fsq_png.py --episode=0241
   ```
5. Check file permissions on assets directory
6. Verify API endpoint is registered: `curl http://localhost:8888/docs`

## Performance

### Rendering Speed
- **Average**: 1-3 seconds per FSQ
- **Factors**: Quote length, system resources, font loading
- **Optimization**: Font caching, reusable image objects

### Storage Impact
- **Per FSQ**: ~50-200 KB (PNG with transparency)
- **Episode**: Varies by quote count
- **Optimization**: PNG compression, resolution options

### Scalability
- **Concurrent Generation**: Supported via async endpoints
- **Batch Processing**: Can process multiple quotes
- **Resource Limits**: Timeout prevents runaway processes

---

## Summary

The FSQ Automatic Asset Generation System provides a seamless workflow for creating broadcast-quality quote graphics:

1. **User-Friendly**: Simple modal interface
2. **Automatic**: No manual PNG creation needed
3. **Broadcast Quality**: 1920x1080 HD resolution
4. **Production Ready**: Transparent backgrounds for compositing
5. **Integrated**: Works with existing cue system
6. **Scalable**: Handles multiple quotes efficiently

This system eliminates the manual graphic design step for FSQ cues, allowing producers to quickly add professional quote overlays to episodes with just a few clicks.
