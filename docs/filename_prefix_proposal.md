# Filename Prefix Proposal for Obsidian Compatibility

## Current State
- ✅ Backend updates `order:` field in YAML frontmatter (10, 20, 30, etc.)
- ✅ File permissions fixed (Docker runs as `kevin:disaffected`)
- ✅ Rundown reordering works end-to-end

## Problem
Obsidian's default file browser sorts alphabetically by filename, ignoring frontmatter. This means:
- `BILTONG.md` comes before `COLD OPEN.md` alphabetically
- But `COLD OPEN.md` might have `order: 10` and `BILTONG.md` might have `order: 20`
- Users need plugins to sort by frontmatter `order:` field

## Proposed Solution
Add **optional** filename prefixing alongside the existing frontmatter approach:

### Option A: Zero-Padded Numbers
```
10 BILTONG.md
20 COLD OPEN.md  
30 INTERVIEW.md
```

### Option B: Letter Prefixes
```
A BILTONG.md
B COLD OPEN.md
C INTERVIEW.md
```

## Implementation Plan

### 1. Backend API Enhancement
Add optional `rename_files` parameter to reorder endpoint:
```python
@app.post("/rundown/{episode_number}/reorder")
async def reorder_rundown(
    episode_number: str, 
    segments: List[dict],
    rename_files: bool = False  # New optional parameter
):
```

### 2. Renaming Logic
When `rename_files=True`:
1. Update frontmatter `order:` field (current behavior)
2. Rename files with order prefix
3. Update any internal references/links
4. Return mapping of old → new filenames

### 3. Reference Updates
Scan for and update:
- Internal markdown links: `[[OLD_NAME]]` → `[[NEW_NAME]]`
- Asset references in other files
- Any hardcoded filename references

### 4. Frontend Options
Add toggle in RundownManager:
```vue
<v-switch
  v-model="renameFiles"
  label="Rename files with order prefixes (for Obsidian)"
  density="compact"
/>
```

## Pros & Cons

### Pros
- ✅ Perfect Obsidian compatibility (sorts correctly by default)
- ✅ Visual order when browsing files directly
- ✅ Optional feature (doesn't break existing workflows)
- ✅ Still maintains frontmatter approach as primary

### Cons
- ❌ File renaming can break external references
- ❌ More complex implementation
- ❌ Potential for filename conflicts
- ❌ Makes file history harder to track

## Recommendation

**Phase 1**: Keep current frontmatter-only approach as default
- Document how to configure Obsidian plugins for frontmatter sorting
- Test current system thoroughly

**Phase 2** (if needed): Implement optional filename prefixing
- Add as opt-in feature for users who prefer filename-based sorting
- Provide clear warnings about potential reference breaking

## Alternative: Obsidian Configuration

Instead of filename prefixing, provide clear documentation on configuring Obsidian:

1. **Dataview Plugin**: Sort by frontmatter fields
2. **Templater**: Auto-generate ordered views
3. **Custom CSS**: Style files based on frontmatter

This might be simpler and less disruptive than implementing filename renaming.
