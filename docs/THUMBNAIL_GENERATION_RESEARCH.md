# Thumbnail Generation System - Research & Implementation Plan

**Status**: URGENT - Needs Decision & Implementation
**Conversation Context**: 2025-10-13 - Episode file structure standardization discussion
**Related To**: Episode Directory Standard - exports/ and thumbnails/ folders

---

## Requirements

### Platform-Specific Thumbnail Formats Needed

#### Video Platforms (16:9)
- **YouTube/Rumble**: 1280x720 pixels, under 2MB
- **High Quality**: 1920x1080 pixels

#### Podcast Platforms (1:1 Square)
- **Apple Podcasts/Spotify**: 3000x3000 pixels, under 500KB
- **Minimum Size**: 1400x1400 pixels

#### Social Media
- **Instagram/TikTok**: 1080x1920 (9:16 vertical)
- **Facebook**: 1080x1080 (square)

### Proposed Directory Structure

```
/mnt/sync/disaffected/episodes/{EPISODE}/
├── thumbnails/                          # Master artwork (source files)
│   ├── master-16x9.psd                 # Photoshop master for widescreen
│   ├── master-16x9.png                 # High-res 16:9 master (3840x2160)
│   ├── master-square.psd               # Photoshop master for square/podcast
│   └── master-square.png               # High-res 1:1 master (3000x3000)
│
└── exports/                             # Distribution-ready thumbnails
    ├── {EPISODE}-poster-16x9.png       # 1920x1080 (high-quality)
    ├── {EPISODE}-poster-16x9-web.png   # 1280x720 (YouTube/Rumble)
    ├── {EPISODE}-poster-square.png     # 3000x3000 (podcasts)
    ├── {EPISODE}-poster-square-small.png # 1400x1400 (podcast minimum)
    ├── {EPISODE}-poster-vertical.png   # 1080x1920 (Instagram/TikTok)
    └── {EPISODE}-poster-facebook.png   # 1080x1080 (Facebook)
```

---

## Python Library Research (2025-10-13)

### Option 1: psd-tools
**PyPI**: https://pypi.org/project/psd-tools/
**GitHub**: https://github.com/psd-tools/psd-tools

**Capabilities**:
- ✅ Read PSD files (layers, effects, text, smart objects)
- ✅ Extract layers to PNG
- ✅ Parse PSD structure
- ❌ **CANNOT CREATE or WRITE PSD files** (read-only)

**Status**: Actively maintained (last update Oct 2025)
**Python**: 3.9+

**Use Case**: Could extract layers from template PSDs, but cannot generate new PSDs

### Option 2: pytoshop
**GitHub**: https://github.com/mdboom/pytoshop

**Capabilities**:
- ✅ Read PSD/PSB files
- ✅ Write PSD/PSB files
- ✅ Create layered PSD files programmatically

**Status**: Less actively maintained
**Community**: Smaller than psd-tools

**Use Case**: Could potentially create PSDs from scratch

### Option 3: Aspose.PSD for Python
**Docs**: https://docs.aspose.com/psd/python-net/

**Capabilities**:
- ✅ Create PSD files from scratch
- ✅ Add layers, text, shapes, effects
- ✅ Full manipulation of PSD structure

**Drawback**: **Commercial/paid library**
**Pricing**: Unknown - needs investigation

---

## Initial Options Presented (Verbatim from Discussion)

### Option 1: **Template-Based System**
1. Create PSD templates with placeholders
2. Python extracts layers, modifies text/images
3. Re-saves PSD (using pytoshop)
4. Opens in Photoshop with updated content

### Option 2: **Generate PNG Layers, Assemble in Photoshop**
1. Python generates individual PNG layers programmatically
2. Use Photoshop scripting (JSX) to import and stack layers
3. Show-Build triggers Photoshop via command line

### Option 3: **Use Aspose.PSD (Commercial)**
- Full PSD creation capability
- Cost: Need to check pricing

### Option 4: **Export to Figma/Canva API Instead**
- Generate thumbnails via Figma/Canva APIs
- Export final images in all required formats
- Skip PSD entirely for automated generation

---

## Proposed Implementation Approaches (Detailed)

### Approach A: Template-Based PSD Modification
**How it works**:
1. Create master PSD templates with placeholder layers
2. Python script uses `pytoshop` to:
   - Load template PSD
   - Replace text layers (episode number, title, date)
   - Replace image layers (show logo, guest photos, etc.)
   - Save modified PSD
3. Export all required formats from modified PSD

