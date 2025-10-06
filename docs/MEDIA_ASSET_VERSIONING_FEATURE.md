# Media Asset Versioning System - Feature Design

## Overview
Implementation of a versioning system for media assets (images, videos, audio) to enable non-destructive editing workflows, quality management, and transformation tracking.

## Core Concept
Each media asset can have multiple versions with one designated as "featured/active". Versions are tracked with their own AssetIDs and maintain provenance information about their source and transformations.

## Benefits

### 1. Non-destructive Workflow
- Keep originals safe while experimenting
- All edits create new versions rather than overwriting
- Easy rollback to any previous state

### 2. Provenance Tracking
- Know the source of each version
- Track transformation history and operations
- Audit trail for media modifications

### 3. Quality Options
- Low-res versions for editing/previewing
- High-res versions for production/export
- Multiple quality levels per asset

### 4. A/B Testing
- Compare different edits/versions side-by-side
- Quick switching between options
- Visual comparison tools

### 5. Workflow Integration
- ComfyUI outputs become tracked versions
- External tool results (upscaling, background removal) tracked
- Web searches for high-resolution alternatives managed as versions

## Database Schema Design

### New MediaAsset Model
```python
class MediaAsset(Base):
    __tablename__ = "media_assets"

    # Identity
    id = Column(Integer, primary_key=True)
    asset_id = Column(String, unique=True, nullable=False)  # MED-20250103-001

    # Relationship to Cue
    cue_asset_id = Column(String, ForeignKey("cues.asset_id"))  # Links to parent cue
    episode_id = Column(Integer, ForeignKey("episodes.id"))

    # Version Info
    version_number = Column(Integer, nullable=False)  # 1, 2, 3...
    version_label = Column(String)  # "original", "upscaled", "bg-removed", "web-optimized"
    is_featured = Column(Boolean, default=False)  # Active/selected version

    # File Information
    file_path = Column(String, nullable=False)
    file_name = Column(String)
    file_size = Column(Integer)  # bytes
    mime_type = Column(String)

    # Dimensions & Technical
    width = Column(Integer)
    height = Column(Integer)
    duration = Column(Float)  # For video/audio
    format = Column(String)  # jpg, png, mp4, etc.
    color_depth = Column(String)

    # Provenance
    source_operation = Column(String)  # "upload", "upscale", "comfyui-workflow-x", "bg-remove"
    source_asset_id = Column(String)  # Parent version this was derived from
    source_url = Column(String)  # If fetched from web

    # Metadata
    metadata = Column(JSON)  # EXIF, technical details, workflow params
    tags = Column(JSON)  # Searchable tags

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    cue = relationship("Cue", back_populates="media_assets")
```

### Updates to Existing Cue Model
```python
class Cue(Base):
    # ... existing fields ...

    # Media versioning
    featured_media_asset_id = Column(String, ForeignKey("media_assets.asset_id"))

    # Relationships
    media_assets = relationship("MediaAsset", back_populates="cue", cascade="all, delete-orphan")
    featured_media = relationship("MediaAsset", foreign_keys=[featured_media_asset_id])
```

## AssetID Format Options

### Option 1: Hierarchical (Cue-based)
- Format: `{episode}-{type}-{seq}-v{version}`
- Example: `0241-IMG-001-v002`
- Pros: Clear parent-child relationship
- Cons: Complicated when assets are shared across cues

### Option 2: Independent (Standalone)
- Format: `MED-{date}-{seq}`
- Example: `MED-20250103-001`
- Pros: Clean, globally unique, reusable
- Cons: Requires lookup to find cue relationship

### Option 3: Hybrid (Recommended)
- Cue keeps logical AssetID: `0241-IMG-001`
- Media gets physical AssetID: `MED-20250103-001`
- Linked via foreign key relationship
- Best of both worlds

## API Endpoints

### Version Management
```
GET    /api/episodes/{episode_id}/cues/{cue_id}/media/versions
POST   /api/episodes/{episode_id}/cues/{cue_id}/media/versions
GET    /api/media/versions/{asset_id}
PUT    /api/media/versions/{asset_id}
DELETE /api/media/versions/{asset_id}
POST   /api/media/versions/{asset_id}/set-featured
```

### Transformation Operations
```
POST   /api/media/versions/{asset_id}/upscale
POST   /api/media/versions/{asset_id}/remove-background
POST   /api/media/versions/{asset_id}/comfyui-workflow
POST   /api/media/versions/{asset_id}/fetch-high-res
```

## UI Components

### 1. Version Selector (Modify Tab)
- Grid/list view of all versions
- Thumbnail previews
- Version metadata display
  - Version number and label
  - File size and dimensions
  - Source operation
  - Creation date
- "Set as Featured" button
- Quick actions (delete, download, duplicate)

### 2. Version Comparison View
- Side-by-side comparison
- Overlay/blend modes
- Metadata comparison table
- Zoom/pan synchronized

