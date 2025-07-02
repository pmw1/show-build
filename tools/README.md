# Tools Directory

This directory contains Python utilities and scripts for the Show-Build project.

## Configuration Management

### `paths.py`
Central configuration module for all Python scripts in the project. This ensures consistent path handling and eliminates hardcoded paths throughout the codebase.

**Key Configurations:**
- `EPISODE_ROOT`: Path to episode data directory
- `BLUEPRINTS`: Path to template blueprints
- `HEADER_PATH`: Path to HTML header template
- `VALID_CUE_TYPES`: Allowed cue block types for validation

**Usage:**
```python
from paths import EPISODE_ROOT, BLUEPRINTS, HEADER_PATH, VALID_CUE_TYPES

# Use configured paths instead of hardcoded strings
episode_path = EPISODE_ROOT / episode_number
```

## Scripts

### `compile-script-dev.py`
Compiles episode markdown files into formatted HTML scripts for production.

**Features:**
- Validates cue blocks for completeness and correctness
- Generates formatted HTML output with proper styling
- Handles multiple cue types (FSQ, SOT, GFX)
- Supports validation-only mode

**Usage:**
```bash
# Compile episode 0225
python compile-script-dev.py 0225

# Validate only (no output file)
python compile-script-dev.py 0225 --validate
```

### `media_job_queue.py`
Handles media processing job queue management.

## Adding New Tools

When creating new Python scripts in this directory:

1. **Import from `paths.py`** for path configurations:
   ```python
   from paths import EPISODE_ROOT, BLUEPRINTS, VALID_CUE_TYPES
   ```

2. **Follow the established patterns** for error handling and output formatting

3. **Update this README** with documentation for your new tool

## Path Structure Expected

The tools expect this directory structure:
```
show-build/
├── tools/           # This directory
│   ├── paths.py     # Configuration module
│   └── blueprints/  # Template directory
│       └── printing/
│           └── script-cover.html
└── ../episodes/     # Episode data (up one level from show-build)
    └── {episode}/
        ├── info.md
        └── rundown/
            └── *.md
```

## Configuration Changes

If you need to change path configurations:

1. Edit `paths.py` only - don't hardcode paths in individual scripts
2. Test all dependent scripts after making changes
3. Update this documentation if adding new configuration options
