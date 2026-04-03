# Test Data Management System

This document explains the test data management system implemented in Show-Build to cleanly separate test/dummy data from production content.

## Overview

Every content table in the database now includes an `is_test_data` boolean field that flags whether an entry is test/dummy data (`TRUE`) or production data (`FALSE`). This provides clean separation and safe bulk operations.

## Implementation Details

### Database Schema

The following tables now include `is_test_data BOOLEAN DEFAULT FALSE NOT NULL`:

**Content Tables (High Priority):**
- `episodes_legacy` - Legacy episode metadata
- `rundown_items_legacy` - Legacy rundown segments  
- `episodes` - V2 episode data
- `rundown_items` - V2 rundown content
- `assets` - Media files and assets
- `organizations` - Organization entities
- `shows` - Show/program data

**System Tables:**
- `users` - User accounts (test users)
- `processing_jobs` - Background job tracking
- `cue_blocks` - Production cue data
- `extracted_quotes` - Quote extraction results

### Model Integration

All relevant SQLAlchemy models in `app/models/` package (with backward-compat shim at `models_v2.py`) and `models_user.py` have been updated with:

```python
# Test data flag
is_test_data = Column(Boolean, default=False, nullable=False)  # True for test/dummy data
```

## Usage Guidelines

### Creating Test Data

When creating test/dummy content, explicitly flag it:

```python
# Example: Creating test episode
test_episode = EpisodeLegacy(
    episode_number="9999",
    title="TEST: Sample Episode", 
    is_test_data=True  # ✅ Flag as test data
)

# Example: Creating test user
test_user = User(
    username="testuser123",
    email="test@example.com",
    hashed_password="...",
    is_test_data=True  # ✅ Flag as test user
)
```

### Querying Production Data Only

Filter out test data in production queries:

```python
# Get only production episodes
production_episodes = db.query(EpisodeLegacy).filter(
    EpisodeLegacy.is_test_data == False
).all()

# Get production rundown items for episode
production_items = db.query(RundownItemLegacy).filter(
    RundownItemLegacy.episode_id == episode_id,
    RundownItemLegacy.is_test_data == False
).order_by(RundownItemLegacy.order).all()

# Get production users
real_users = db.query(User).filter(
    User.is_test_data == False,
    User.is_active == True
).all()
```

### API Endpoints

API endpoints should support filtering test data:

```python
@router.get("/episodes")
async def get_episodes(
    exclude_test: bool = True,  # Default to excluding test data
    db: Session = Depends(get_db)
):
    query = db.query(EpisodeLegacy)
    
    if exclude_test:
        query = query.filter(EpisodeLegacy.is_test_data == False)
        
    return query.all()
```

### Frontend Integration

Frontend components can include test data toggles:

```javascript
// Vue component for episode list
const episodes = await api.get('/episodes', {
    params: {
        exclude_test: !showTestData  // User preference
    }
})

// Filter in UI
const productionEpisodes = episodes.filter(ep => !ep.is_test_data)
```

## Test Data Management Operations

### Bulk Test Data Creation

Create consistent test datasets:

```sql
-- Create test organization
INSERT INTO organizations (asset_id, name, slug, is_test_data, created_at) VALUES 
('ORG-TEST-001', 'Test Media Corp', 'test-media-corp', TRUE, NOW());

-- Create test show
INSERT INTO shows (asset_id, organization_id, title, slug, is_test_data, created_at)
SELECT 'SHOW-TEST-001', id, 'Test Show', 'test-show', TRUE, NOW()
FROM organizations WHERE asset_id = 'ORG-TEST-001';

-- Create test episodes
INSERT INTO episodes_legacy (episode_number, title, is_test_data, episode_path) VALUES
('9001', 'TEST: Episode 1', TRUE, '/test/episodes/9001'),
('9002', 'TEST: Episode 2', TRUE, '/test/episodes/9002'),
('9003', 'TEST: Episode 3', TRUE, '/test/episodes/9003');
```

### Bulk Test Data Cleanup

Safely remove test data:

```sql
-- ⚠️ DANGER: This will delete ALL test data
-- Always backup first: ./scripts/backup_before_migration.sh

-- Delete test data in correct order (respecting foreign keys)
DELETE FROM cue_blocks WHERE is_test_data = TRUE;
DELETE FROM rundown_items_legacy WHERE is_test_data = TRUE;
DELETE FROM rundown_items WHERE is_test_data = TRUE;
DELETE FROM assets WHERE is_test_data = TRUE;
DELETE FROM episodes_legacy WHERE is_test_data = TRUE;
DELETE FROM episodes WHERE is_test_data = TRUE;
DELETE FROM shows WHERE is_test_data = TRUE;
DELETE FROM organizations WHERE is_test_data = TRUE;
DELETE FROM processing_jobs WHERE is_test_data = TRUE;
DELETE FROM extracted_quotes WHERE is_test_data = TRUE;
DELETE FROM users WHERE is_test_data = TRUE;
```

### Test Data Analysis

Monitor test data usage:

```sql
-- Count test vs production data by table
SELECT 
    'episodes_legacy' as table_name,
    COUNT(*) FILTER (WHERE is_test_data = FALSE) as production_count,
    COUNT(*) FILTER (WHERE is_test_data = TRUE) as test_count,
    COUNT(*) as total_count
FROM episodes_legacy
UNION ALL
SELECT 
    'rundown_items_legacy',
    COUNT(*) FILTER (WHERE is_test_data = FALSE),
    COUNT(*) FILTER (WHERE is_test_data = TRUE),
    COUNT(*)
FROM rundown_items_legacy
UNION ALL
SELECT 
    'users',
    COUNT(*) FILTER (WHERE is_test_data = FALSE),
    COUNT(*) FILTER (WHERE is_test_data = TRUE),
    COUNT(*)
FROM users;
```

