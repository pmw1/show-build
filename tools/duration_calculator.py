#!/usr/bin/env python3
"""
Duration Calculator Tool - Show-Build Tools Suite

Calculates segment durations and updates episode totals using the centralized path system.

Usage:
    python duration_calculator.py --segment=SEGMEEJ44L61P9LZV
    python duration_calculator.py --episode=0236
"""

import argparse
import sys
import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add both tools and app directories to Python path
tools_dir = Path(__file__).parent
sys.path.insert(0, str(tools_dir))
sys.path.insert(0, str(tools_dir.parent / 'app'))

# Import from centralized paths system
from paths import EPISODE_ROOT, PROJECT_ROOT

# Import app-level path manager for more sophisticated path handling
try:
    from core.paths import ShowBuildPaths
    path_manager = ShowBuildPaths()
    EPISODES_ROOT = path_manager.episodes_root
except ImportError:
    # Fallback to tools path system
    EPISODES_ROOT = Path("/mnt/sync/disaffected/episodes")


class FileManager:
    """File operations for duration calculator."""
    
    @staticmethod
    def read_file(file_path: Path) -> str:
        """Read file content."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.read_text(encoding='utf-8')
    
    @staticmethod
    def write_file(file_path: Path, content: str) -> None:
        """Write file content."""
        file_path.write_text(content, encoding='utf-8')
    
    @staticmethod
    def extract_frontmatter(content: str) -> tuple[str, str, str]:
        """Extract YAML frontmatter from markdown content.
        Returns: (frontmatter, body, full_content)
        """
        if not content.startswith('---'):
            return "", content, content
        
        lines = content.split('\n')
        frontmatter_lines = []
        body_lines = []
        in_frontmatter = True
        frontmatter_end = 0
        
        for i, line in enumerate(lines[1:], 1):  # Skip first ---
            if line.strip() == '---' and in_frontmatter:
                frontmatter_end = i + 1
                in_frontmatter = False
                continue
            
            if in_frontmatter:
                frontmatter_lines.append(line)
            else:
                body_lines.append(line)
        
        frontmatter = '\n'.join(frontmatter_lines)
        body = '\n'.join(body_lines)
        
        return frontmatter, body, content
    
    @staticmethod
    def extract_asset_id_from_frontmatter(content: str) -> Optional[str]:
        """Extract AssetID from YAML frontmatter."""
        frontmatter, _, _ = FileManager.extract_frontmatter(content)
        if not frontmatter:
            return None
        
        lines = frontmatter.split('\n')
        for line in lines:
            trimmed_line = line.strip()
            if trimmed_line.startswith('AssetID:'):
                asset_id_part = trimmed_line[8:].strip()  # Remove 'AssetID:'
                return asset_id_part if asset_id_part and asset_id_part != '' else None
        
        return None


class DurationSettings:
    """Duration calculation settings."""
    def __init__(
        self,
        speech_wpm: int = 150,
        fsq_wpm: int = 120,
        include_adlibs: bool = True,
        include_sots: bool = True,
        include_fsqs: bool = True
    ):
        self.speech_wpm = speech_wpm
        self.fsq_wpm = fsq_wpm
        self.include_adlibs = include_adlibs
        self.include_sots = include_sots
        self.include_fsqs = include_fsqs


class CueAnalysis:
    """Analysis result for a cue."""
    def __init__(self, cue_type: str, calculated_duration: Optional[str] = None):
        self.cue_type = cue_type
        self.calculated_duration = calculated_duration


class EpisodeDurationCalculator:
    """Handles episode-wide duration calculation and updates using Show-Build path system."""
    
    def __init__(self):
        self.episodes_root = EPISODES_ROOT
        self.settings = DurationSettings(
            speech_wpm=150,
            fsq_wpm=120,
            include_adlibs=True,
            include_sots=True,
            include_fsqs=True
        )
        
        # Verify episodes directory exists
        if not self.episodes_root.exists():
            print(f"⚠️  Episodes directory not found at: {self.episodes_root}")
            print(f"   Please ensure the media path is correctly mounted.")
            print(f"   Expected path: /mnt/sync/disaffected/episodes")
    
    def find_segment_by_assetid(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Find segment file by AssetID using Show-Build path system."""
        if not self.episodes_root.exists():
            print(f"Episodes directory not found: {self.episodes_root}")
            return None
        
        print(f"🔍 Scanning episodes directory: {self.episodes_root}")
        
        episode_count = 0
        for episode_dir in self.episodes_root.iterdir():
            if not episode_dir.is_dir() or not episode_dir.name.isdigit():
                continue
            
            episode_count += 1
            episode_number = episode_dir.name
            rundown_path = episode_dir / "rundown"
            
            if not rundown_path.exists():
                continue
            
            for segment_file in rundown_path.glob("*.md"):
                try:
                    content = FileManager.read_file(segment_file)
                    file_asset_id = FileManager.extract_asset_id_from_frontmatter(content)
                    
                    if file_asset_id == asset_id:
                        print(f"✓ Found AssetID {asset_id} in episode {episode_number}")
                        return {
                            'file_path': segment_file,
                            'segment_name': segment_file.stem,
                            'episode_number': episode_number,
                            'asset_id': asset_id
                        }
                except Exception as e:
                    print(f"   Warning: Error reading {segment_file}: {e}")
                    continue
        
        print(f"   Scanned {episode_count} episodes, AssetID not found")
        return None
    
    def calculate_segment_duration(self, segment_file: Path, update_file: bool = True) -> float:
        """Calculate duration for a single segment file."""
        try:
            estimator = FileDurationEstimator(self.settings)
            
            # Read segment content
            content = FileManager.read_file(segment_file)
            
            # Parse content and calculate duration
            body_content, cue_blocks = estimator._parse_segment_content(content)
            
            # Calculate speech duration
            speech_word_count = estimator._count_words(body_content)
            speech_duration = speech_word_count / self.settings.speech_wpm * 60  # seconds
            
            # Analyze cue blocks
            sot_duration = 0.0
            fsq_duration = 0.0
            adlib_duration = 0.0
            cue_analyses = []
            
            for cue_data in cue_blocks:
                analysis = estimator._analyze_cue_block(cue_data)
                cue_analyses.append(analysis)
                
                if analysis.cue_type == "SOT" and self.settings.include_sots:
                    if analysis.calculated_duration:
                        sot_duration += estimator._parse_duration_to_seconds(analysis.calculated_duration)
                
                elif analysis.cue_type == "FSQ" and self.settings.include_fsqs:
                    if analysis.calculated_duration:
                        fsq_duration += estimator._parse_duration_to_seconds(analysis.calculated_duration)
                
                elif analysis.cue_type == "ADLIB" and self.settings.include_adlibs:
                    if analysis.calculated_duration:
                        adlib_duration += estimator._parse_duration_to_seconds(analysis.calculated_duration)
            
            # Calculate total duration
            total_seconds = speech_duration + sot_duration + fsq_duration + adlib_duration
            total_duration_formatted = estimator._seconds_to_duration_string(total_seconds)
            
            # Update file if requested
            if update_file:
                updated_content = estimator._update_segment_duration(content, total_duration_formatted, cue_analyses)
                FileManager.write_file(segment_file, updated_content)
            
            # Show breakdown
            cue_summary = []
            if sot_duration > 0:
                cue_summary.append(f"SOT: {estimator._seconds_to_duration_string(sot_duration)}")
            if fsq_duration > 0:
                cue_summary.append(f"FSQ: {estimator._seconds_to_duration_string(fsq_duration)}")
            if adlib_duration > 0:
                cue_summary.append(f"ADLIB: {estimator._seconds_to_duration_string(adlib_duration)}")
            
            cue_info = f" ({', '.join(cue_summary)})" if cue_summary else ""
            print(f"✓ {segment_file.name}: {total_duration_formatted} [{speech_word_count} words{cue_info}]")
            return total_seconds
            
        except Exception as e:
            print(f"✗ Error calculating duration for {segment_file.name}: {e}")
            return 0.0
    
    def process_single_segment(self, asset_id: str) -> bool:
        """Process a single segment by AssetID."""
        print(f"🎯 Processing segment: {asset_id}")
        
        segment_info = self.find_segment_by_assetid(asset_id)
        if not segment_info:
            print(f"✗ Segment with AssetID {asset_id} not found")
            return False
        
        segment_file = segment_info['file_path']
        episode_number = segment_info['episode_number']
        
        print(f"📁 Segment file: {segment_file.name}")
        print(f"📺 Episode: {episode_number}")
        print("")
        
        # Calculate segment duration
        segment_duration = self.calculate_segment_duration(segment_file, update_file=True)
        
        if segment_duration > 0:
            print("")
            # Update episode total
            self.update_episode_total_duration(episode_number)
            print(f"✅ Segment {asset_id} processed successfully")
            return True
        else:
            print(f"✗ Failed to calculate duration for segment {asset_id}")
            return False
    
    def process_episode(self, episode_number: str) -> bool:
        """Process all segments in an episode."""
        # Normalize episode number to 4 digits if needed
        if len(episode_number) < 4:
            episode_number = episode_number.zfill(4)
        
        episode_path = self.episodes_root / episode_number
        rundown_path = episode_path / "rundown"
        
        if not episode_path.exists():
            print(f"✗ Episode {episode_number} not found at {episode_path}")
            return False
            
        if not rundown_path.exists():
            print(f"✗ Episode {episode_number} rundown not found at {rundown_path}")
            return False
        
        print(f"📺 Processing episode {episode_number}")
        print(f"📁 Rundown path: {rundown_path}")
        
        segment_files = list(rundown_path.glob("*.md"))
        if not segment_files:
            print(f"✗ No segment files found in {rundown_path}")
            return False
        
        print(f"📝 Found {len(segment_files)} segments")
        print("")
        
        total_episode_duration = 0.0
        processed_count = 0
        
        # Process each segment
        for segment_file in sorted(segment_files):
            segment_duration = self.calculate_segment_duration(segment_file, update_file=True)
            total_episode_duration += segment_duration
            if segment_duration > 0:
                processed_count += 1
        
        print("")
        
        # Update episode total duration
        if processed_count > 0:
            self.update_episode_total_duration(episode_number, total_episode_duration)
            
            total_formatted = self._seconds_to_duration_string(total_episode_duration)
            print(f"📊 Episode {episode_number} Summary:")
            print(f"   Segments processed: {processed_count}/{len(segment_files)}")
            print(f"   Total duration: {total_formatted}")
            print(f"✅ Episode {episode_number} processed successfully")
            return True
        else:
            print(f"✗ No segments were successfully processed in episode {episode_number}")
            return False
    
    def update_episode_total_duration(self, episode_number: str, total_duration_seconds: Optional[float] = None):
        """Update episode info.md with total duration."""
        episode_path = self.episodes_root / episode_number
        info_file = episode_path / "info.md"
        
        if not info_file.exists():
            print(f"⚠️  Episode info.md not found: {info_file}")
            return
        
        try:
            # If total duration not provided, calculate from all segments
            if total_duration_seconds is None:
                total_duration_seconds = self._calculate_episode_total_from_segments(episode_number)
            
            total_duration_formatted = self._seconds_to_duration_string(total_duration_seconds)
            
            # Read current content
            content = FileManager.read_file(info_file)
            
            # Update duration in frontmatter
            updated_content = self._update_episode_duration_in_frontmatter(content, total_duration_formatted)
            
            # Write back to file
            FileManager.write_file(info_file, updated_content)
            
            print(f"📝 Updated episode {episode_number} total duration: {total_duration_formatted}")
            
        except Exception as e:
            print(f"✗ Error updating episode total duration: {e}")
    
    def _calculate_episode_total_from_segments(self, episode_number: str) -> float:
        """Calculate total episode duration by reading all segment durations."""
        episode_path = self.episodes_root / episode_number
        rundown_path = episode_path / "rundown"
        
        total_seconds = 0.0
        
        if rundown_path.exists():
            for segment_file in rundown_path.glob("*.md"):
                try:
                    content = FileManager.read_file(segment_file)
                    duration_str = self._extract_duration_from_frontmatter(content)
                    if duration_str:
                        total_seconds += self._parse_duration_to_seconds(duration_str)
                except Exception as e:
                    print(f"⚠️  Error reading duration from {segment_file.name}: {e}")
        
        return total_seconds
    
    def _extract_duration_from_frontmatter(self, content: str) -> Optional[str]:
        """Extract duration field from YAML frontmatter."""
        frontmatter, _, _ = FileManager.extract_frontmatter(content)
        if not frontmatter:
            return None
        
        match = re.search(r'^duration:\s*(.+)$', frontmatter, re.MULTILINE)
        if match:
            return match.group(1).strip().strip('"\'')
        return None
    
    def _update_episode_duration_in_frontmatter(self, content: str, new_duration: str) -> str:
        """Update duration field in episode info.md frontmatter."""
        lines = content.split('\n')
        updated_lines = []
        in_frontmatter = False
        duration_updated = False
        
        for i, line in enumerate(lines):
            if line.strip() == '---':
                updated_lines.append(line)
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    in_frontmatter = False
                    # Add duration if not found
                    if not duration_updated:
                        updated_lines.insert(-1, f"total_runtime: {new_duration}")
                        duration_updated = True
                continue
            
            if in_frontmatter:
                # Update existing duration field (handle both total_runtime and duration)
                if line.strip().startswith('total_runtime:') or line.strip().startswith('duration:'):
                    updated_lines.append(f"total_runtime: {new_duration}")
                    duration_updated = True
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        return '\n'.join(updated_lines)
    
    def _parse_duration_to_seconds(self, duration_str: str) -> float:
        """Parse duration string to seconds."""
        if not duration_str:
            return 0.0
        
        parts = duration_str.split(':')
        try:
            if len(parts) == 4:  # HH:MM:SS:FF (timecode with frames)
                hours, minutes, seconds, frames = map(float, parts)
                # Assume 30 fps for frame conversion (standard for broadcast)
                frame_seconds = frames / 30.0
                return hours * 3600 + minutes * 60 + seconds + frame_seconds
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(float, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:  # MM:SS
                minutes, seconds = map(float, parts)
                return minutes * 60 + seconds
            else:  # Just seconds
                return float(parts[0])
        except ValueError:
            return 0.0
    
    def _seconds_to_duration_string(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS:MS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 100)  # Convert fractional seconds to centiseconds (00-99)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{milliseconds:02d}"


class FileDurationEstimator:
    """File-only version of DurationEstimator for script use."""
    
    def __init__(self, settings: DurationSettings):
        self.settings = settings
    
    def _parse_segment_content(self, content: str) -> tuple[str, List[Dict[str, Any]]]:
        """Parse segment content into body text and cue blocks."""
        lines = content.split('\n')
        
        # Skip frontmatter
        in_frontmatter = False
        body_lines = []
        cue_blocks = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Handle frontmatter
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    in_frontmatter = False
                i += 1
                continue
            
            if in_frontmatter:
                i += 1
                continue
            
            # Check for cue block start
            if '<!-- Begin Cue -->' in line:
                # Extract cue block
                cue_lines = [line]
                i += 1
                
                while i < len(lines) and '<!-- End Cue -->' not in lines[i]:
                    cue_lines.append(lines[i])
                    i += 1
                
                if i < len(lines):
                    cue_lines.append(lines[i])  # Include end comment
                
                # Parse cue block
                cue_data = self._parse_cue_block('\n'.join(cue_lines))
                if cue_data:
                    cue_blocks.append(cue_data)
                
                i += 1
                continue
            
            # Regular body content
            body_lines.append(line)
            i += 1
        
        body_content = '\n'.join(body_lines)
        return body_content, cue_blocks
    
    def _parse_cue_block(self, cue_text: str) -> Optional[Dict[str, Any]]:
        """Parse a cue block and extract field data."""
        cue_data = {}
        
        for line in cue_text.split('\n'):
            line = line.strip()
            # Match [Field: Value] pattern
            field_match = re.match(r'^\[([^:]+):\s*(.*)\]$', line)
            if field_match:
                field_name = field_match.group(1).strip()
                field_value = field_match.group(2).strip()
                
                # Check if this is a combined Type field with Duration (e.g., "ADLIB, Duration: 00:01:00")
                if field_name.lower() == 'type' and ', Duration:' in field_value:
                    parts = field_value.split(', Duration:')
                    cue_data['type'] = parts[0].strip()
                    cue_data['duration'] = parts[1].strip()
                # Map common field names
                elif field_name.lower() == 'type':
                    cue_data['type'] = field_value
                elif field_name.lower() == 'assetid':
                    cue_data['AssetID'] = field_value
                elif field_name.lower() == 'duration':
                    cue_data['duration'] = field_value
                elif field_name.lower() == 'quote':
                    cue_data['quote'] = field_value
                elif field_name.lower() == 'slug':
                    cue_data['slug'] = field_value
                else:
                    cue_data[field_name.lower()] = field_value
        
        return cue_data if cue_data else None
    
    def _analyze_cue_block(self, cue_data: Dict[str, Any]) -> CueAnalysis:
        """Analyze a single cue block and calculate its duration."""
        cue_type = cue_data.get('type', 'UNKNOWN')
        original_duration = cue_data.get('duration')
        calculated_duration = None
        
        if cue_type == "SOT":
            calculated_duration = original_duration or "00:00:30"  # Default 30 seconds
        
        elif cue_type == "FSQ":
            quote_text = cue_data.get('quote', '')
            if quote_text:
                word_count = self._count_words(quote_text)
                duration_seconds = word_count / self.settings.fsq_wpm * 60
                calculated_duration = self._seconds_to_duration_string(duration_seconds)
            else:
                calculated_duration = "00:00:10"  # Default for empty quotes
        
        elif cue_type == "ADLIB":
            calculated_duration = original_duration or "00:01:00"  # Default 1 minute
        
        return CueAnalysis(cue_type, calculated_duration)
    
    def _count_words(self, text: str) -> int:
        """Count words in text, excluding markdown formatting."""
        if not text:
            return 0
        
        # Remove markdown formatting
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # headers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)        # *italic*
        text = re.sub(r'__([^_]+)__', r'\1', text)          # __bold__
        text = re.sub(r'_([^_]+)_', r'\1', text)            # _italic*
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text) # links
        text = re.sub(r'<[^>]+>', '', text)  # HTML tags
        
        words = text.split()
        return len(words)
    
    def _parse_duration_to_seconds(self, duration_str: str) -> float:
        """Parse duration string to seconds."""
        if not duration_str:
            return 0.0
        
        parts = duration_str.split(':')
        try:
            if len(parts) == 4:  # HH:MM:SS:FF (timecode with frames)
                hours, minutes, seconds, frames = map(float, parts)
                # Assume 30 fps for frame conversion (standard for broadcast)
                frame_seconds = frames / 30.0
                return hours * 3600 + minutes * 60 + seconds + frame_seconds
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(float, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:  # MM:SS
                minutes, seconds = map(float, parts)
                return minutes * 60 + seconds
            else:  # Just seconds
                return float(parts[0])
        except ValueError:
            return 0.0
    
    def _seconds_to_duration_string(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS:MS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 100)  # Convert fractional seconds to centiseconds (00-99)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{milliseconds:02d}"
    
    def _update_segment_duration(self, content: str, new_duration: str, cue_analyses: List[CueAnalysis]) -> str:
        """Update duration in frontmatter and FSQ durations in cue blocks."""
        lines = content.split('\n')
        updated_lines = []
        in_frontmatter = False
        duration_updated = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Handle frontmatter
            if line.strip() == '---':
                updated_lines.append(line)
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    in_frontmatter = False
                    # Add duration if not found
                    if not duration_updated:
                        updated_lines.insert(-1, f"duration: {new_duration}")
                        duration_updated = True
                i += 1
                continue
            
            if in_frontmatter:
                # Update duration field
                if line.strip().startswith('duration:'):
                    updated_lines.append(f"duration: {new_duration}")
                    duration_updated = True
                else:
                    updated_lines.append(line)
                i += 1
                continue
            
            # Handle cue blocks - update FSQ durations
            if '<!-- Begin Cue -->' in line:
                cue_start = i
                cue_lines = [line]
                i += 1
                
                while i < len(lines) and '<!-- End Cue -->' not in lines[i]:
                    cue_lines.append(lines[i])
                    i += 1
                
                if i < len(lines):
                    cue_lines.append(lines[i])  # Include end comment
                
                # Update FSQ duration if applicable
                updated_cue_lines = self._update_cue_block_duration(cue_lines, cue_analyses)
                updated_lines.extend(updated_cue_lines)
                
                i += 1
                continue
            
            # Regular content
            updated_lines.append(line)
            i += 1
        
        return '\n'.join(updated_lines)
    
    def _update_cue_block_duration(self, cue_lines: List[str], cue_analyses: List[CueAnalysis]) -> List[str]:
        """Update duration field in FSQ cue blocks."""
        # Extract cue type to find matching analysis
        cue_type = None
        quote_text = None
        
        for line in cue_lines:
            type_match = re.search(r'^\[Type:\s*(.+)\]$', line.strip())
            if type_match:
                cue_type = type_match.group(1).strip()
            
            quote_match = re.search(r'^\[Quote:\s*(.*)\]$', line.strip())
            if quote_match:
                quote_text = quote_match.group(1).strip()
        
        # Find matching analysis for FSQ cues
        if cue_type == "FSQ":
            # Calculate duration from quote if available
            calculated_duration = None
            if quote_text:
                word_count = self._count_words(quote_text)
                duration_seconds = word_count / self.settings.fsq_wpm * 60
                calculated_duration = self._seconds_to_duration_string(duration_seconds)
            else:
                calculated_duration = "00:00:10"  # Default for empty quotes
            
            if calculated_duration:
                updated_lines = []
                duration_updated = False
                
                for line in cue_lines:
                    if re.match(r'^\[Duration:\s*.*\]$', line.strip()):
                        updated_lines.append(f"[Duration: {calculated_duration}]")
                        duration_updated = True
                    else:
                        updated_lines.append(line)
                
                # Add duration field if not found
                if not duration_updated and cue_type == "FSQ":
                    # Insert before the end comment
                    for i, line in enumerate(updated_lines):
                        if '<!-- End Cue -->' in line:
                            updated_lines.insert(i, f"[Duration: {calculated_duration}]")
                            break
                
                return updated_lines
        
        return cue_lines


def main():
    parser = argparse.ArgumentParser(
        description="Calculate segment durations and update episode totals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python duration_calculator.py --segment=SEGMEEJ44L61P9LZV
  python duration_calculator.py --episode=0236
  python duration_calculator.py --episode=236  # Auto-pads to 0236

Path Configuration:
  Uses Show-Build centralized path system
  Episodes directory: /mnt/sync/disaffected/episodes
  Automatically detects Docker vs development environments
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--segment',
        type=str,
        help='Process single segment by AssetID (e.g., SEGMEEJ44L61P9LZV)'
    )
    group.add_argument(
        '--episode',
        type=str,
        help='Process all segments in episode (e.g., 0236 or 236)'
    )
    
    args = parser.parse_args()
    
    print("🎬 Show-Build Duration Calculator")
    print("=" * 60)
    print(f"📁 Episodes path: {EPISODES_ROOT}")
    print(f"🔧 Tools path: {tools_dir}")
    print("")
    
    calculator = EpisodeDurationCalculator()
    
    try:
        if args.segment:
            success = calculator.process_single_segment(args.segment)
        elif args.episode:
            success = calculator.process_episode(args.episode)
        else:
            print("✗ No segment or episode specified")
            sys.exit(1)
        
        if success:
            print("\n🎉 Duration calculation completed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Duration calculation failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()