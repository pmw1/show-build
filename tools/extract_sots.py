#!/usr/bin/env python3
"""
SOT Video Extraction Script

Processes rundown segment markdown files to extract SOT cue blocks and generates trimmed video clips
using FFmpeg on the host system with 2-second padding.

Usage:
    python extract_sots.py <episode_number> <index_number> [--dry-run]

Examples:
    python extract_sots.py 0237 10    # Processes "10 *.md" file from episode 0237 rundown
    python extract_sots.py 0225 20    # Processes "20 *.md" file from episode 0225 rundown
"""

import re
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

# Add the app directory to Python path so we can import Show-Build modules
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))


def parse_timecode(timecode: str) -> Tuple[int, int, int, int]:
    """Parse timecode in format hh:mm:ss.ff to hours, minutes, seconds, frames."""
    # Handle both hh:mm:ss.ff and hh:mm:ss:ff formats
    timecode = timecode.replace('.', ':')
    
    parts = timecode.split(':')
    if len(parts) == 3:
        # No frames specified, default to 00
        parts.append('00')
    elif len(parts) != 4:
        raise ValueError(f"Invalid timecode format: {timecode}")
    
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    frames = int(parts[3])
    
    return hours, minutes, seconds, frames


def timecode_to_frames(timecode: str, fps: float = 25.0) -> int:
    """Convert timecode to total frame count."""
    hours, minutes, seconds, frames = parse_timecode(timecode)
    total_seconds = hours * 3600 + minutes * 60 + seconds
    total_frames = int(total_seconds * fps) + frames
    return total_frames


