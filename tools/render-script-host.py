#!/usr/bin/env python3
"""
Host Script Renderer - Show-Build Edition

Renders episode markdown files into formatted HTML scripts for host reading.
Uses Show-Build centralized path configuration for maintainability.

This is a ported and refactored version of the original render-script-host.py
from the disaffected tools directory, adapted to use Show-Build path management.

Usage:
    python render-script-host.py <episode_number> [--validate]
    python render-script-host.py <episode_number> --status-list
    python render-script-host.py <episode_number> --rules

Examples:
    python render-script-host.py 0236              # Render episode 0236
    python render-script-host.py 0236 --validate   # Validate only, no output
    python render-script-host.py 0236 --status-list # Show all file statuses

Path Configuration:
    All paths are imported from paths.py to ensure consistency across tools.
    Episodes are located at: {PROJECT_ROOT}/episodes (not /mnt/sync/disaffected/episodes)
"""

import os
import sys
import argparse
from pathlib import Path
import re
from datetime import datetime, date
import yaml
import html

# Add tools directory to Python path for imports
tools_dir = Path(__file__).parent
sys.path.insert(0, str(tools_dir))

# Import Show-Build project paths
from paths import EPISODE_ROOT, BLUEPRINTS, HEADER_PATH, VALID_CUE_TYPES

__version__ = "2.0.0-showbuild"