### 3. Derivation Tree
- Visual tree showing version lineage
- Original → Transform → Result chain
- Click to select version
- Hover for details

### 4. Version Creation UI
- "Create New Version" modal
- Source selection (current, original, specific version)
- Operation selection:
  - Upload replacement
  - Upscale (factor, method)
  - Background removal
  - ComfyUI workflow (select workflow)
  - Fetch high-res from web (search)
  - Custom transformation
- Preview before save
- Auto-generate version label

### 5. Featured Version Indicator
- Badge/icon on active version
- Quick toggle in version list
- Visual highlight in metadata panel

## File Storage Strategy

### Directory Structure
```
/episodes/{episode_id}/media/{cue_asset_id}/
  ├── original/
  │   └── MED-20250103-001.jpg
  ├── processed/
  │   ├── MED-20250103-002-upscaled.jpg
  │   ├── MED-20250103-003-bg-removed.png
  │   └── MED-20250103-004-optimized.jpg
  └── metadata/
      └── versions.json
```

### Cleanup Policy
- Keep original always
- Keep featured version always
- Optional: Auto-delete unused versions after N days
- Warn before deletion if version is source for other versions

## Integration Points

### ComfyUI Workflow Integration
- Workflow output auto-creates new version
- Version metadata includes workflow parameters
- Can replay workflow on different source version
- Workflow preset library

### External Tool Integration
- Upscaling services (Topaz, waifu2x, Real-ESRGAN)
- Background removal (remove.bg, PhotoRoom)
- Format conversion
- Compression/optimization
- AI enhancement tools

### Web Search Integration
- Search for higher resolution of same image
- Visual similarity matching
- License/attribution tracking
- Download as new version with source URL

## Implementation Tasks

### Phase 1: Database & Core API
- [ ] Create MediaAsset model and migration
- [ ] Update Cue model with media relationships
- [ ] Implement AssetID generation for media
- [ ] Create version management API endpoints
- [ ] Implement featured version logic
- [ ] Add version CRUD operations

### Phase 2: File Management
- [ ] Update file upload to create versioned assets
- [ ] Implement version file storage structure
- [ ] Add version deletion with file cleanup
- [ ] Implement version duplicate/copy functionality

### Phase 3: Basic UI
- [ ] Add version list to Modify tab
- [ ] Implement version selector component
- [ ] Add "Set as Featured" functionality
- [ ] Create version metadata display
- [ ] Implement version creation modal

### Phase 4: Transformation Operations
- [ ] Implement upscaling operation
- [ ] Add background removal
- [ ] Create format conversion
- [ ] Add image optimization

### Phase 5: Advanced UI
- [ ] Build version comparison view
- [ ] Create derivation tree visualization
- [ ] Add batch operations
- [ ] Implement version tagging/labeling

### Phase 6: External Integrations
- [ ] ComfyUI workflow integration
- [ ] External upscaling service integration
- [ ] Background removal service integration
- [ ] Web image search integration

### Phase 7: Optimization
- [ ] Implement version caching
- [ ] Add lazy loading for version thumbnails
- [ ] Optimize storage with deduplication
- [ ] Add version archival system

## Configuration Options

### Settings to Add
```python
{
    "media_versioning": {
        "enabled": True,
        "auto_version_on_edit": True,
        "max_versions_per_asset": 50,
        "auto_cleanup_unused": False,
        "cleanup_after_days": 30,
        "default_upscale_factor": 2.0,
        "storage_path": "/episodes/{episode_id}/media/{cue_asset_id}/",
        "thumbnail_size": 300,
        "comparison_modes": ["side-by-side", "overlay", "slider"],
        "comfyui_enabled": True,
        "external_services": {
            "upscaling": "local",  # or "topaz", "waifu2x"
            "bg_removal": "local"  # or "remove.bg", "photoroom"
        }
    }
}
```

## Migration Strategy

### For Existing Assets
1. Scan existing media files
2. Create MediaAsset record for each as v1 "original"
3. Link to parent cue
4. Set as featured version
5. Migrate metadata from cue to media_asset
6. Update cue references

### Backward Compatibility
- Cues without versioning continue to work with direct file paths
- Gradual migration as assets are edited
- Fallback to simple file path if versioning disabled

## Future Enhancements

### AI-Powered Features
- Auto-tagging of versions
- Smart version recommendations
- Quality assessment scoring
- Automatic optimal version selection based on context

### Collaboration Features
- Version comments/annotations
- Approval workflows
- Lock versions for review
- Team version sharing

### Analytics
- Version usage tracking
- Storage optimization suggestions
- Transformation pattern analysis
- Quality improvement metrics

## Notes
- Consider storage implications with many versions
- Balance between version history and disk usage
- Thumbnail generation for quick previews
- Metadata indexing for fast search
- Version export/import for backup/restore