**Pros**:
- Consistent branding
- Designer controls look in Photoshop
- Reusable templates

**Cons**:
- Requires pytoshop (less maintained)
- Limited to template structure
- Text/layer replacement may be complex

### Approach B: PNG Layer Generation + Photoshop Scripting
**How it works**:
1. Python generates individual PNG layers:
   - Background layer
   - Text layers (rendered with Pillow)
   - Logo/graphic layers
   - Photo layers
2. Photoshop JSX script (ExtendScript) imports layers
3. Script stacks layers into PSD with effects
4. Exports all required formats

**Pros**:
- Python does what it's good at (image generation)
- Photoshop does what it's good at (compositing/effects)
- Full control over final PSD

**Cons**:
- Requires Photoshop installed on server
- Cross-platform complexity (Windows/Mac/Linux)
- Licensing issues for server Photoshop

### Approach C: Skip PSD - Use Figma/Canva API
**How it works**:
1. Design templates in Figma or Canva
2. Python calls Figma/Canva API with episode data
3. API generates thumbnails in all required formats
4. Download and save to exports/

**Pros**:
- Cloud-based, no local Photoshop needed
- APIs designed for automation
- Built-in export in multiple formats

**Cons**:
- Requires API subscription (cost)
- Dependency on external service
- Less control than local generation

### Approach D: Pure Python Image Generation (No PSD)
**How it works**:
1. Design thumbnail layouts in code using Pillow/PIL
2. Generate all formats directly as PNG/JPG
3. Skip PSD entirely - work with high-res PNG masters

**Pros**:
- No external dependencies
- Fast, automated
- Easy to version control (code-defined layouts)

**Cons**:
- No PSD for manual editing
- Designers can't tweak in Photoshop
- Complex layouts harder to code

### Approach E: Hybrid - Generate PNG Masters, Manual PSD Creation
**How it works**:
1. Show-Build generates basic PNG thumbnails (text + layout)
2. Designers optionally import into Photoshop for enhancement
3. Save PSD in `thumbnails/` folder for future reference
4. Export system generates all required formats from PSD or PNG

**Pros**:
- Automated default thumbnails
- Optional manual enhancement
- Flexible workflow

**Cons**:
- Two-step process
- Inconsistent results (some auto, some manual)

---

## Decision Points

### 1. PSD Requirement
**Question**: Is PSD a hard requirement, or is high-res PNG master acceptable?
- If PSD required: Approaches A, B, or E
- If PNG acceptable: Approach D or E

### 2. Automation Level
**Question**: Fully automated or semi-automated (with designer input)?
- Fully automated: Approach A or D
- Semi-automated: Approach B or E
- Cloud-based: Approach C

### 3. Infrastructure
**Question**: What software can we install on the server?
- Photoshop available: Approach B
- Python only: Approach A, D, or E
- Cloud API access: Approach C

### 4. Budget
**Question**: Budget for commercial tools?
- Aspose.PSD license: $$$ (unknown cost)
- Figma/Canva API: $$ (subscription)
- Free open-source only: Approaches A, B, D, or E

---

## Recommended Next Steps

1. **Define hard requirements**:
   - Must PSD files be generated, or are PNG masters OK?
   - Fully automated or designer-assisted workflow?

2. **Test pytoshop library**:
   - Can it reliably create/modify PSDs?
   - Performance with template-based approach?

3. **Prototype simple thumbnail generator**:
   - Use Pillow to create basic 16:9 and 1:1 thumbnails
   - Test export to all required formats
   - Verify file sizes and quality

4. **Evaluate Figma API**:
   - Check pricing and capabilities
   - Test integration with Show-Build

5. **Decide on approach and implement**

---

## Implementation Priority

**URGENT** - This blocks the canonical file structure specification and episode consolidation workflow.

**Timeline**:
- Decision on approach: Within 1 week
- Prototype implementation: 2 weeks
- Full integration: 1 month

---

## Related Documentation

- Episode Directory Standard: `/docs/EPISODE_DIRECTORY_STANDARD.md` (when created)
- Platform thumbnail requirements: See research above
- Export automation: TBD

---

## Notes from Discussion

- User wants PSD support for manual editing capability
- Different aspect ratios (16:9, 1:1) need different master compositions
- File size constraints are critical (2MB for video platforms, 500KB for podcasts)
- Current workflow is manual - automation would save significant time

**Key Quote**: "I am going to be looking at adding features to show build to assist in the creation of thumbnails. We should stick with PSD for now. But can we code some modules for show build to help create PSD files?"

---

**END OF RESEARCH DOCUMENT**
