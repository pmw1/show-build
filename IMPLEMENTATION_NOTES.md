# Show-Build Implementation Notes

## Recently Implemented Features

### Duration Analysis API (2025-08-16)

**Endpoint:** `/api/duration/getDuration`

**Purpose:** Temporary trigger to analyze SOT (Sound on Tape) duration using FFprobe and update markdown Duration fields

**Functionality:**
- Takes AssetID as input
- Looks up AssetID in registry to determine type (cue SOT vs rundown item) 
- For cue SOT: extracts MediaURL, processes with FFprobe, updates duration field in cue block
- For rundown item: batch processes all related SOTs, updates individual cue durations and calculates total
- Returns duration in HH:MM:SS format

**Files Added:**
- `/app/duration_analysis_router.py` - Main implementation
- Added to main.py router includes

**Status:** ✅ Implemented and deployed

---

## Next Focus Areas

### Unified AssetID System (2025-08-16)

**Endpoint:** `/newAssetID` (unified), plus legacy endpoints

**Purpose:** Universal AssetID generation for all asset types with database storage and parent-child linkage

**Functionality:**
- Unified endpoint handles all asset types: episode, segment, cue, ad, promo, cta
- Creates appropriate database records in episodes, segments, cues, or rundown_items tables
- Automatic parent-child relationship linkage via AssetLinks
- Backward compatible legacy endpoints at `/generate_asset_id/{type}`
- Full AssetID tracking through enhanced AssetID service

**Supported Asset Types:**
- `episode`: Creates episode record with episode_number, auto-creates default org/show/season structure
- `segment`: Creates segment record with slug, links to parent episode AssetID
- `cue`: Creates cue record with slug and cue_type (SOT, GFX, FSQ, VO, NET), links to parent segment
- `ad`, `promo`, `cta`: Creates rundown_item records for advertisements/promotions/CTAs

**Parent Linkage:**
- Episodes: No parent needed (top-level)
- Segments: parent_asset_id should be episode AssetID
- Cues: parent_asset_id should be segment AssetID
- Ads/Promos/CTAs: parent_asset_id optional (creates default rundown if none)

**Files Added:**
- `/app/new_assetid_router.py` - Main unified implementation
- Added to main.py router includes
- Enhanced `/generate_asset_id/rundown` and `/generate_asset_id/cue` legacy endpoints

**Test Results:** ✅ All asset types tested successfully with proper database storage and linkage

**Examples:**
```bash
# Create episode
curl -X POST "/newAssetID" -d '{"asset_type": "episode", "episode_number": 123, "slug": "test-episode"}'

# Create segment linked to episode  
curl -X POST "/newAssetID" -d '{"asset_type": "segment", "slug": "test-segment", "parent_asset_id": "EPSXXX"}'

# Create cue linked to segment
curl -X POST "/newAssetID" -d '{"asset_type": "cue", "slug": "sot-cue", "parent_asset_id": "SEGXXX", "cue_type": "SOT"}'
```

**Status:** ✅ Implemented and deployed