def load_media_list_mapping(episode_path):
    """Load mapping from slug to enumerated prefix from media-list.txt"""
    media_list_path = episode_path / "rundown" / "media-list.txt"
    slug_to_enumerated = {}
    
    if not media_list_path.exists():
        print(f"\033[33mWARNING: media-list.txt not found at {media_list_path}\033[0m")
        return slug_to_enumerated
    
    try:
        with open(media_list_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Extract the enumerated prefix and original filename
                # Format: {order}_{counter:02d}_{original_filename}
                match = re.match(r'^(\d+)_(\d{2})_(.+)$', line)
                if match:
                    enumerated_number = match.group(1)  # Just the number like "010"
                    original_filename = match.group(3)
                    
                    # Extract slug from filename (remove extension)
                    slug = Path(original_filename).stem.lower()
                    slug_to_enumerated[slug] = enumerated_number
                    
                    print(f"\033[35mDEBUG: Mapped slug '{slug}' -> '{enumerated_number}'\033[0m")
    except Exception as e:
        print(f"\033[31mERROR: Failed to read media-list.txt: {e}\033[0m")
    
    print(f"\033[36mLoaded {len(slug_to_enumerated)} media mappings from media-list.txt\033[0m")
    return slug_to_enumerated

def get_ordinal_day(day):
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return f"{day}{suffix}"

def parse_yaml_frontmatter(content):
    match = re.match(r'^---\s*$(.*?)^---\s*$', content, re.DOTALL | re.MULTILINE)
    if match:
        try:
            return yaml.safe_load(match.group(1))
        except yaml.YAMLError as e:
            print(f"\033[31mERROR: Invalid YAML frontmatter: {e}\033[0m")
            print(f"\033[33mTip: Check for missing spaces after colons (e.g., 'key: value' not 'key:value')\033[0m")
            return {}
    return {}

def display_rules():
    """Display all validation rules in human-readable format"""
    print("\033[36m" + "="*80 + "\033[0m")
    print("\033[36mVALIDATION RULES FOR HOST SCRIPT RENDERING (Show-Build Edition)\033[0m")
    print("\033[36m" + "="*80 + "\033[0m")
    
    print(f"\n\033[35mPATH CONFIGURATION:\033[0m")
    print(f"   Episodes Root: {EPISODE_ROOT}")
    print(f"   Header Template: {HEADER_PATH}")
    print(f"   Valid Cue Types: {', '.join(VALID_CUE_TYPES)}")
    
    print("\n\033[33m1. FRONTMATTER FIELD REQUIREMENTS:\033[0m")
    print("   \033[32mREQUIRED FIELDS (all content types):\033[0m")
    print("     • id: Unique identifier (e.g., 'segment_20250720_001')")
    print("     • status: Must be 'production' for inclusion in output")
    print("     • order: Numeric value for sorting (e.g., '10', '20', '30')")
    print("     • slug: Short identifier (auto-generated from filename if missing)")
    print("   \033[32mOPTIONAL FIELDS:\033[0m")
    print("     • type: Content type descriptor")
    print("     • duration: Length of segment")
    print("     • title: Human-readable title")
    print("     • airdate: When content airs")
    print("     • priority: Processing priority")
    print("     • guests: Guest information")
    print("     • resources: Additional resources")
    print("     • tags: Content tags")
    print("     • server_message: Server-specific messages")
    
    print("\n\033[33m2. SEGMENT INCLUSION RULES:\033[0m")
    print("   • Only segments with status: 'production' are included in final output")
    print("   • Segments with empty status ('') are EXCLUDED and flagged in red")
    print("   • Segments with any other status (e.g., 'final', 'draft') are EXCLUDED and flagged in red")
    print("   • Files that cannot be read are EXCLUDED and flagged as errors")
    
    print("\n\033[33m3. ORDER FIELD RULES:\033[0m")
    print("   • Segments are sorted EXCLUSIVELY by the 'order' field in frontmatter")
    print("   • Order field must be numeric (e.g., '10', '20', '30')")
    print("   • Segments with missing order field are assigned '9999' and sorted last")
    print("   • Duplicate order values are FORBIDDEN - validation will fail")
    print("   • Order field should match filename prefix (e.g., '10 File.md' should have order: '10')")
    
    print("\n\033[33m4. FILENAME vs ORDER VALIDATION:\033[0m")
    print("   • If filename starts with number (e.g., '10 File.md') but order field differs, WARNING issued")
    print("   • If filename has numeric prefix but no order field, WARNING issued")
    print("   • If order field exists but filename has no numeric prefix, WARNING issued")
    
    print("\n\033[33m5. CUE BLOCK VALIDATION RULES:\033[0m")
    print("   • All cue blocks must have proper structure: <!-- Begin Cue --> ... <!-- End Cue -->")
    print("   • Required fields for ALL cue types:")
    print("     - [Type: XXX] - must be one of: 'GFX', 'SOT', 'FSQ', 'ADLIB'")
    print("     - [Slug: xxx] - cannot be empty (except ADLIB cues)")
    print("     - [AssetID: xxx] - for identification (except inline ADLIB cues)")
    print("   • Type-specific requirements:")
    print("     - GFX: Must have [MediaURL: xxx] (cannot be empty)")
    print("     - FSQ: Must have [Quote: xxx] (cannot be empty)")
    print("     - SOT: Optional [Duration: xxx] and [Transcription: xxx]")
    print("     - ADLIB: Can use inline format [Type: ADLIB, Duration: 00:01:00] (no slug/AssetID needed)")
    print("       Displays '[AD LIB] {duration}' in bold 1.5em font")
    print("   • Optional fields for all types:")
    print("     - [Attribution: xxx] - source attribution")
    print("   • All cue blocks must have proper closing tag: <!-- End Cue -->")
    
    print("\n\033[33m6. CONTENT PROCESSING RULES:\033[0m")
    print("   • Segments must have either content OR a slug (cannot be completely empty)")
    print("   • YAML frontmatter sections (between ---) are removed from content")
    print("   • ## Notes and ## Description sections are automatically removed")
    print("   • MediaURL lines and <img> tags in paragraphs are filtered out")
    print("   • Duplicate cues (same AssetID + Slug combination) are automatically deduplicated")
    print("   • Duplicate SOT references (same slug) are automatically deduplicated")
    print("   • Percentage signs (%) in content are auto-escaped to %% for safety")
    
    print("\n\033[33m7. FILE STRUCTURE REQUIREMENTS (Show-Build):\033[0m")
    print(f"   • Episode folder must exist: {EPISODE_ROOT}/<episode_number>/")
    print(f"   • Rundown folder must exist: {EPISODE_ROOT}/<episode_number>/rundown/")
    print("   • Only .md files in rundown folder are processed")
    print("   • info.md file should exist for episode metadata (optional but recommended)")
    print(f"   • Output directory created automatically: {EPISODE_ROOT}/<episode_number>/exports/")
    
    print("\n\033[33m8. SORTING AND OUTPUT RULES:\033[0m")
    print("   • Final sorting is by order field (numeric), then filename (alphabetic tiebreaker)")
    print("   • Files with same order value use filename for stable, predictable ordering")
    print("   • Output filename format: script-MM-DD-YY-production-N.html")
    print("   • Version number auto-increments if file already exists")
    
    print("\n\033[31m9. VALIDATION FAILURE CONDITIONS (COMPILATION ABORTS):\033[0m")
    print("   • Malformed cue blocks: Use <!-- Begin Cue --> not <<!-- Begin Cue -->>")
    print("   • Missing End Cue tags: Every Begin Cue must have matching End Cue")
    print("   • Extra angle brackets in HTML comments will prevent cue recognition")
    print("   • Incorrect field formatting: [Type: GFX] not [Type:GFX] (space after colon)")
    print("   • Duplicate order field values across segments")
    print("   • Invalid cue block structure (missing Begin/End tags)")
    print("   • Missing required cue fields (Type, Slug, AssetID)")
    print("   • Empty required cue fields (MediaURL for GFX, Quote for FSQ)")
    print("   • Invalid cue Type (not GFX, SOT, or FSQ)")
    print("   • File read errors (encoding, permissions, etc.)")
    print("   • No segments with status: 'production' found")
    
    print("\n\033[33m10. NON-BLOCKING WARNINGS:\033[0m")
    print("   • Order field vs filename prefix mismatch")
    print("   • Missing order field with numeric filename prefix")
    print("   • Order field present but no numeric filename prefix")
    print("   • Empty content after frontmatter removal")
    print("   • Percentage signs in content (auto-corrected)")
    print("   • Missing optional cue fields (Duration, Transcription)")
    
    print("\n\033[32m11. SPECIAL CONTENT HANDLING:\033[0m")
    print("   • SOT references: {SOT/slug-name} are converted to cue blocks")
    print("   • HTML escaping applied to paragraph content for safety")
    print("   • Line breaks (\\n) converted to <br> tags in paragraphs")
    print("   • Content split into paragraphs on double line breaks")
    
    print("\n\033[36m" + "="*80 + "\033[0m")
    print("\033[36mUSAGE:\033[0m")
    print("\033[36m  --validate    Check rules without generating output\033[0m")
    print("\033[36m  --status-list See status of all files\033[0m")
    print("\033[36m  --rules       Display this rules reference\033[0m")
    print("\033[36m" + "="*80 + "\033[0m")

def list_status_and_slug(rundown_path):
    """List status and slug for all files in rundown directory"""
    segment_files = sorted(rundown_path.glob("*.md"))
    if not segment_files:
        print(f"\033[31munknown\terror\tNo markdown files found in {rundown_path}\033[0m")
        return
    
    for file_path in segment_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            frontmatter = parse_yaml_frontmatter(content)
            status = frontmatter.get("status", "").strip().lower()
            slug = frontmatter.get("slug", file_path.stem).strip().lower()
            print(f"status: {status}\tslug: {slug}")
        except Exception:
            print(f"\033[31munknown\terror\t{file_path.name}: Failed to read file\033[0m")

def validate_cue_blocks(segment_files):
    valid = True
    cue_pattern = re.compile(r"(<!--\s*Begin Cue\s*-->.*?(?:<!--\s*End Cue\s*-->|$))", re.DOTALL | re.IGNORECASE)
    # Also handle malformed cue blocks with extra angle brackets
    malformed_cue_pattern = re.compile(r"(<<!--\s*Begin Cue\s*-->>.*?(?:<<!--\s*End Cue\s*-->>|$))", re.DOTALL | re.IGNORECASE)

    # First, validate order field vs filename prefix and check for duplicates
    order_counts = {}
    for file_path in segment_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            frontmatter = parse_yaml_frontmatter(content)
            order = str(frontmatter.get("order", "")).strip()
            
            # Track order field usage for duplicate detection
            if order:
                if order in order_counts:
                    order_counts[order].append(file_path.name)
                else:
                    order_counts[order] = [file_path.name]
            
            # Extract numeric prefix from filename
            filename_match = re.match(r'^(\d+)', file_path.name)
            filename_prefix = filename_match.group(1) if filename_match else None
            
            if filename_prefix and order and filename_prefix != order:
                print(f"\033[31m{file_path.name} has filename prefix '{filename_prefix}' but order field '{order}' - will fall into position {order} in rendered output\033[0m")
            elif filename_prefix and not order:
                print(f"\033[33mWARNING: {file_path.name} has filename prefix '{filename_prefix}' but no order field - will be sorted last\033[0m")
            elif not filename_prefix and order:
                print(f"\033[33mWARNING: {file_path.name} has order field '{order}' but no numeric filename prefix\033[0m")
                
        except Exception:
            # Will be handled in the main validation loop below
            pass
    
    # Check for duplicate order values
    for order_val, file_list in order_counts.items():
        if len(file_list) > 1:
            print(f"\033[31mDUPLICATE ORDER '{order_val}' found in files: {', '.join(file_list)} - relative order between these files will be unpredictable\033[0m")
            valid = False

    for file_path in segment_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            print(f"\033[31munknown\terror\t{file_path.name}: Failed to read file\033[0m")
            valid = False
            continue

        frontmatter = parse_yaml_frontmatter(content)
        segment_id = frontmatter.get("id", "unknown")
        status = frontmatter.get("status", "").strip().lower()

        # Check status and log exclusion reason - Only allow production status
        if status != "production":
            if status == "":
                print(f"\033[31m{segment_id}\texcluded\t{file_path.name}: Status is empty (not 'production')\033[0m")
            else:
                print(f"\033[31m{segment_id}\texcluded\t{file_path.name}: Status '{status}' is not 'production'\033[0m")
            valid = False
            continue

        cue_blocks = cue_pattern.findall(content)
        malformed_cue_blocks = malformed_cue_pattern.findall(content)
        
        # Check for malformed cue blocks and warn
        if malformed_cue_blocks:
            print(f"\033[33mWARNING: {file_path.name} contains malformed cue blocks with extra angle brackets\033[0m")
            print(f"\033[33mFound: <<!-- Begin Cue -->> instead of <!-- Begin Cue -->\033[0m")
            # Convert malformed blocks to proper format for processing
            for malformed_block in malformed_cue_blocks:
                corrected_block = malformed_block.replace('<<!--', '<!--').replace('-->>', '-->')
                cue_blocks.append(corrected_block)
        
        for block in cue_blocks:
            cue_type = re.search(r"\[Type:\s*(.*?)\]", block, re.IGNORECASE)
            slug = re.search(r"\[Slug:\s*(.*?)\]", block, re.IGNORECASE)
            asset_id = re.search(r"\[AssetID:\s*(.*?)\]", block, re.IGNORECASE)
            media_url = re.search(r"\[MediaURL:\s*(.*?)\]", block, re.IGNORECASE)
            quote = re.search(r"\[Quote:\s*(.*?)\](?=\s*(?:\n\[|\[|$))", block, re.IGNORECASE | re.DOTALL)
            attribution = re.search(r"\[Attribution:\s*(.*?)\]", block, re.IGNORECASE)

            # Handle special ADLIB inline format: [Type: ADLIB, Duration: 00:01:00]
            adlib_inline = re.search(r"\[Type:\s*ADLIB\s*,\s*Duration:\s*(.*?)\]", block, re.IGNORECASE)
            
            if adlib_inline:
                # Special handling for inline ADLIB format
                cue_type_str = "ADLIB"
                asset_id_str = "ADLIB"
                slug_str = "adlib"
                # For validation purposes, treat as having slug and asset_id
                slug = type('obj', (object,), {'group': lambda self, x: 'adlib'})()
                asset_id = type('obj', (object,), {'group': lambda self, x: 'ADLIB'})()
            else:
                # Normal cue block parsing
                asset_id_str = asset_id.group(1).strip() if asset_id else "unknown"
                cue_type_str = cue_type.group(1).strip().upper() if cue_type else "unknown"
                slug_str = slug.group(1).strip().lower() if slug else "unknown-slug"

            errors = []
            if not cue_type and not adlib_inline:
                errors.append("Missing [Type]")
            elif cue_type_str not in VALID_CUE_TYPES:
                errors.append(f"Invalid [Type: {cue_type_str}]")
            
            # ADLIB and BREAK cues don't require slug, other cues do
            if cue_type_str not in ("ADLIB", "BREAK"):
                if not slug or not slug.group(1).strip():
                    errors.append("Missing or empty [Slug]")
            
            # ADLIB cues (both inline and standard) have optional AssetID, BREAK cues require AssetID, other cues require AssetID
            if cue_type_str not in ("ADLIB"):
                if not asset_id or not asset_id.group(1).strip():
                    errors.append("Missing or empty [AssetID]")
            
            if cue_type_str == "FSQ" and (not quote or not quote.group(1).strip()):
                errors.append("Missing or empty [Quote]")
            if cue_type_str == "GFX" and (not media_url or not media_url.group(1).strip()):
                errors.append("Missing or empty [MediaURL]")
            if not re.search(r"<!--\s*End Cue\s*-->", block, re.IGNORECASE):
                errors.append("Missing End Cue")

            color = "\033[32m" if not errors else "\033[31m"
            output = f"{asset_id_str} / {cue_type_str} / {slug_str} **{'VALID' if not errors else 'INVALID'}**"
            if errors:
                output += f" [{'; '.join(errors)}]"
            print(f"{color}{output}\033[0m")

            if errors:
                valid = False

    return valid

def format_cue_block(block, media_mapping=None, block_counter=None):
    cue_type = re.search(r"\[Type:\s*(.*?)\]", block, re.IGNORECASE)
    slug = re.search(r"\[Slug:\s*(.*?)\]", block, re.IGNORECASE)
    asset_id = re.search(r"\[AssetID:\s*(.*?)\]", block, re.IGNORECASE)
    media_url = re.search(r"\[MediaURL:\s*(.*?)\]", block, re.IGNORECASE)
    quote = re.search(r"\[Quote:\s*(.*?)\](?=\s*(?:\[|$))", block, re.IGNORECASE | re.DOTALL)
    attribution = re.search(r"\[Attribution:\s*(.*?)\]", block, re.IGNORECASE)
    duration = re.search(r"\[Duration:\s*(.*?)\]", block, re.IGNORECASE)
    transcription = re.search(r"\[Transcription:\s*(.*?)\]", block, re.IGNORECASE)

    # Handle special ADLIB inline format: [Type: ADLIB, Duration: 00:01:00]
    adlib_inline = re.search(r"\[Type:\s*ADLIB\s*,\s*Duration:\s*(.*?)\]", block, re.IGNORECASE)
    
    if adlib_inline:
        # Special handling for inline ADLIB format
        cue_type_str = "ADLIB"
        slug_str = "adlib"
        asset_id_str = "ADLIB"
        duration_str = adlib_inline.group(1).strip()
    elif not cue_type:
        return ""
    else:
        cue_type_str = cue_type.group(1).strip().upper()
        # Special handling for BREAK cues - use actual AssetID and Slug
        if cue_type_str == "BREAK":
            slug_str = slug.group(1).strip().lower() if slug else "break"
            asset_id_str = asset_id.group(1).strip() if asset_id else "BREAK"
        else:
            slug_str = slug.group(1).strip().lower() if slug else "unknown-slug"
            asset_id_str = asset_id.group(1).strip() if asset_id else "unknown"
    
    # Use enumerated number if available in media mapping
    display_slug = slug_str
    if media_mapping and slug_str in media_mapping:
        enumerated_number = media_mapping[slug_str]
        display_slug = f"{enumerated_number} {slug_str}"
    
    print(f"{asset_id_str}\t{cue_type_str}\t{slug_str}")

    entry = (
        "<div class='cue'>\n"
        "<p class='cue-header' style='font-weight:bold; font-size:1em;'>[[ {cue_type_str} / {display_slug} ]]</p>\n"
    ).format(cue_type_str=cue_type_str, display_slug=display_slug)

    if cue_type_str == "GFX":
        if media_url:
            media_url_str = media_url.group(1).strip()
            entry += (
                "<div class='gfx'>\n"
                "<img src='{media_url}' style='max-width:875px; max-height:875px; border:1px solid #ccc;' />\n"
                "</div>\n"
            ).format(media_url=media_url_str)

    elif cue_type_str == "SOT":
        entry += "<div class='sot'>\n"
        if duration and duration.group(1).strip():
            entry += (
                "<p style='margin-top: 0.1em; margin-bottom: 0; font-size: 0.72em;'>Duration: {duration}</p>\n"
            ).format(duration=duration.group(1).strip())
        if transcription and transcription.group(1).strip():
            entry += (
                "<p style='margin-top: 0.1em; margin-bottom: 0; font-size: 0.72em;'>Trans: {transcription}</p>\n"
            ).format(transcription=html.escape(transcription.group(1).strip()))
        else:
            entry += "<p style='margin-top: 0.1em; margin-bottom: 0; font-size: 0.72em;'>No Transcript</p>\n"
        entry += "</div>\n"

    elif cue_type_str == "FSQ":
        if quote:
            quote_text = quote.group(1).strip()
            if not quote_text:
                return ""
            attribution_text = re.sub(r'^\W+', '', attribution.group(1).strip()) if attribution else ""
            entry += (
                "<div class='fsq'>\n"
                "<blockquote>{0}</blockquote>\n"
                "<p>— {1}</p>\n"
                "</div>\n"
            ).format(html.escape(quote_text), html.escape(attribution_text))
        else:
            return ""

    elif cue_type_str == "ADLIB":
        # Use inline duration if available, otherwise look for separate Duration field
        if adlib_inline:
            duration_str = adlib_inline.group(1).strip()
        else:
            duration_str = duration.group(1).strip() if duration else "00:00"
        entry += (
            "<div class='adlib'>\n"
            "<p style='font-weight: bold; font-size: 1.5em;'>[AD LIB] {0}</p>\n"
            "</div>\n"
        ).format(duration_str)

    elif cue_type_str == "BREAK":
        # Handle block progression: A -> B -> C -> D...
        if block_counter is None or 'count' not in block_counter:
            # Should not happen with current initialization, but fallback
            current_block = "A"
            next_block = "B"
        else:
            # Each break marks the end of current block and start of next block
            current_block = chr(65 + block_counter['count'])  # A=0, B=1, C=2...
            next_block = chr(65 + block_counter['count'] + 1)
            block_counter['count'] += 1  # Increment for next break
        
        entry += (
            "<div class='block-end' style='text-align: center; font-weight: bold; font-size: 1.2em; margin: 20px 0; padding: 10px; background-color: #f0f0f0; border: 2px solid #ccc;'>"
            "END OF BLOCK {current_block}"
            "</div>\n"
            "<div class='page-break'></div>\n"
            "<div class='block-start' style='text-align: center; font-weight: bold; font-size: 1.2em; margin: 20px 0; padding: 10px; background-color: #e8f4fd; border: 2px solid #007acc;'>"
            "BEGINNING OF BLOCK {next_block}"
            "</div>\n"
        ).format(current_block=current_block, next_block=next_block)

    entry += "</div>\n"
    return entry

def process_segment(file_path, para_counter, media_mapping=None, block_counter=None):
    try:
        print(f"\033[36mProcessing segment file: {file_path.name}\033[0m")  # DEBUG
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        print(f"\033[31munknown\terror\t{file_path.name}: Failed to read file\033[0m")
        return [], para_counter

    frontmatter = parse_yaml_frontmatter(content)
    slug = frontmatter.get("slug", file_path.stem).strip().lower()
    segment_id = frontmatter.get("id", "unknown")
    status = frontmatter.get("status", "").strip().lower()

    # Only process segments with status: production
    if status != "production":
        if status == "":
            print(f"\033[31m{segment_id}\texcluded\t{file_path.name}: Status is empty (not 'production')\033[0m")
        else:
            print(f"\033[31m{segment_id}\texcluded\t{file_path.name}: Status '{status}' is not 'production'\033[0m")
        return [], para_counter

    print(f"{segment_id}\tsegment\t{slug}")

    # Debug: Show content before processing
    print(f"\033[35mDEBUG: Original content length: {len(content)}\033[0m")
    
    content = re.sub(r'^\s*---\s*.*?---\s*', '', content, flags=re.DOTALL)
    print(f"\033[35mDEBUG: After frontmatter removal: {len(content)}\033[0m")
    
    # Remove specific unwanted sections but preserve ## Script content
    content = re.sub(r'##\s*Notes\s*.*?(?=\n##|\n---|$)', '', content, flags=re.DOTALL)
    print(f"\033[35mDEBUG: After Notes removal: {len(content)}\033[0m")
    
    content = re.sub(r'##\s*Description\s*.*?(?=\n##|\n---|$)', '', content, flags=re.DOTALL)
    print(f"\033[35mDEBUG: After Description removal: {len(content)}\033[0m")
    
    # Remove ## Script header but keep the content under it
    content = re.sub(r'##\s*Script\s*\n', '', content, flags=re.IGNORECASE)
    print(f"\033[35mDEBUG: After Script header removal: {len(content)}\033[0m")
    print(f"\033[35mDEBUG: Final content preview: {repr(content[:200])}\033[0m")

    if not content.strip() and not slug:
        return [(
            "<p style='text-align:left; font-weight:bold; font-size:2em; color:red; font-family:Helvetica,sans-serif;'>"
            "COMPILE ERROR29278: Missing Slug; Fatal output \\/\\ can not compile</p>\n"
        )], para_counter

    if not content.strip():
        print(f"\033[33mWARNING: {file_path.name} has no content after frontmatter removal\033[0m")  # DEBUG
        return [], para_counter

    print(f"\033[32mGenerating output for segment: {slug}\033[0m")  # DEBUG

    header_html = (
        "<p class='segment-header' style='text-align:left; font-weight:bold; font-size:1.5em; font-family:Helvetica,sans-serif;'>"
        "{slug}</p>\n"
    ).format(slug=slug)

    output = [header_html]
    seen_slugs = set()
    processed_cues = set()

    sot_pattern = r"(\{SOT/[^}]+\})"
    cue_pattern = r"(<!--\s*Begin Cue\s*-->.*?<!--\s*End Cue\s*-->)"
    # Also handle malformed cue blocks with extra angle brackets
    malformed_cue_pattern = r"(<<!--\s*Begin Cue\s*-->>.*?<<!--\s*End Cue\s*-->>)"

    sot_matches = list(re.finditer(sot_pattern, content, re.IGNORECASE))
    cue_matches = list(re.finditer(cue_pattern, content, re.DOTALL | re.IGNORECASE))
    malformed_cue_matches = list(re.finditer(malformed_cue_pattern, content, re.DOTALL | re.IGNORECASE))
    
    # Convert malformed cue matches to proper format
    for match in malformed_cue_matches:
        corrected_content = match.group(0).replace('<<!--', '<!--').replace('-->>', '-->')
        print(f"\033[33mCORRECTING: Malformed cue block in {file_path.name}\033[0m")
        # Create a new match object for the corrected content
        cue_matches.append(re.match(cue_pattern, corrected_content))
    
    all_matches = sot_matches + cue_matches
    all_matches = [m for m in all_matches if m is not None]  # Filter out None matches
    all_matches.sort(key=lambda m: m.start())

    pos = 0
    for match in all_matches:
        part = content[pos:match.start()].strip()
        if part:
            paragraphs = re.split(r'\n\s*\n', part)
            for para in paragraphs:
                para = para.strip()
                if not para or re.match(r"\[MediaURL:[^\]]+\]", para, re.IGNORECASE) or re.match(r"<img\s", para, re.IGNORECASE):
                    continue
                para = html.escape(para).replace("\n", "<br>")
                if '%' in para:
                    previous_para = para
                    para = para.replace('%', '%%')
                para_counter += 1
                output.append(
                    "<p id='para-{0}' style='text-align:justify; width:100%; font-family:Helvetica,sans-serif; line-height:1.5;'>{1}</p>\n".format(para_counter, para)
                )
        block = match.group(0)
        if re.match(sot_pattern, block, re.IGNORECASE):
            sot_name = block[5:-1].strip()
            if sot_name in seen_slugs:
                pos = match.end()
                continue
            seen_slugs.add(sot_name)
            
            # Use enumerated prefix if available in media mapping
            display_sot_name = sot_name
            if media_mapping and sot_name in media_mapping:
                enumerated_prefix = media_mapping[sot_name]
                display_sot_name = f"{enumerated_prefix} {sot_name}"
            
            print(f"unknown\tSOT\t{sot_name}")
            output.append(
                "<div class='cue'>\n"
                "<p class='cue-header' style='font-weight:bold; font-size:1em;'>[[ SOT / {0} ]]</p>\n"
                "<div class='sot'>\n"
                "<p style='margin-top: 0.1em; margin-bottom: 0; font-size: 0.72em;'>No Transcript</p>\n"
                "</div>\n"
                "</div>\n".format(display_sot_name)
            )
        else:
            asset_id = re.search(r"\[AssetID:\s*(.*?)\]", block, re.IGNORECASE)
            slug = re.search(r"\[Slug:\s*(.*?)\]", block, re.IGNORECASE)
            if asset_id and slug:
                cue_key = (asset_id.group(1).strip(), slug.group(1).strip().lower())
                if cue_key in processed_cues:
                    pos = match.end()
                    continue
                processed_cues.add(cue_key)
            cue_output = format_cue_block(block, media_mapping, block_counter)
            if cue_output:
                slug_match = re.search(r"\[\[ [A-Z]+ / ([^\]]+) \]\]", cue_output)
                if slug_match:
                    cue_slug = slug_match.group(1).strip()
                    if cue_slug in seen_slugs:
                        pos = match.end()
                        continue
                    seen_slugs.add(cue_slug)
                output.append(cue_output)
        pos = match.end()

    part = content[pos:].strip()
    if part:
        paragraphs = re.split(r'\n\s*\n', part)
        for para in paragraphs:
            para = para.strip()
            if not para or re.match(r"\[MediaURL:[^\]]+\]", para, re.IGNORECASE) or re.match(r"<img\s", para, re.IGNORECASE):
                continue
            para = html.escape(para).replace("\n", "<br>")
            if '%' in para:
                previous_para = para
                para = para.replace('%', '%%')
            para_counter += 1
            output.append(
                "<p id='para-{0}' style='text-align:justify; width:100%; font-family:Helvetica,sans-serif; line-height:1.5;'>{1}</p>\n".format(para_counter, para)
            )

    print(f"\033[32mSegment {slug} generated {len(output)} output elements\033[0m")  # DEBUG
    return output, para_counter

def compile_script(episode_number, validate_only=False, status_list=False, show_rules=False):
    """
    Main script compilation function - adapted for Show-Build path management
    """
    episode_path = EPISODE_ROOT / episode_number
    info_path = episode_path / "info.md"
    
    # Check if media-list.txt exists and warn if not
    media_list_path = episode_path / "rundown" / "media-list.txt"
    if not media_list_path.exists():
        print(f"\033[33m" + "="*80 + "\033[0m")
        print(f"\033[33mWARNING: media-list.txt not found at {media_list_path}\033[0m")
        print(f"\033[33mElement enumerations will not be present in host script until media-list is generated.\033[0m")
        print(f"\033[33mRun 'python render-list.py {episode_number}' first to create the media list.\033[0m")
        print(f"\033[33m" + "="*80 + "\033[0m")
        print()  # Blank line after warning
    
    # Load media list mapping for enumerated filenames
    media_mapping = load_media_list_mapping(episode_path)
    
    # Handle rules display
    if show_rules:
        display_rules()
        return
        
    if not episode_path.exists():
        print(f"\033[31munknown\terror\t{episode_number}: Episode folder does not exist at {episode_path}\033[0m")
        return

    rundown_path = episode_path / "rundown"
    if not rundown_path.exists():
        print(f"\033[31munknown\terror\t{episode_number}: Rundown folder does not exist at {rundown_path}\033[0m")
        return

    # Handle status list flag
    if status_list:
        list_status_and_slug(rundown_path)
        return

    segment_files = sorted(rundown_path.glob("*.md"))
    if not segment_files:
        print(f"\033[31munknown\terror\t{episode_number}: No markdown files found in {rundown_path}\033[0m")
        return

    # Filter segments by status: production only, and sort by order field
    valid_segments = []
    segment_order_map = {}
    
    print(f"\033[36m=== FILTERING SEGMENTS ===\033[0m")
    for file_path in segment_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            frontmatter = parse_yaml_frontmatter(content)
            status = frontmatter.get("status", "").strip().lower()
            segment_id = frontmatter.get("id", "unknown")
            order = str(frontmatter.get("order", "")).strip()
            
            if status == "production":
                valid_segments.append(file_path)
                # Store order field for sorting - convert to int for proper numerical sorting
                order_val = order if order else "9999"  # Default high value for empty order
                segment_order_map[file_path] = order_val
                print(f"\033[32m✓ INCLUDED: {file_path.name} (status: 'production', order: '{order_val}')\033[0m")
            else:
                if status == "":
                    print(f"\033[31m✗ EXCLUDED: {segment_id}\t{file_path.name}: Status is empty (not 'production')\033[0m")
                else:
                    print(f"\033[31m✗ EXCLUDED: {segment_id}\t{file_path.name}: Status '{status}' is not 'production'\033[0m")
        except Exception as e:
            print(f"\033[31munknown\terror\t{file_path.name}: Failed to read file - {str(e)}\033[0m")

    # Sort by order field (numeric) with filename as tiebreaker for stability
    valid_segments.sort(key=lambda x: (int(segment_order_map[x]) if segment_order_map[x].isdigit() else 9999, x.name))
    print(f"\033[36mSorted segments by order field (with filename tiebreaker):\033[0m")
    for seg in valid_segments:
        order_val = segment_order_map[seg]
        print(f"\033[36m  {seg.name} (order: {order_val})\033[0m")

    if not valid_segments:
        print(f"\033[31munknown\terror\t{episode_number}: No segments with status 'production' found\033[0m")
        return

    if not validate_cue_blocks(valid_segments):
        print(f"\033[31munknown\terror\t{episode_number}: Validation failed, aborting\033[0m")
        return

    if validate_only:
        return

    info_data = {}
    if info_path.exists():
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                info_data = parse_yaml_frontmatter(f.read())
        except Exception:
            print(f"\033[31munknown\terror\tinfo.md: Failed to read info file\033[0m")

    episode_num = info_data.get("episode_number", episode_number)
    title = info_data.get("title", f"EPISODE NUMBER {episode_number}")
    subtitle = info_data.get("subtitle", "")
    airdate = info_data.get("airdate", "")
    date_str = ""
    mm = dd = yy = ""
    try:
        if airdate:
            if isinstance(airdate, (date, datetime)):
                airdate = airdate.strftime("%Y-%m-%d")
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", airdate):
                raise ValueError(f"Airdate '{airdate}' is not in 'YYYY-MM-DD' format")
            airdate_date = datetime.strptime(airdate, "%Y-%m-%d").replace(hour=21, minute=0, second=0)
            date_str = airdate_date.strftime("%B %dth, %Y at 9:00 PM")
            mm, dd, yy = airdate_date.strftime("%m-%d-%y").split("-")
    except (ValueError, TypeError, AttributeError) as e:
        print(f"\033[31mError parsing airdate: {e}\033[0m")
        print(f"\033[33mProceeding without valid airdate.\033[0m")
        date_str = ""
        mm = dd = yy = ""

    # Output to exports folder (sibling to rundown)
    exports_path = episode_path / "exports"
    exports_path.mkdir(exist_ok=True)  # Create exports folder if it doesn't exist
    print(f"\033[32mExporting to directory: {exports_path}\033[0m")
    
    base_filename = f"script-{'-'.join(filter(None, [mm, dd, yy]))}-production-1.html"
    output_path = exports_path / base_filename
    version = 1
    while output_path.exists():
        version += 1
        output_path = exports_path / f"script-{'-'.join(filter(None, [mm, dd, yy]))}-production-{version}.html"

    cover_html = (
        "<div class='cover-page'>\n"
        "<div style='text-align: center; font-size: 2.5em'>DISAFFECTED</div>\n"
        "<div style='text-align: center; font-size: 1em'>EPISODE: {episode_num}</div>\n"
        "<div style='text-align: center; font-size: 1.2em'>{date_str}</div>\n"
        "<br><br>\n"
        "<div style='text-align: center; font-size: 1.2em'>Title:</div>\n"
        "<div style='text-align: center; font-size: 1.5em'>{title}</div>\n"
    )
    if subtitle:
        cover_html += "<br><br>\n<div style='text-align: center; font-size: 1.2em'>Subtitle</div>\n<div style='text-align: center; font-size: 1.2em'>{subtitle}</div>\n"
    cover_html += "<br><br>\n</div>\n"

    script_output = []
    para_counter = 0
    block_counter = {'count': 0}  # Track block progression A, B, C...

    script_output.append(
        "<!DOCTYPE html>\n<html>\n<head>\n"
        "<style>\n"
        "body { font-family: Helvetica, sans-serif; font-size: 33px; }\n"
        ".container { width: 95%; max-width: 800px; margin: 0 auto; border-left: 1px dotted rgba(128, 128, 128, 0.5); border-right: 1px dotted rgba(128, 128, 128, 0.5); padding: 1em; }\n"
        ".cue { margin-top: 2em; page-break-inside: avoid; }\n"
        ".cue-header { font-weight: bold; font-size: 1.2em; margin-bottom: 0.5em; }\n"
        ".gfx { text-align: left; }\n"
        ".sot { text-align: left; font-size: 1.1em; }\n"
        ".fsq { text-align: left; max-width: 100%; page-break-inside: avoid; }\n"
        ".fsq blockquote { width: 100%; max-width: 100%; margin: 0; padding: 1.65em; border-left: 9px solid #ccc; border-right: 9px solid #ccc; line-height: 1.5; color: rgba(0, 0, 0, 0.75); box-sizing: border-box; }\n"
        ".fsq p { font-size: 1.1em; margin-top: 0.5em; }\n"
        ".block-end { text-align: center; font-weight: bold; font-size: 1.2em; text-transform: uppercase; margin: 2em 0 0.5em 0; background: #f0f0f0; padding: 1em; border: 2px solid #ccc; page-break-after: always; }\n"
        ".block-break { text-align: center; font-weight: bold; font-size: 1em; text-transform: uppercase; margin: 0.5em 0 2em 0; background: #e0e0e0; padding: 0.5em; }\n"
        ".block-start { text-align: center; font-weight: bold; font-size: 1.2em; text-transform: uppercase; margin: 2em 0; background: #f0f0f0; padding: 1em; border: 2px solid #ccc; }\n"
        ".page-number { \n"
        "  position: fixed;\n"
        "  bottom: 20px;\n"
        "  right: 20px;\n"
        "  font-size: 12pt;\n"
        "  color: #333;\n"
        "  font-weight: bold;\n"
        "  background: white;\n"
        "  padding: 5px 10px;\n"
        "  border: 1px solid #ccc;\n"
        "  z-index: 1000;\n"
        "}\n"
        ".page-break { page-break-before: always; }\n"
        "/* Print styles for PDF pagination */\n"
        "@media print {\n"
        "  @page {\n"
        "    size: 8.5in 11in;\n"
        "    margin: 1in;\n"
        "  }\n"
        "  body { font-size: 27px; }\n"
        "  .container { border: none; width: 100%; max-width: none; margin: 0; padding: 0; }\n"
        "  .cue { page-break-inside: avoid; break-inside: avoid; margin-top: 1.5em; }\n"
        "  .segment-header { page-break-after: avoid; }\n"
        "  .gfx img { max-width: 6in; max-height: 6in; }\n"
        "  .fsq blockquote { page-break-inside: avoid; break-inside: avoid; }\n"
        "  .cover-page { page-break-after: always; }\n"
        "  .block-end { page-break-after: always; }\n"
        "  .block-start { page-break-before: avoid; }\n"
        "  .page-number {\n"
        "    position: absolute;\n"
        "    bottom: 0.5in;\n"
        "    right: 0.5in;\n"
        "    font-size: 12pt;\n"
        "    color: #333;\n"
        "    font-weight: bold;\n"
        "    background: white;\n"
        "    padding: 5px 10px;\n"
        "    border: 1px solid #333;\n"
        "  }\n"
        "}\n"
        "/* Screen styles for page simulation */\n"
        "@media screen {\n"
        "  .page-number {\n"
        "    position: relative;\n"
        "    text-align: right;\n"
        "    font-size: 0.8em;\n"
        "    color: #666;\n"
        "    margin: 1em 0;\n"
        "    padding: 0.5em 0;\n"
        "    border-bottom: 1px dotted #ccc;\n"
        "  }\n"
        "}\n"
        "</style>\n"
        "</head>\n<body>\n<div class='container'>\n"
    )
    script_output.append(cover_html.format(episode_num=episode_num, date_str=date_str, title=title, subtitle=subtitle))

    # Load header template if available
    if HEADER_PATH.exists():
        try:
            with open(HEADER_PATH, "r", encoding="utf-8") as f:
                header_html = f.read()
        except Exception:
            print(f"\033[31munknown\terror\theader: Failed to read header file at {HEADER_PATH}\033[0m")
            header_html = ""
    else:
        print(f"\033[33mWARNING: Header template not found at {HEADER_PATH}\033[0m")
        header_html = ""
    script_output.append(header_html)
    
    # Add initial BLOCK A marker
    script_output.append("<div class='block-start'>BLOCK A</div>\n")

    print(f"\033[36m=== PROCESSING SEGMENTS ===\033[0m")
    previous_was_break = False
    segment_count = 0
    
    for i, segment in enumerate(valid_segments):
        if i > 0:  # Add blank line between segments (except before first)
            print()
            # Add horizontal rule between segments
            script_output.append("<hr style='border: 1px solid #ccc; margin: 2em 0;' />\n")
        
        # Remove automatic page breaks to avoid conflicts with BREAK cues
        # Page breaks are now handled exclusively by BREAK cue blocks
        
        # Block transitions are now handled entirely within BREAK cues
        
        segment_html, para_counter = process_segment(segment, para_counter, media_mapping, block_counter)
        script_output.extend(segment_html)
        
        # Check if this segment is a break segment
        try:
            with open(segment, "r", encoding="utf-8") as f:
                content = f.read()
            frontmatter = parse_yaml_frontmatter(content)
            if "break" in segment.name.lower() or frontmatter.get("type", "").lower() == "break":
                previous_was_break = True
        except Exception:
            pass

    script_output.append("</div>\n</body>\n</html>")

    if output_path.exists():
        output_path.unlink()
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(script_output))
        print(f"\033[32mOutput written to: {output_path}\033[0m")
        
        # Generate PDF using wkhtmltopdf
        pdf_path = output_path.with_suffix('.pdf')
        print(f"\033[36mGenerating PDF: {pdf_path.name}\033[0m")
        
        try:
            import subprocess
            result = subprocess.run([
                'wkhtmltopdf',
                '--page-size', 'Letter',
                '--margin-top', '0.75in',
                '--margin-right', '0.75in', 
                '--margin-bottom', '0.75in',
                '--margin-left', '0.75in',
                '--enable-local-file-access',
                '--encoding', 'UTF-8',
                str(output_path),
                str(pdf_path)
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"\033[32mPDF generated: {pdf_path}\033[0m")
                if result.stderr:
                    print(f"\033[33mwkhtmltopdf warnings: {result.stderr.strip()}\033[0m")
            else:
                print(f"\033[33mWARNING: wkhtmltopdf failed: {result.stderr.strip()}\033[0m")
                print(f"\033[33mStdout: {result.stdout.strip()}\033[0m")
                print(f"\033[33mHTML file available at: {output_path}\033[0m")
                
        except FileNotFoundError:
            print(f"\033[33mWARNING: wkhtmltopdf not found. Install with: sudo apt install wkhtmltopdf\033[0m")
            print(f"\033[33mHTML file available at: {output_path}\033[0m")
        except subprocess.TimeoutExpired:
            print(f"\033[33mWARNING: PDF generation timed out after 60 seconds\033[0m")
            print(f"\033[33mHTML file available at: {output_path}\033[0m")
        except Exception as e:
            print(f"\033[33mWARNING: PDF generation failed: {e}\033[0m")
            print(f"\033[33mHTML file available at: {output_path}\033[0m")
            
    except Exception:
        print(f"\033[31munknown\terror\t{output_path.name}: Failed to write output file\033[0m")

def main():
    print(f"Render-script-host.py version {__version__} (Show-Build Edition)")
    print("\033[36m" + "="*80 + "\033[0m")
    print("\033[36mSHOW-BUILD HOST SCRIPT RENDERER\033[0m")
    print("\033[36m" + "="*80 + "\033[0m")
    print(f"\033[35mEpisodes Root: {EPISODE_ROOT}\033[0m")
    print(f"\033[35mHeader Template: {HEADER_PATH}\033[0m")
    print(f"\033[35mValid Cue Types: {', '.join(VALID_CUE_TYPES)}\033[0m")
    print("\033[36m" + "="*80 + "\033[0m")
    
    parser = argparse.ArgumentParser(
        description="Render host reading script from episode markdown files (Show-Build Edition)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python render-script-host.py 0236              # Render episode 0236
  python render-script-host.py 0236 --validate   # Validate only, no output
  python render-script-host.py 0236 --status-list # Show all file statuses
  python render-script-host.py 0236 --rules      # Display validation rules

Show-Build Configuration:
  Episodes path: {EPISODE_ROOT}
  Output path: {{episode}}/exports/
  Header template: {HEADER_PATH}
        """
    )
    
    parser.add_argument("episode_number", help="4-digit episode number (e.g., 0236)")
    parser.add_argument("--validate", action="store_true", help="Run validation only, no HTML output")
    parser.add_argument("--status-list", action="store_true", help="List status and slug for all files in rundown directory")
    parser.add_argument("--rules", action="store_true", help="Display all validation rules")
    
    args = parser.parse_args()
    
    if not re.match(r"^\d{4}$", args.episode_number):
        print("\033[31mERROR: Episode number must be 4 digits (e.g., 0236)\033[0m")
        sys.exit(1)
    
    # Display debug information
    episode_path = EPISODE_ROOT / args.episode_number
    print(f"\033[35m[DEBUG] Episode path: {episode_path}\033[0m")
    print(f"\033[35m[DEBUG] Episode exists: {episode_path.exists()}\033[0m")
    
    if episode_path.exists():
        info_path = episode_path / "info.md"
        rundown_path = episode_path / "rundown"
        print(f"\033[35m[DEBUG] Info path: {info_path} (exists: {info_path.exists()})\033[0m")
        print(f"\033[35m[DEBUG] Rundown path: {rundown_path} (exists: {rundown_path.exists()})\033[0m")
    
    compile_script(
        args.episode_number,
        validate_only=args.validate,
        status_list=args.status_list,
        show_rules=args.rules
    )

if __name__ == "__main__":
    main()