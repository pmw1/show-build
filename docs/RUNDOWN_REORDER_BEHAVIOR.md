# Rundown Reorder Behavior Documentation

## Current Behavior (As of now)

When you drag and drop items in the Content Editor rundown:

1. **Frontend** (`ContentEditor.vue`):
   - Updates the visual order in the UI
   - Calls `saveRundownOrder()` which sends a POST to `/api/rundown/{episode}/reorder`
   - Sends the current filenames and new order values

2. **Backend** (`main.py` - `reorder_rundown` function):
   - **ONLY updates the `order:` field** in the YAML frontmatter
   - **DOES NOT rename files**
   - Files keep their original names

### Example:
Before reordering:
```
/episodes/0123/rundown/
  10 intro.md          (order: 10)
  20 main-segment.md   (order: 20)
  30 closing.md        (order: 30)
```

After dragging "closing" to the top:
```
/episodes/0123/rundown/
  10 intro.md          (order: 20)  ← File name unchanged, order updated
  20 main-segment.md   (order: 30)  ← File name unchanged, order updated
  30 closing.md        (order: 10)  ← File name unchanged, order updated
```

**Problem**: The file names (10, 20, 30) no longer match the actual order in the frontmatter!

## Enhanced Behavior (Proposed)

The enhanced version (`enhanced_reorder.py`) would:

1. **Update the `order:` field** in YAML frontmatter
2. **ALSO rename the files** to match the new order
3. Preserve the slug portion of the filename

### Example:
Before reordering:
```
/episodes/0123/rundown/
  10 intro.md          (order: 10)
  20 main-segment.md   (order: 20)
  30 closing.md        (order: 30)
```

After dragging "closing" to the top:
```
/episodes/0123/rundown/
  10 closing.md        (order: 10)  ← File renamed, order matches
  20 intro.md          (order: 20)  ← File renamed, order matches
  30 main-segment.md   (order: 30)  ← File renamed, order matches
```

## Benefits of Enhanced Approach

1. **File system consistency**: File names always match the actual order
2. **Better for manual editing**: When browsing files in the filesystem, they appear in the correct order
3. **Clearer for debugging**: No confusion about which order is "real"
4. **Git-friendly**: Changes are more obvious in version control

## Implementation Status

- ✅ Current basic reorder (updates frontmatter only) is **WORKING**
- 📝 Enhanced reorder with file renaming is **AVAILABLE** in `enhanced_reorder.py`
- ⚠️ Enhanced version is **NOT YET INTEGRATED** into main.py

## How to Enable Enhanced Reordering

To enable file renaming on reorder:

1. Import the enhanced function in `main.py`:
```python
from enhanced_reorder import reorder_rundown_with_rename
```

2. Replace the existing `reorder_rundown` function with:
```python
@app.post("/rundown/{episode_number}/reorder")
async def reorder_rundown(episode_number: str, payload: ReorderRequest):
    return await reorder_rundown_with_rename(episode_number, payload.dict())
```

## Considerations

### Pros of File Renaming:
- Maintains consistency between filename and order
- Better for manual file system navigation
- Clearer git history

### Cons of File Renaming:
- More disk I/O operations
- Potential for conflicts if files are being edited elsewhere
- Slightly more complex error handling
- May break external references to specific filenames

## Recommendation

For a production system where the rundown order changes frequently and multiple people work with the files, the enhanced approach with file renaming is recommended for maintaining consistency and clarity.