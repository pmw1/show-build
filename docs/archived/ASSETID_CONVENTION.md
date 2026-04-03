# AssetID Assignment Convention

## Overview
AssetIDs are unique, permanent identifiers assigned to every entity in the Show-Build system. Once assigned, an AssetID never changes and provides complete tracking throughout the entity's lifecycle.

## AssetID Format

```
[PREFIX][TIMESTAMP][RANDOM]
```

**Example**: `SEG1h2k3m4nABC123`

- **PREFIX** (3 chars): Entity type identifier
- **TIMESTAMP** (8 chars): Base36 encoded millisecond timestamp
- **RANDOM** (6 chars): Random alphanumeric for uniqueness

## Entity Prefixes

| Prefix | Entity Type | Example ID |
|--------|------------|------------|
| ORG | Organization | ORG1h2k3m4nXYZ789 |
| SHW | Show | SHW1h2k3m4nDEF456 |
| SSN | Season/Series | SSN1h2k3m4nGHI012 |
| EPS | Episode | EPS1h2k3m4nJKL345 |
| BLK | Block | BLK1h2k3m4nMNO678 |
| SEG | Segment | SEG1h2k3m4nPQR901 |
| SCR | Script | SCR1h2k3m4nSTU234 |
| ELM | Element | ELM1h2k3m4nVWX567 |
| CUE | Cue | CUE1h2k3m4nYZA890 |
| AST | Generic Asset | AST1h2k3m4nBCD123 |

## Assignment Rules

### 1. When to Assign

**ALWAYS assign AssetID when:**
- Creating any new entity
- Importing content from external sources
- Duplicating existing entities (duplicate gets new ID)
- Migrating from legacy system

**NEVER assign AssetID when:**
- Updating existing entity
- Moving entity (e.g., segment between episodes)
- Changing entity status

### 2. Request Requirements

When requesting an AssetID, you MUST provide:

```python
{
    "entity_type": "segment",           # Required: What type of entity
    "reason": "create",                  # Required: Why you need the ID
    "requested_by": "user@example.com",  # Required: Who is requesting
    "linked_to": [                       # Optional: Related AssetIDs
        {
            "asset_id": "EPS123ABC",
            "link_type": "belongs_to"
        }
    ],
    "context": {                         # Optional: Additional context
        "source": "web_editor",
        "action": "new_segment_creation"
    }
}
```

### 3. Relationship Types

When linking AssetIDs, use these standard relationship types:

| Link Type | Description | Example |
|-----------|-------------|---------|
| parent_child | Hierarchical relationship | Episode → Segment |
| belongs_to | Membership relationship | Segment belongs to Episode |
| contains | Container relationship | Block contains Segments |
| derived_from | Created from another asset | Clip derived from Segment |
| references | References another asset | Cue references Element |
| replaces | Replaces deprecated asset | New version replaces old |
| extracted_from | Extracted portion | Quote extracted from transcript |
| related_to | General relationship | Segment related to another |
| duplicate_of | Duplicate content | Copy of existing asset |
| version_of | Different version | Draft/final versions |

### 4. Request Reasons

Standard reasons for requesting AssetIDs:

| Reason | When to Use |
|--------|-------------|
| create | Creating new entity from scratch |
| import | Importing from external source |
| duplicate | Creating copy of existing entity |
| migration | Migrating from old system |
| replacement | Replacing lost/damaged ID |
| test | Testing/development purposes |

## Usage Examples

### Creating a New Segment

```python
from services.asset_id import AssetIDService

asset_id = AssetIDService.request_asset_id(
    db=db,
    entity_type="segment",
    reason="create",
    requested_by="josh@disaffected.fm",
    linked_to=[
        {"asset_id": "EPS20241201ABC", "link_type": "belongs_to"},
        {"asset_id": "BLK20241201DEF", "link_type": "contains"}
    ],
    context={
        "source": "web_editor",
        "episode_number": "0237",
        "block": "A",
        "segment_title": "Opening Monologue"
    }
)
# Returns: SEG1h2k3m4nPQR901
```

### Importing Media Element

```python
asset_id = AssetIDService.request_asset_id(
    db=db,
    entity_type="element",
    reason="import",
    requested_by="automation@disaffected.fm",
    linked_to=[
        {"asset_id": "SEG1h2k3m4nPQR901", "link_type": "belongs_to"}
    ],
    context={
        "source": "media_upload",
        "file_path": "/videos/intro.mp4",
        "file_type": "video",
        "duration": 30
    }
)
# Returns: ELM1h2k3m4nVWX567
```

### Creating Cue for Element

```python
asset_id = AssetIDService.request_asset_id(
    db=db,
    entity_type="cue",
    reason="create",
    requested_by="josh@disaffected.fm",
    linked_to=[
        {"asset_id": "SEG1h2k3m4nPQR901", "link_type": "belongs_to"},
        {"asset_id": "ELM1h2k3m4nVWX567", "link_type": "references"}
    ],
    context={
        "cue_type": "media",
        "time_offset": 45.5,
        "action": "play_video"
    }
)
# Returns: CUE1h2k3m4nYZA890
```

## Pending Messages

You can attach messages to AssetIDs that don't exist yet:

```python
AssetIDService.add_pending_message(
    db=db,
    future_asset_id="SEG1h2k3m4nFUTURE",
    message="Remember to add B-roll footage here",
    message_type="production",
    priority=8,
    user_id="director@disaffected.fm"
)
```

When `SEG1h2k3m4nFUTURE` is created, the message will be automatically delivered.

## Tracking & History

Every AssetID maintains complete history:

```python
history = AssetIDService.get_asset_history(db, "SEG1h2k3m4nPQR901")

# Returns:
{
    "asset_id": "SEG1h2k3m4nPQR901",
    "entity_type": "segment",
    "created_at": "2024-12-01T10:30:00Z",
    "requested_by": "josh@disaffected.fm",
    "request_reason": "create",
    "initial_links": [...],
    "relationships": {
        "as_source": [...],
        "as_target": [...]
    },
    "messages": [...],
    "metadata": {...}
}
```

## Best Practices

1. **Request Early**: Get AssetID as soon as entity is conceptualized
2. **Link Appropriately**: Always link to parent/related entities
3. **Provide Context**: Include rich context for future reference
4. **Use Standard Types**: Stick to defined relationship and reason types
5. **Never Reuse**: Each entity gets ONE AssetID for life
6. **Track Everything**: The more metadata, the better

## Migration from Legacy System

For existing content without AssetIDs:

```python
# Migration example for existing episode
asset_id = AssetIDService.request_asset_id(
    db=db,
    entity_type="episode",
    reason="migration",
    requested_by="migration_script",
    context={
        "legacy_id": "0237",
        "migration_date": "2024-12-01",
        "source_system": "markdown_files"
    }
)
```

## MQTT Events

AssetID operations trigger MQTT events:

- **Topic**: `assetid/created/{entity_type}`
- **Payload**: `{"asset_id": "...", "entity_type": "...", "timestamp": "..."}`

Subscribe to track AssetID creation in real-time:

```python
# Subscribe to all segment creations
mqtt_client.subscribe("assetid/created/segment")
```

---

*This convention ensures consistent, trackable AssetID assignment across the Show-Build system.*