# Script Writing and Cue Insertion Architecture

## Overview
Scripts are written within rundown segments, and production cues (VO, NAT, PKG, GFX, FSQ, SOT) are inserted as specially formatted markers that can be parsed and rendered appropriately.

## Script Storage Structure

### 1. Segment-Based Script Storage
Each rundown segment file (`/episodes/0237/rundown/10 Opening.md`) contains:

```markdown
---
id: '0237001'
slug: opening
type: segment
order: 10
duration: 00:05:00
title: Opening
---

## Script

Welcome to episode 237 of Disaffected.

[VO: opening-music]
Today we're discussing the latest developments in...

[NAT: street-sounds :15]
The streets were busy as protesters gathered...

[SOT: interview-john-doe :45]

[GFX: lower-third "John Doe - Expert"]
According to our expert analysis...

[PKG: investigation-report 2:30]

[FSQ: full-screen-graphic-1]
As you can see from this data...
```

## Cue Format Specification

### Standard Cue Syntax
```
[CUE_TYPE: asset-id duration options]
```

### Cue Types and Their Formats

#### 1. **VO (Voice Over)**
```markdown
[VO: asset-id duration]
[VO: opening-narration :30]
```
- Audio plays while anchor continues reading
- Duration optional, defaults to full clip

#### 2. **NAT (Natural Sound)**
```markdown
[NAT: asset-id duration]
[NAT: crowd-ambience :10]
```
- Natural/ambient sound, usually under voice
- Often used for transitions

#### 3. **SOT (Sound on Tape)**
```markdown
[SOT: asset-id duration]
[SOT: interview-segment 1:15]
```
- Full audio/video segment
- Anchor stops, clip plays

#### 4. **PKG (Package)**
```markdown
[PKG: asset-id duration]
[PKG: reporter-package 3:00]
```
- Pre-produced segment/story
- Complete piece with its own script

#### 5. **GFX (Graphics)**
```markdown
[GFX: asset-id "display-text"]
[GFX: lower-third "John Doe - Title"]
[GFX: map-graphic]
```
- On-screen graphics
- Can include text overlays

#### 6. **FSQ (Full Screen Graphic)**
```markdown
[FSQ: asset-id duration]
[FSQ: chart-1 :20]
```
- Full screen graphic or video
- Replaces main video feed

## Implementation Architecture

### 1. **Writing Workflow**

#### Manual Insertion
Writers type cues directly in markdown:
```markdown
The president announced today...
[SOT: president-speech :45]
...that new policies would take effect.
```

#### Modal-Based Insertion
Using the existing modal system in ContentEditor:
1. User clicks cue button (VO, NAT, etc.)
2. Modal opens with fields:
   - Asset selection (dropdown or file picker)
   - Duration (timecode input)
   - Options (cue-specific fields)
3. Modal generates properly formatted cue
4. Inserts at cursor position

### 2. **Cue Storage Options**

#### Option A: Inline Storage (Recommended)
Cues stored as markdown text within script:
```markdown
## Script
Opening remarks here...
[VO: music-bed :30]
Main content continues...
```

**Pros:**
- Simple, readable, portable
- Works with any markdown editor
- Version control friendly
- No database required

**Cons:**
- Parsing required for rendering
- Less structured than database

#### Option B: Reference Storage
Cues stored separately with markers:
```markdown
## Script
Opening remarks here...
{{cue:1001}}
Main content continues...
```

```yaml
## Cues
- id: 1001
  type: VO
  asset: music-bed
  duration: 00:00:30
  position: 45  # character position in script
```

**Pros:**
- Structured data
- Easy to query all cues
- Can track cue relationships

**Cons:**
- More complex
- Requires synchronization
- Less portable

### 3. **Parsing and Rendering**

#### Parse Cues from Script
```javascript
function parseCues(scriptText) {
  const cuePattern = /\[(VO|NAT|SOT|PKG|GFX|FSQ):\s*([^\]]+)\]/g;
  const cues = [];
  let match;
  
  while ((match = cuePattern.exec(scriptText)) !== null) {
    const [fullMatch, type, params] = match;
    const parts = params.split(' ');
    
    cues.push({
      type,
      assetId: parts[0],
      duration: parts[1] || null,
      text: parts.slice(2).join(' '),
      position: match.index,
      raw: fullMatch
    });
  }
  
  return cues;
}
```

