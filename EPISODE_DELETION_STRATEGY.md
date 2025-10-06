# Episode Deletion Strategy & Design Analysis

## 🚨 Critical Design Flaw Identified

### The Problem
The `episode_templates` table is being **misused** to store specific episodes (0001, 0238, 0239) rather than reusable templates. This creates confusion and breaks the intended template system.

### Current Flawed Architecture
```
BlueprintTemplate (✅ Correct)
├── "Sunday Show Template" 
├── "Interview Template"
└── "Breaking News Template"

EpisodeTemplate (❌ WRONG - storing episodes, not templates)
├── Episode 0001 
├── Episode 0238
└── Episode 0239
```

### Intended Architecture
```
BlueprintTemplate (✅ Templates)
├── "Sunday Show Template"
├── "Interview Template" 
└── "Breaking News Template"

Episodes (✅ Actual episodes)
├── Episode 0001 (created from Sunday Show Template)
├── Episode 0238 (created from Interview Template)
└── Episode 0239 (created from Sunday Show Template)
```

### Root Cause Analysis
**File: `/app/services/episode_scaffold.py:280`**
```python
# WRONG: Creating episode-specific records in "templates" table
episode = EpisodeTemplate(
    episode_number=episode_number,  # ← This should not exist in templates!
    title=request.title,
    ...
)
```

**Model Comment Contradiction:**
- Line 49: `"""Episodes created through scaffolding"""`
- Table name: `episode_templates`

This indicates the table was intended for episodes but incorrectly named as "templates".

---

## 🗑️ Comprehensive Episode Deletion Strategy

### Phase 1: Database Analysis & Mapping

**Tables with Episode References:**
1. `episodes` (models_v2) - Main episode records ✅
2. `episode_templates` (models_episode) - **MISNAMED** - Actually stores episodes ❌
3. `episodes_legacy` (models) - Legacy episode format ✅
4. `rundowns` - Episode rundowns (via episode_id FK) ✅
5. `rundown_items` - Items within rundowns (via rundown_id FK) ✅
6. `rundown_items_legacy` - Legacy rundown items (via episode_id FK) ✅
7. `segments` - Episode segments (via episode_id FK) ✅
8. `breaks` - Episode breaks (via episode_id FK) ✅
9. `assets` - Episode assets (via episode_id FK) ✅
10. `processing_jobs` - Episode processing (via episode_id FK) ✅
11. `extracted_quotes` - Episode quotes (via episode_id FK) ✅

### Phase 2: Deletion Order (Respecting Foreign Key Constraints)

```sql
-- Step 1: Delete leaf records (no dependencies)
DELETE FROM rundown_items WHERE rundown_id IN (
    SELECT id FROM rundowns WHERE episode_id IN (
        SELECT id FROM episodes WHERE episode_number = ?
    )
);

DELETE FROM extracted_quotes WHERE episode_id IN (
    SELECT id FROM episodes WHERE episode_number = ?
);

DELETE FROM processing_jobs WHERE episode_id IN (
    SELECT id FROM episodes WHERE episode_number = ?
);

DELETE FROM segments WHERE episode_id IN (
    SELECT id FROM episodes WHERE episode_number = ?
);

DELETE FROM breaks WHERE episode_id IN (
    SELECT id FROM episodes WHERE episode_number = ?
);

DELETE FROM assets WHERE episode_id IN (
    SELECT id FROM episodes WHERE episode_number = ?
);

DELETE FROM rundown_items_legacy WHERE episode_id IN (
    SELECT id FROM episodes WHERE episode_number = ?
);

-- Step 2: Delete rundowns (after rundown_items are gone)
DELETE FROM rundowns WHERE episode_id IN (
    SELECT id FROM episodes WHERE episode_number = ?
);

-- Step 3: Delete episode records from all episode tables
DELETE FROM episode_templates WHERE episode_number = ?;  -- MISNAMED TABLE
DELETE FROM episodes_legacy WHERE episode_number = ?;
DELETE FROM episodes WHERE episode_number = ?;
```

### Phase 3: Filesystem Cleanup

```bash
# Container paths
docker exec show-build-server rm -rf /home/episodes/{episode_number}

# Host paths  
rm -rf /mnt/sync/disaffected/episodes/{episode_number}

# Backup locations (if any)
rm -rf /path/to/backups/episodes/{episode_number}
```

### Phase 4: Cache & Service Cleanup

```bash
# Clear any cached data
redis-cli DEL "episode:{episode_number}:*"

# Restart services to clear memory cache
docker restart show-build-server show-build-frontend
```

---

## 🔧 Recommended Design Fixes

### Fix 1: Rename Table & Model
```sql
-- Rename table to reflect actual purpose
ALTER TABLE episode_templates RENAME TO scaffold_episodes;

-- Update model name in code
class ScaffoldEpisode(Base):  -- was EpisodeTemplate
    """Episodes created through scaffolding system"""
    __tablename__ = "scaffold_episodes"  -- was episode_templates
```

