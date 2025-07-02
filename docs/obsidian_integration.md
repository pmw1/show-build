# Obsidian Configuration for Show-Build Integration

## Current System
The Show-Build backend updates the `order:` field in YAML frontmatter when segments are reordered:

```yaml
---
title: "COLD OPEN"
slug: "cold-open"
asset_id: "abc123"
order: 10
---
```

## Obsidian Setup for Frontmatter Sorting

### Option 1: Dataview Plugin
Install the Dataview plugin and create a custom view:

```dataview
TABLE title, order, asset_id
FROM "episodes/0229/rundown"
SORT order ASC
```

Or create a list view:
```dataview
LIST
FROM "episodes/0229/rundown"  
SORT order ASC
```

### Option 2: File Tree Alternative Plugin
1. Install "File Tree Alternative" plugin
2. Configure to sort by frontmatter fields
3. Set `order` as the primary sort field

### Option 3: Custom CSS Snippet
Create a CSS snippet to visually indicate order:

```css
/* Show order number before filename in file explorer */
.nav-file-title::before {
  content: attr(data-order) " - ";
  color: #666;
  font-size: 0.8em;
}
```

### Option 4: Templater + QuickAdd
Create templates that auto-generate ordered indices:

```javascript
// Templater script to generate ordered rundown
const files = app.vault.getMarkdownFiles()
  .filter(f => f.path.includes('rundown'))
  .sort((a, b) => {
    const aOrder = app.metadataCache.getFileCache(a)?.frontmatter?.order || 999;
    const bOrder = app.metadataCache.getFileCache(b)?.frontmatter?.order || 999;
    return aOrder - bOrder;
  });

return files.map(f => `- [[${f.basename}]]`).join('\n');
```

## Recommended Workflow

1. **Primary**: Use Dataview plugin for ordered segment lists
2. **Backup**: Manual MOCs (Maps of Content) that reference segments in order
3. **Visual**: Custom CSS to show order indicators

## Example Dataview Queries

### Simple List
```dataview
LIST
FROM "episodes/0229/rundown"
SORT order ASC
```

### Detailed Table
```dataview
TABLE 
  title as "Title",
  order as "Order", 
  asset_id as "Asset ID",
  file.mtime as "Modified"
FROM "episodes/0229/rundown"
SORT order ASC
```

### Rundown Overview
```dataview
TABLE WITHOUT ID
  ("**" + title + "**") as "Segment",
  ("Order: " + order) as "Position"
FROM "episodes/0229/rundown"
SORT order ASC
```

This approach leverages Obsidian's powerful plugin ecosystem without requiring filename changes that could break references or complicate the backend.