#### Render for Display
```javascript
function renderScriptWithCues(scriptText, cues) {
  let rendered = scriptText;
  
  cues.forEach(cue => {
    const cueHtml = `
      <div class="cue cue-${cue.type.toLowerCase()}">
        <span class="cue-type">${cue.type}</span>
        <span class="cue-asset">${cue.assetId}</span>
        ${cue.duration ? `<span class="cue-duration">${cue.duration}</span>` : ''}
      </div>
    `;
    
    rendered = rendered.replace(cue.raw, cueHtml);
  });
  
  return rendered;
}
```

### 4. **Integration with ContentEditor**

#### Current Modal System
The ContentEditor already has modals for each cue type:
- `VoModal.vue`
- `NatModal.vue`
- `PkgModal.vue`
- `GfxModal.vue`
- `FsqModal.vue`
- `SotModal.vue`

#### Enhanced Integration
1. **Asset Selection**: Link to AssetID system
2. **Duration Picker**: Timecode input component
3. **Preview**: Show/play selected asset
4. **Validation**: Ensure asset exists and is correct type

### 5. **Script Compilation with Cues**

When compiling the full script:

```javascript
async function compileScriptWithCues(episodeNumber) {
  const segments = await getRundownSegments(episodeNumber);
  const compiled = [];
  
  for (const segment of segments) {
    const script = segment.script;
    const cues = parseCues(script);
    
    // Enhance cues with asset metadata
    for (const cue of cues) {
      const asset = await getAssetMetadata(cue.assetId);
      cue.assetPath = asset.path;
      cue.assetTitle = asset.title;
    }
    
    compiled.push({
      segment: segment.title,
      script: script,
      cues: cues,
      rendered: renderScriptWithCues(script, cues)
    });
  }
  
  return compiled;
}
```

## Display and Export Formats

### 1. **Editor View** (Markdown with Visual Cues)
```markdown
Welcome to the show.
┌─ VO: opening-music [:30] ─┐
└────────────────────────────┘
Today's top story...
```

### 2. **Teleprompter View** (Clean Text)
```
Welcome to the show.
[[ PLAY VO - 30 SECONDS ]]
Today's top story...
```

### 3. **Production View** (Technical Script)
```
| TIME  | VIDEO        | AUDIO          | SCRIPT                |
|-------|--------------|----------------|-----------------------|
| 00:00 | CAM 1        | MIC 1          | Welcome to the show.  |
| 00:05 | CAM 1 + VO   | VO: music-bed  | Today's top story...  |
```

### 4. **Export Formats**
- **PDF**: Formatted script with cue boxes
- **DOCX**: Script with cue tables
- **HTML**: Interactive with cue playback
- **JSON**: Structured data for automation

## Benefits of This Approach

1. **Simplicity**: Cues are just formatted text
2. **Portability**: Works in any markdown editor
3. **Flexibility**: Easy to add new cue types
4. **Integration**: Works with existing modal system
5. **Version Control**: Git-friendly text format
6. **Searchability**: Can grep for specific cues
7. **Compatibility**: Maintains Obsidian compatibility

## Implementation Priority

### Phase 1: Basic Implementation
1. Define standard cue format
2. Implement cue parser
3. Add visual rendering in editor

### Phase 2: Modal Integration
1. Enhance existing modals with cue insertion
2. Add asset picker integration
3. Implement duration/timecode inputs

### Phase 3: Advanced Features
1. Cue validation and checking
2. Asset availability verification
3. Timeline view of all cues
4. Export to production formats

## Example Complete Segment

```markdown
---
id: '0237010'
slug: top-story
type: segment
order: 20
duration: 00:08:00
title: Top Story - Climate Protests
---

## Script

[GFX: headline-graphic "Climate Protests Intensify"]

Good evening. Our top story tonight: Climate protesters have gathered in major cities across the country.

[NAT: protest-chants :10]

The demonstrations, which began early this morning, have drawn thousands of participants.

[PKG: field-report 2:30]

[GFX: lower-third "Jane Smith - Field Reporter"]

For more on this story, we go now to our correspondent in the field.

[SOT: interview-organizer 1:15]

[FSQ: protest-map :20]

As you can see from this map, protests are happening simultaneously in over 50 cities.

[VO: closing-music :15]

We'll continue following this story throughout the evening.

## Notes
- Ensure B-roll is ready for PKG
- Verify SOT audio levels
- Have backup graphic ready
```

This architecture provides a clean, flexible way to write scripts with embedded production cues while maintaining simplicity and compatibility with your existing workflow.