### Fix 2: Proper Template System
```python
# Templates should be reusable
class BlueprintTemplate(Base):
    """Reusable templates for creating episodes"""
    name: str  # "Sunday Show Template"
    template_type: str  # "weekly", "interview", "breaking"
    # No episode_number field!

# Episodes should reference templates
class Episode(Base):
    """Actual episodes created from templates"""
    episode_number: str  # "0239"
    template_id: ForeignKey  # References BlueprintTemplate
    title: str  # "The Princess and the Pea"
```

### Fix 3: Cascade Delete Constraints
```sql
-- Add proper cascade deletes
ALTER TABLE rundowns 
ADD CONSTRAINT fk_rundowns_episode 
FOREIGN KEY (episode_id) REFERENCES episodes(id) 
ON DELETE CASCADE;

ALTER TABLE assets 
ADD CONSTRAINT fk_assets_episode 
FOREIGN KEY (episode_id) REFERENCES episodes(id) 
ON DELETE CASCADE;

-- Apply to all episode-dependent tables
```

---

## 🛠️ Complete Deletion Script

### SQL Script: `delete_episode.sql`
```sql
-- Complete episode deletion with transaction safety
BEGIN;

-- Log the deletion attempt
INSERT INTO deletion_log (episode_number, deleted_at, status) 
VALUES (?, NOW(), 'started');

-- Delete in dependency order
DELETE FROM rundown_items WHERE rundown_id IN (
    SELECT id FROM rundowns WHERE episode_id IN (
        SELECT id FROM episodes WHERE episode_number = ?
    )
);

DELETE FROM extracted_quotes WHERE episode_id IN (
    SELECT id FROM episodes WHERE episode_number = ?
);

DELETE FROM processing_jobs WHERE episode_id IN (
    SELECT id FROM episodes WHERE episode_number = ?
);

DELETE FROM segments WHERE episode_id IN (
    SELECT id FROM episodes WHERE episode_number = ?
);

DELETE FROM breaks WHERE episode_id IN (
    SELECT id FROM episodes WHERE episode_number = ?
);

DELETE FROM assets WHERE episode_id IN (
    SELECT id FROM episodes WHERE episode_number = ?
);

DELETE FROM rundown_items_legacy WHERE episode_id IN (
    SELECT id FROM episodes WHERE episode_number = ?
);

DELETE FROM rundowns WHERE episode_id IN (
    SELECT id FROM episodes WHERE episode_number = ?
);

-- Delete from all episode tables
DELETE FROM episode_templates WHERE episode_number = ?;
DELETE FROM episodes_legacy WHERE episode_number = ?;
DELETE FROM episodes WHERE episode_number = ?;

-- Log successful completion
UPDATE deletion_log SET status = 'completed' WHERE episode_number = ?;

COMMIT;
```

### Bash Script: `delete_episode.sh`
```bash
#!/bin/bash
set -e

EPISODE_NUMBER=$1

if [ -z "$EPISODE_NUMBER" ]; then
    echo "Usage: $0 <episode_number>"
    exit 1
fi

echo "🗑️  Deleting episode $EPISODE_NUMBER completely..."

# Database deletion
echo "📊 Deleting database records..."
docker exec show-build-postgres psql -U showbuild -d showbuild -f delete_episode.sql -v episode_number="'$EPISODE_NUMBER'"

# Filesystem deletion
echo "📁 Deleting filesystem data..."
docker exec show-build-server rm -rf /home/episodes/$EPISODE_NUMBER
rm -rf /mnt/sync/disaffected/episodes/$EPISODE_NUMBER

# Cache cleanup
echo "🗄️  Clearing cache..."
docker exec show-build-redis redis-cli DEL "episode:$EPISODE_NUMBER:*" 2>/dev/null || true

# Service restart
echo "🔄 Restarting services..."
docker restart show-build-server show-build-frontend

echo "✅ Episode $EPISODE_NUMBER deleted successfully!"
```

---

## 📋 Verification Checklist

After deletion, verify no traces remain:

```sql
-- Database verification
SELECT COUNT(*) FROM episodes WHERE episode_number = '?';  -- Should be 0
SELECT COUNT(*) FROM episode_templates WHERE episode_number = '?';  -- Should be 0  
SELECT COUNT(*) FROM episodes_legacy WHERE episode_number = '?';  -- Should be 0
SELECT COUNT(*) FROM rundowns WHERE episode_id IN (SELECT id FROM episodes WHERE episode_number = '?');  -- Should be 0
```

```bash
# Filesystem verification
ls -la /home/episodes/ | grep {episode_number}  # Should be empty
ls -la /mnt/sync/disaffected/episodes/ | grep {episode_number}  # Should be empty
```

---

## 🎯 Priority Actions

1. **Immediate**: Implement complete deletion script for current episodes
2. **Short-term**: Fix the `episode_templates` naming/design confusion
3. **Long-term**: Add proper CASCADE delete constraints
4. **Architecture**: Separate templates from episodes properly

---

**Last Updated**: 2025-09-06  
**Issue Severity**: Critical - Affects episode creation/deletion workflows  
**Estimated Fix Time**: 2-4 hours for complete implementation