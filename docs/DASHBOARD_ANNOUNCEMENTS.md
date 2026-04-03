# Dashboard Announcements Guide

This guide explains how to create and manage announcements that display on the Show-Build dashboard.

## Overview

The Show-Build dashboard includes an **Announcements Panel** that automatically displays HTML announcement files. Announcements appear in reverse chronological order (newest first) and can be clicked to view full content in a modal dialog.

## Creating Announcements

### File Naming Convention

Announcement files must follow this naming pattern:

```
YYYY-MM-DD-title-slug.html
```

**Examples:**
- `2025-11-22-modifications.html`
- `2025-12-01-new-feature.html`
- `2025-12-15-maintenance-notice.html`

**Components:**
- `YYYY-MM-DD`: Date in ISO format (year-month-day)
- `title-slug`: Lowercase, hyphen-separated title
- `.html`: File extension (must be HTML)

### File Location

Place announcement HTML files in:

```
/mnt/process/show-build/app/docs/announcements/
```

This directory is volume-mounted into the backend Docker container at `/app/docs/announcements/`.

### HTML Template

Use standard HTML with semantic markup:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Your Announcement Title</title>
</head>
<body>
    <h1>📋 Your Announcement Title</h1>

    <p>Introduction paragraph explaining the announcement.</p>

    <h2>Section Heading</h2>

    <ul>
        <li><strong>Feature Name:</strong> Description of the feature or change.</li>
        <li><strong>Another Feature:</strong> More details here.</li>
    </ul>

    <h2>Additional Information</h2>

    <p>More content here with <strong>bold text</strong> and <em>italic text</em>.</p>

    <hr>

    <p><em>Last updated: Month DD, YYYY</em></p>
</body>
</html>
```

## Supported HTML Elements

The announcement content renderer supports:

### Typography
- `<h1>`, `<h2>`, `<h3>` - Headings (automatically styled with primary color)
- `<p>` - Paragraphs
- `<strong>` - Bold text
- `<em>` - Italic text

### Lists
- `<ul>` - Unordered lists
- `<ol>` - Ordered lists
- `<li>` - List items

### Code
- `<code>` - Inline code snippets
- `<pre>` - Code blocks

### Other
- `<hr>` - Horizontal divider
- `<a href="">` - Links (external links work)

## How It Works

### Backend API

The announcements system uses two API endpoints:

1. **List announcements**: `GET /api/announcements/`
   - Returns array of announcements with metadata
   - Sorted by date (newest first)
   - Extracts title from filename slug

2. **Get announcement content**: `GET /api/announcements/{announcement_id}`
   - Returns full HTML content
   - `announcement_id` is the filename without `.html` extension

### Frontend Component

The `AnnouncementsPanel.vue` component:
- Fetches announcements on mount
- Displays list with titles and dates
- Opens modal when clicked
- Renders HTML content with proper styling

## Examples

### Simple Feature Announcement

**Filename:** `2025-11-25-new-export-feature.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>New Export Feature</title>
</head>
<body>
    <h1>🎉 New Export Feature Available</h1>

    <p>We've added a new export feature that allows you to export rundown items in multiple formats.</p>

    <h2>Supported Formats</h2>

    <ul>
        <li><strong>PDF:</strong> Print-ready rundown documents</li>
        <li><strong>JSON:</strong> Machine-readable data export</li>
        <li><strong>Markdown:</strong> Plain text format for editing</li>
    </ul>

    <h2>How to Use</h2>

    <p>Click the "Export" button in the rundown toolbar and select your desired format.</p>
</body>
</html>
```

### Maintenance Notice

**Filename:** `2025-12-01-scheduled-maintenance.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Scheduled Maintenance</title>
</head>
<body>
    <h1>⚠️ Scheduled Maintenance Notice</h1>

    <p>The Show-Build system will undergo scheduled maintenance on <strong>December 5, 2025</strong>.</p>

    <h2>Maintenance Window</h2>

    <ul>
        <li><strong>Start:</strong> December 5, 2025 at 2:00 AM EST</li>
        <li><strong>Duration:</strong> Approximately 2 hours</li>
        <li><strong>Impact:</strong> System will be unavailable during this time</li>
    </ul>

    <h2>What's Being Updated</h2>

    <ul>
        <li>Database performance optimizations</li>
        <li>Security patches</li>
        <li>Backend dependency updates</li>
    </ul>

    <p>Please save all work before the maintenance window begins.</p>
</body>
</html>
```

### Tips and Tricks

**Filename:** `2025-11-30-keyboard-shortcuts.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Keyboard Shortcuts</title>
</head>
<body>
    <h1>⌨️ Keyboard Shortcuts Guide</h1>

    <p>Speed up your workflow with these helpful keyboard shortcuts:</p>

    <h2>Content Editor</h2>

    <ul>
        <li><code>Ctrl + S</code> - Save current item</li>
        <li><code>Ctrl + B</code> - Bold text</li>
        <li><code>Ctrl + I</code> - Italic text</li>
        <li><code>Enter Enter</code> - Create new paragraph (cursor auto-positioned)</li>
    </ul>

    <h2>Rundown Manager</h2>

    <ul>
        <li><code>Ctrl + N</code> - New rundown item</li>
        <li><code>Drag & Drop</code> - Reorder items</li>
    </ul>
</body>
</html>
```

## Managing Announcements

### Adding New Announcements

1. Create HTML file with proper naming convention
2. Place in `/mnt/process/show-build/app/docs/announcements/`
3. File appears immediately (no restart needed)
4. Refresh dashboard to see new announcement

### Removing Announcements

Simply delete the HTML file from the announcements directory. The dashboard will update on next refresh.

### Editing Announcements

1. Edit the HTML file directly
2. Save changes
3. Refresh dashboard to see updates

## Troubleshooting

### Announcement Not Appearing

- **Check filename format**: Must match `YYYY-MM-DD-title-slug.html`
- **Check location**: Must be in `/mnt/process/show-build/app/docs/announcements/`
- **Check permissions**: File should be readable (644 or similar)
- **Refresh browser**: Hard refresh with Ctrl+Shift+R

### Content Not Displaying Correctly

- **Validate HTML**: Ensure HTML is well-formed
- **Check console**: Browser console may show rendering errors
- **Use supported elements**: Stick to basic HTML elements listed above

### API Endpoint Test

Test the announcements API directly:

```bash
# List all announcements
curl https://192.168.51.207:8888/api/announcements/ | python3 -m json.tool

# Get specific announcement content
curl https://192.168.51.207:8888/api/announcements/2025-11-22-modifications | python3 -m json.tool
```

## Related Files

- **Backend Router**: `/mnt/process/show-build/app/announcements_router.py`
- **Frontend Component**: `/mnt/process/show-build/disaffected-ui/src/components/AnnouncementsPanel.vue`
- **Announcements Directory**: `/mnt/process/show-build/app/docs/announcements/`

## Best Practices

1. **Use clear, descriptive titles** in filenames
2. **Keep content concise** - announcements should be scannable
3. **Use proper date format** - Always YYYY-MM-DD for sorting
4. **Include emojis sparingly** - One in the h1 heading is usually enough
5. **Test HTML rendering** - Preview content before deploying
6. **Archive old announcements** - Move to subdirectory or delete when no longer relevant
7. **Include update dates** - Add "Last updated" footer for clarity
