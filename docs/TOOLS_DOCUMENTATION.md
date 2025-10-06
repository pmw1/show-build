# Show-Build Tools Documentation

This document provides comprehensive documentation for all tools in the Show-Build tools suite located in `/mnt/process/show-build/tools/`.

## Overview

The Show-Build tools suite consists of Python utilities that support episode production, content management, and workflow automation. These tools integrate with the FastAPI backend and work directly with episode data structures.

## Tool Categories

### Duration and Time Management Tools

#### duration_calculator.py
**Purpose**: Calculate and update segment and episode durations based on content analysis.

**Features**:
- Analyzes speech content using configurable words-per-minute rates
- Processes SOT (Sound on Tape) cues with duration fields
- Calculates FSQ (Full Screen Quote) durations at 120 WPM
- Handles ADLIB cues with specified durations
- Supports timecode format with frames (HH:MM:SS:FF)
- Updates episode and segment frontmatter automatically

**Usage**:
```bash
# Calculate duration for a specific segment
python duration_calculator.py --segment=SEGMEEJ44L61P9LZV

# Calculate durations for entire episode
python duration_calculator.py --episode=0236
```

**Configuration**:
- Speech WPM: 140 (configurable via DurationSettings)
- FSQ WPM: 120 (matches Obsidian plugin)
- Frame rate: 30 fps for timecode conversion

**Supported Cue Types**:
- **SOT**: Uses duration field from cue block
- **FSQ**: Calculates from word count at 120 WPM
- **ADLIB**: Uses specified duration, supports combined format `[Type: ADLIB, Duration: 00:01:00]`

### Content Management Tools

#### order-from-file-pref.py
**Purpose**: Update segment order fields in frontmatter based on filename numeric prefixes.

**Features**:
- Extracts numeric prefixes from filenames (e.g., "10" from "10 News Roundup.md")
- Updates `order:` field in YAML frontmatter with quoted values
- Smart detection to skip files that already have correct order values
- Comprehensive logging of changes and skips
- Supports both positional and named arguments

**Usage**:
```bash
# Update order fields for episode 0236
python order-from-file-pref.py --episode=0236
python order-from-file-pref.py 0236

# View help and examples
python order-from-file-pref.py --help
```

**Output Example**:
```
✅ UPDATED: 10 News Roundup and Updates.md -> order: "10"
✅ UPDATED: 20 Biltong.md -> order: "20"
⏭️  SKIPPED: 30 Man Up.md (order already "30")
```

**Processing Logic**:
1. Scans all `.md` files in episode's rundown directory
2. Extracts numeric prefix using regex `^(\d+)`
3. Updates or adds `order: "XX"` in YAML frontmatter
4. Preserves existing frontmatter structure and formatting

### Quality Assurance Tools

#### fsq_duration_scanner.py
**Purpose**: Scan and fix FSQ cue blocks missing duration fields across all episodes.

**Features**:
- Scans all episodes for FSQ cue blocks
- Identifies missing duration fields
- Calculates correct durations using 120 WPM
- Automatically fixes missing duration fields
- Provides comprehensive reporting and statistics

**Usage**:
```bash
# Scan only and report status
python fsq_duration_scanner.py --scan

# List detailed information about missing durations
python fsq_duration_scanner.py --list-missing

# Fix all missing duration fields
python fsq_duration_scanner.py --fix

# Combined scan and fix
python fsq_duration_scanner.py --scan --fix
```

**Integration Points**:
- Uses same 120 WPM calculation as Obsidian cue manager plugin
- Ensures consistency between frontend and backend duration calculations
- Supports the standard FSQ cue block format with `<!-- Begin Cue -->` markers

## Tool Architecture

### Path Management
All tools use centralized path management through `core.paths.ShowBuildPaths`:
```python
from core.paths import ShowBuildPaths
path_manager = ShowBuildPaths()
EPISODES_ROOT = path_manager.episodes_root
```

**Fallback Path**: `/mnt/sync/disaffected/episodes`

### Error Handling
Tools implement consistent error handling patterns:
- Graceful fallbacks for missing dependencies
- Comprehensive logging with emoji indicators
- Exit codes: 0 (success), 1 (error), 130 (user cancellation)

### File Format Support
Tools work with Show-Build's standard file formats:
- **Episode Directories**: `/episodes/{episode_number}/`
- **Rundown Files**: `/episodes/{episode_number}/rundown/*.md`
- **YAML Frontmatter**: Standard Jekyll/Obsidian compatible format
- **Cue Blocks**: `<!-- Begin Cue -->` ... `<!-- End Cue -->` format

## Integration with Show-Build Ecosystem

### Frontend Integration
- **Obsidian Plugin**: FSQ duration calculations match cue manager plugin (120 WPM)
- **Vue Frontend**: Order fields enable proper rundown sorting and display
- **Duration Display**: Calculated durations appear in episode and segment views

### Backend Integration
- **FastAPI Endpoints**: Tools can be invoked via API endpoints
- **Database Sync**: Frontmatter updates sync with PostgreSQL via file watchers
- **AssetID System**: Tools respect and work with AssetID conventions

### Workflow Integration
Tools support typical production workflows:
1. **Content Creation**: Order fields maintain segment sequence
2. **Duration Planning**: Duration calculator provides accurate time estimates
3. **Quality Assurance**: FSQ scanner ensures consistent metadata
4. **Publishing**: All tools prepare content for broadcast/distribution

## Development Guidelines

### Adding New Tools
When creating new tools, follow these patterns:
1. Use centralized path management (`core.paths`)
2. Implement comprehensive argument parsing with help text
3. Provide detailed console output with progress indicators
4. Support both single-item and batch operations
5. Include error handling and validation
6. Document usage examples and integration points

### Testing Tools
Tools should be tested with:
- Valid episode numbers (e.g., 0236)
- Edge cases (missing files, malformed data)
- Large datasets (multiple episodes)
- Integration scenarios (concurrent access)

### Configuration Management
Tools use consistent configuration patterns:
- Environment variables for paths and settings
- Class-based settings objects (e.g., `DurationSettings`)
- Sensible defaults with override capabilities
- Documentation of all configurable parameters

## Troubleshooting

### Common Issues

**Path Not Found Errors**:
- Verify episodes directory exists at `/mnt/sync/disaffected/episodes`
- Check episode number format (4 digits, e.g., "0236")
- Ensure rundown subdirectory exists

**Permission Errors**:
- Verify write permissions to episode directories
- Check file locks from concurrent processes

**Duration Calculation Issues**:
- Verify cue block format matches expected structure
- Check for malformed timecode strings
- Ensure FSQ blocks have Quote fields for word counting

**Frontmatter Parsing Issues**:
- Verify YAML syntax in frontmatter
- Check for missing `---` delimiters
- Ensure proper field name formatting

### Debug Mode
Most tools support verbose output for troubleshooting:
```bash
# Enable detailed logging (when supported)
python tool_name.py --verbose --episode=0236
```

## Future Enhancements

### Planned Features
- **Batch Processing**: Multi-episode operations
- **Configuration Files**: Tool-specific settings files
- **API Integration**: Direct database updates via FastAPI
- **Validation Tools**: Content structure verification
- **Export Tools**: Format conversion and distribution support

### Integration Opportunities
- **GitHub Actions**: Automated tool execution on content changes
- **Database Triggers**: Real-time sync between files and database
- **Queue System**: Background processing for heavy operations
- **Monitoring**: Tool execution tracking and performance metrics

---

**Last Updated**: August 16, 2025  
**Tool Suite Version**: 1.0  
**Show-Build Compatibility**: v2.x+