### Test Environment Setup

For development environments, create comprehensive test datasets:

```python
def create_test_dataset():
    """Create comprehensive test dataset for development"""
    
    # Test organization
    org = Organization(
        asset_id="TEST-ORG-001",
        name="Test Broadcasting Corp",
        slug="test-broadcasting",
        is_test_data=True
    )
    db.add(org)
    db.flush()
    
    # Test show
    show = Show(
        asset_id="TEST-SHOW-001", 
        organization_id=org.id,
        title="Test Talk Show",
        slug="test-talk-show",
        is_test_data=True
    )
    db.add(show)
    db.flush()
    
    # Test episodes
    for i in range(1, 6):
        episode = EpisodeLegacy(
            episode_number=f"900{i}",
            title=f"TEST: Episode {i}",
            subtitle=f"Test episode {i} for development",
            status="draft",
            episode_path=f"/test/episodes/900{i}",
            is_test_data=True
        )
        db.add(episode)
        
        # Test rundown items
        for j in range(1, 4):
            item = RundownItemLegacy(
                episode_id=episode.id,
                asset_id=f"TEST-ITEM-{i:02d}-{j:02d}",
                slug=f"test-segment-{j}",
                type="segment",
                order=j,
                title=f"Test Segment {j}",
                script_content=f"This is test content for segment {j}",
                file_path=f"/test/episodes/900{i}/segments/segment-{j}.md",
                is_test_data=True
            )
            db.add(item)
    
    db.commit()
```

## Best Practices

### 1. Naming Conventions

Use clear prefixes for test data:

- **Episodes**: `900X` numbers for test episodes
- **Asset IDs**: `TEST-*` prefix (`TEST-ORG-001`, `TEST-SHOW-001`)
- **Titles**: `TEST:` prefix in titles
- **Usernames**: `test*` prefix (`testuser1`, `testadmin`)
- **Slugs**: `test-*` prefix

### 2. Data Relationships

Maintain referential integrity in test data:

```python
# ✅ Good: Test episode with test rundown items
test_episode = EpisodeLegacy(..., is_test_data=True)
test_item = RundownItemLegacy(..., episode=test_episode, is_test_data=True)

# ❌ Bad: Mixing test and production data
production_episode = EpisodeLegacy(..., is_test_data=False)
test_item = RundownItemLegacy(..., episode=production_episode, is_test_data=True)  # Confusing!
```

### 3. Environment-Specific Defaults

Configure different defaults per environment:

```python
# config.py
class Config:
    # Production: exclude test data by default
    DEFAULT_EXCLUDE_TEST_DATA = True

class DevelopmentConfig(Config):
    # Development: include test data by default for testing
    DEFAULT_EXCLUDE_TEST_DATA = False
```

### 4. Test Data Lifecycle

- **Create**: Always flag new test data with `is_test_data=True`
- **Use**: Filter appropriately in production queries  
- **Maintain**: Regular cleanup of outdated test data
- **Archive**: Export test datasets for reuse across environments

## Migration Information

The test data system was added via migration `b3e162fbdbed_add_test_data_flags`:

- **Applied**: 2025-08-13
- **Tables Modified**: 11 content and system tables
- **Default Value**: `FALSE` (all existing data marked as production)
- **Rollback**: Supported via `alembic downgrade` if needed

## Troubleshooting

### Test Data Appearing in Production

```sql
-- Find test data that shouldn't be there
SELECT table_name, COUNT(*) as test_records
FROM (
    SELECT 'episodes_legacy' as table_name FROM episodes_legacy WHERE is_test_data = TRUE
    UNION ALL
    SELECT 'users' FROM users WHERE is_test_data = TRUE
    -- Add other tables as needed
) subq
GROUP BY table_name;
```

### Missing Test Data Flag

If you suspect data should be marked as test:

```sql
-- Find episodes with test-like characteristics
SELECT id, episode_number, title, is_test_data
FROM episodes_legacy 
WHERE (title ILIKE '%test%' OR episode_number LIKE '9%') 
  AND is_test_data = FALSE;

-- Update if confirmed as test data
UPDATE episodes_legacy 
SET is_test_data = TRUE 
WHERE episode_number IN ('9001', '9002', '9003');
```

### Performance Impact

The `is_test_data` field has minimal performance impact:

- Boolean fields are efficient to query
- Default index on `is_test_data` recommended for frequent filtering:

```sql
-- Add index for better query performance
CREATE INDEX idx_episodes_legacy_is_test_data ON episodes_legacy(is_test_data);
CREATE INDEX idx_users_is_test_data ON users(is_test_data);
```

## API Usage Examples

### REST Endpoints

```bash
# Get production episodes only (default)
GET /api/episodes

# Get all episodes including test data  
GET /api/episodes?include_test=true

# Get only test episodes
GET /api/episodes?test_only=true

# Get production rundown for episode
GET /api/episodes/123/rundown?exclude_test=true
```

### GraphQL Queries

```graphql
query GetEpisodes($excludeTest: Boolean = true) {
  episodes(where: {is_test_data: {_eq: $excludeTest}}) {
    id
    episode_number
    title
    is_test_data
    rundown_items(where: {is_test_data: {_eq: $excludeTest}}) {
      id
      title
      type
    }
  }
}
```

This test data management system provides clean separation between test and production data while maintaining full flexibility for development and testing workflows.