def frames_to_timecode(total_frames: int, fps: float = 25.0) -> str:
    """Convert frame count back to timecode format hh:mm:ss.ss (decimal seconds)."""
    total_seconds_decimal = total_frames / fps
    
    hours = int(total_seconds_decimal // 3600)
    minutes = int((total_seconds_decimal % 3600) // 60)
    seconds = total_seconds_decimal % 60
    
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"


def add_seconds_to_timecode(timecode: str, seconds_to_add: float, fps: float = 25.0) -> str:
    """Add seconds to a timecode, handling frame boundaries."""
    total_frames = timecode_to_frames(timecode, fps)
    frames_to_add = int(seconds_to_add * fps)
    new_total_frames = max(0, total_frames + frames_to_add)  # Don't go negative
    return frames_to_timecode(new_total_frames, fps)


def normalize_slug(slug: str) -> str:
    """Convert slug to lowercase and replace spaces with dashes."""
    return slug.lower().replace(' ', '-')


def extract_sot_cues(markdown_content: str) -> List[Dict]:
    """Extract SOT cue blocks from markdown content."""
    sot_cues = []
    
    # Find all cue blocks
    cue_pattern = re.compile(r'<!-- Begin Cue -->(.*?)<!-- End Cue -->', re.DOTALL)
    cue_blocks = cue_pattern.findall(markdown_content)
    
    for block in cue_blocks:
        # Check if this is an SOT cue
        type_match = re.search(r'\[Type:\s*(.*?)\]', block, re.IGNORECASE)
        if not type_match or type_match.group(1).strip().upper() != 'SOT':
            continue
        
        # Extract required fields
        slug_match = re.search(r'\[Slug:\s*(.*?)\]', block, re.IGNORECASE)
        asset_id_match = re.search(r'\[AssetID:\s*(.*?)\]', block, re.IGNORECASE)
        media_url_match = re.search(r'\[MediaURL:\s*(.*?)\]', block, re.IGNORECASE)
        trim_start_match = re.search(r'\[TrimStart:\s*(.*?)\]', block, re.IGNORECASE)
        trim_end_match = re.search(r'\[TrimEnd:\s*(.*?)\]', block, re.IGNORECASE)
        
        # Skip if missing required fields or no trim times
        if not all([slug_match, asset_id_match, media_url_match, trim_start_match, trim_end_match]):
            continue
            
        slug = slug_match.group(1).strip()
        asset_id = asset_id_match.group(1).strip()
        media_url = media_url_match.group(1).strip()
        trim_start = trim_start_match.group(1).strip()
        trim_end = trim_end_match.group(1).strip()
        
        # Skip if trim times are 00:00:00 (unset)
        if trim_start in ['00:00:00', '00:00:00.00'] and trim_end in ['00:00:00', '00:00:00.00']:
            continue
        
        # Add 2-second padding
        real_in = add_seconds_to_timecode(trim_start, -2.0)
        real_out = add_seconds_to_timecode(trim_end, 2.0)
        
        # Generate output filename
        filename = normalize_slug(slug) + '.mp4'
        
        sot_cues.append({
            'asset_id': asset_id,
            'slug': slug,
            'media_url': media_url,
            'time_in': trim_start,
            'time_out': trim_end,
            'real_in': real_in,
            'real_out': real_out,
            'filename': filename
        })
    
    return sot_cues


def resolve_media_path(media_url: str, markdown_file_path: Path) -> Path:
    """Resolve media URL to absolute file path."""
    # If it's already an absolute path, return it
    if Path(media_url).is_absolute():
        return Path(media_url)
    
    # Handle relative paths (like ../assets/video/filename.mp4)
    if media_url.startswith('../'):
        # Resolve relative to the markdown file's directory
        base_dir = markdown_file_path.parent
        resolved_path = (base_dir / media_url).resolve()
        return resolved_path
    
    # Handle paths that start with assets/ (relative to episode root)
    if media_url.startswith('assets/'):
        episode_dir = markdown_file_path.parent.parent  # rundown -> episode
        return episode_dir / media_url
    
    # Handle URLs or other formats - for now just return as-is
    return Path(media_url)


def run_ffmpeg_extraction(sot_cue: Dict, input_path: Path, output_dir: Path, dry_run: bool = False) -> bool:
    """Run FFmpeg to extract video clip with timecode reset and audio sync."""
    output_path = output_dir / sot_cue['filename']
    
    # Build FFmpeg command with timecode reset and audio sync
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output files
        '-i', str(input_path),
        '-ss', sot_cue['real_in'],
        '-to', sot_cue['real_out'],
        '-c:v', 'libx264',  # Re-encode video to reset timecode
        '-c:a', 'aac',      # Re-encode audio for sync
        '-avoid_negative_ts', 'make_zero',  # Reset timestamps to start at zero
        '-fflags', '+genpts',  # Generate presentation timestamps
        '-async', '1',      # Audio sync correction
        '-vsync', '1',      # Video sync correction
        str(output_path)
    ]
    
    print(f"Processing: {sot_cue['slug']}")
    print(f"  Input: {input_path}")
    print(f"  Output: {output_path}")
    print(f"  Time: {sot_cue['real_in']} to {sot_cue['real_out']} (padded)")
    print(f"  Original: {sot_cue['time_in']} to {sot_cue['time_out']}")
    print(f"  Command: {' '.join(cmd)}")
    
    if dry_run:
        print("  [DRY RUN - Not executing]")
        return True
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"  ✅ Success: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Error: FFmpeg failed")
        print(f"  stdout: {e.stdout}")
        print(f"  stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"  ❌ Error: FFmpeg not found. Please install FFmpeg on the host system.")
        return False


def find_rundown_file_by_index(rundown_dir: Path, index: str) -> Path:
    """Find the rundown file that starts with the given index number."""
    pattern = f"{index} *.md"
    matching_files = list(rundown_dir.glob(pattern))
    
    if not matching_files:
        raise FileNotFoundError(f"No rundown file found matching pattern '{pattern}' in {rundown_dir}")
    
    if len(matching_files) > 1:
        print(f"Warning: Multiple files found matching pattern '{pattern}':")
        for f in matching_files:
            print(f"  - {f.name}")
        print(f"Using: {matching_files[0].name}")
    
    return matching_files[0]


def main():
    parser = argparse.ArgumentParser(description='Extract SOT video clips from episode rundown files')
    parser.add_argument('episode_number', help='Episode number (e.g., 0237)')
    parser.add_argument('index_number', help='Index number of the rundown file (e.g., 10)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    try:
        # Import Show-Build path management
        from core.paths import ShowBuildPaths
        paths = ShowBuildPaths()
    except ImportError as e:
        print(f"Error: Cannot import Show-Build path management: {e}")
        print("Make sure you're running this script from the show-build directory")
        sys.exit(1)
    
    episode_number = args.episode_number
    index_number = args.index_number
    
    # Get rundown directory using Show-Build path management
    rundown_dir = paths.get_rundown_dir(episode_number)
    if not rundown_dir.exists():
        print(f"Error: Rundown directory does not exist: {rundown_dir}")
        sys.exit(1)
    
    # Find the specific rundown file by index
    try:
        markdown_path = find_rundown_file_by_index(rundown_dir, index_number)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(f"Available files in {rundown_dir}:")
        for f in rundown_dir.glob('*.md'):
            print(f"  - {f.name}")
        sys.exit(1)
    
    # Read segment markdown content
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading segment markdown file: {e}")
        sys.exit(1)
    
    # Extract SOT cues
    sot_cues = extract_sot_cues(content)
    
    if not sot_cues:
        print("No SOT cues with trim times found in the segment markdown file.")
        sys.exit(0)
    
    print(f"Processing episode: {episode_number}")
    print(f"Processing segment: {markdown_path.name}")
    print(f"Found {len(sot_cues)} SOT cues to process:")
    print()
    
    # Get output directory using Show-Build path management
    episode_dir = paths.get_episode_dir(episode_number)
    output_dir = episode_dir / 'assets' / 'video'
    
    if not output_dir.exists():
        print(f"Error: Output directory does not exist: {output_dir}")
        sys.exit(1)
    
    print(f"Output directory: {output_dir}")
    print()
    
    # Process each SOT cue
    success_count = 0
    for i, sot_cue in enumerate(sot_cues, 1):
        print(f"=== Processing {i}/{len(sot_cues)} ===")
        
        # Resolve input file path
        input_path = resolve_media_path(sot_cue['media_url'], markdown_path)
        
        if not input_path.exists():
            print(f"  ❌ Error: Input file not found: {input_path}")
            continue
        
        # Run FFmpeg extraction
        if run_ffmpeg_extraction(sot_cue, input_path, output_dir, args.dry_run):
            success_count += 1
        
        print()
    
    # Summary
    print(f"=== Summary ===")
    print(f"Processed: {success_count}/{len(sot_cues)} clips successfully")
    if args.dry_run:
        print("(Dry run mode - no files were actually processed)")


if __name__ == '__main__':
    main()