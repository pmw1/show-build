#!/usr/bin/env python3
"""
Episode Cleanup Tool - Show-Build Tools Suite

Performs comprehensive cleanup and validation of episode rundown files.
Checks frontmatter consistency, file naming conventions, and content standards.

Usage:
    python episode-cleanup.py --episode=0236
    python episode-cleanup.py --episode=0236 --fix
"""

import argparse
import sys
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from datetime import datetime

# Add both tools and app directories to Python path
tools_dir = Path(__file__).parent
sys.path.insert(0, str(tools_dir))
sys.path.insert(0, str(tools_dir.parent / 'app'))

# Import from centralized paths system
try:
    from core.paths import ShowBuildPaths
    path_manager = ShowBuildPaths()
    EPISODES_ROOT = path_manager.episodes_root
except ImportError:
    # Fallback to direct path
    EPISODES_ROOT = Path("/mnt/sync/disaffected/episodes")


class CleanupIssue:
    """Represents a cleanup issue found in episode files."""
    
    def __init__(self, issue_type: str, file_path: Path, description: str, severity: str = "WARNING"):
        self.issue_type = issue_type
        self.file_path = file_path
        self.description = description
        self.severity = severity
        self.timestamp = datetime.now().isoformat()
    
    def __str__(self):
        return f"[{self.severity}] {self.issue_type}: {self.file_path.name} - {self.description}"
    
    def to_log_entry(self):
        return f"{self.timestamp} | {self.severity} | {self.issue_type} | {self.file_path} | {self.description}"


class SegmentData:
    """Data extracted from a segment file."""
    
    def __init__(self, file_path: Path, frontmatter: Dict[str, str]):
        self.file_path = file_path
        self.frontmatter = frontmatter
        self.filename_order = self._extract_filename_order()
        
    def _extract_filename_order(self) -> Optional[str]:
        """Extract order number from filename."""
        match = re.match(r'^(\d+)', self.file_path.stem)
        return match.group(1) if match else None


class EpisodeCleanup:
    """Main cleanup engine for episode validation and fixing."""
    
    def __init__(self, episode_number: str, fix_issues: bool = False, auto_confirm: bool = False, skip_cue_validation: bool = False):
        self.episode_number = episode_number
        self.fix_issues = fix_issues
        self.auto_confirm = auto_confirm
        self.skip_cue_validation = skip_cue_validation
        self.episodes_root = EPISODES_ROOT
        self.issues: List[CleanupIssue] = []
        self.fixes_applied = 0
        
        # Title case exceptions (articles, prepositions, conjunctions under 5 letters)
        self.title_case_exceptions = {
            'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'if', 'in', 
            'nor', 'of', 'on', 'or', 'so', 'the', 'to', 'up', 'yet', 'vs'
        }
        
        # Duration limits (in seconds)
        self.min_episode_duration = 5 * 60   # 5 minutes
        self.max_episode_duration = 4 * 60 * 60  # 4 hours
        self.min_segment_duration = 10  # 10 seconds
        self.max_segment_duration = 2 * 60 * 60  # 2 hours
    
    def run_cleanup(self) -> bool:
        """Run the complete cleanup process."""
        episode_path = self.episodes_root / self.episode_number
        rundown_path = episode_path / "rundown"
        
        if not self._validate_episode_path(episode_path, rundown_path):
            return False
        
        print(f"🧹 Episode Cleanup: {self.episode_number}")
        print(f"📁 Rundown path: {rundown_path}")
        print()
        
        # STEP 1: Episode-level validation (critical checks first)
        episode_info = self._get_episode_info(episode_path)
        if not self._validate_episode_info(episode_path, episode_info):
            print("❌ Episode-level validation failed. Cannot continue.")
            return False
        
        # Get all segment files
        segment_files = list(rundown_path.glob("*.md"))
        segments = self._parse_all_segments(segment_files)
        
        print(f"📝 Found {len(segments)} segment files")
        print()
        
        # STEP 2: Segment-level validation checks
        self._check_system_messages(segments)
        self._check_filename_order_mismatch(segments)
        self._check_duplicate_orders(segments)
        self._check_zero_durations(segments)
        self._check_title_case(segments)
        self._check_airdate_format(segments)
        self._check_airdate_consistency(segments, episode_info.get('airdate'))
        
        # STEP 3: Enhanced validation checks
        self._check_segment_assetids(segments)
        self._check_file_content(segments)
        self._check_duration_consistency(segments, episode_info)
        self._check_segment_titles(segments)
        self._check_filename_casing(segments)
        self._check_cue_block_whitespace(segments)
        if not self.skip_cue_validation:
            self._check_cue_blocks(segments)
        
        # Apply fixes if requested
        if self.fix_issues:
            self._apply_fixes()
        
        # Write log file
        self._write_cleanup_log()
        
        # Print summary
        self._print_summary()
        
        return True
    
    def _validate_episode_path(self, episode_path: Path, rundown_path: Path) -> bool:
        """Validate episode and rundown paths exist."""
        if not episode_path.exists():
            print(f"❌ Episode directory not found: {episode_path}")
            return False
        
        if not rundown_path.exists():
            print(f"❌ Rundown directory not found: {rundown_path}")
            return False
        
        return True
    
    def _get_episode_info(self, episode_path: Path) -> Dict[str, str]:
        """Get complete episode info from info.md file."""
        info_file = episode_path / "info.md"
        if not info_file.exists():
            return {}
        
        try:
            content = info_file.read_text(encoding='utf-8')
            return self._extract_frontmatter(content) or {}
        except Exception:
            return {}
    
    def _validate_episode_info(self, episode_path: Path, episode_info: Dict[str, str]) -> bool:
        """Validate critical episode-level frontmatter fields."""
        print("🔍 Validating episode-level info.md...")
        
        # Check AssetID exists and is valid
        episode_asset_id = episode_info.get('AssetID', '').strip()
        if not episode_asset_id:
            self.issues.append(CleanupIssue(
                "EPISODE_MISSING_ASSETID", episode_path / "info.md",
                "Episode AssetID is missing", "ERROR"
            ))
            print("❌ HARD FAIL: Episode AssetID is missing")
            return False
        
        # TODO: Validate AssetID exists in database
        # For now, just check format
        if not re.match(r'^[A-Z0-9]{17}$', episode_asset_id):
            self.issues.append(CleanupIssue(
                "EPISODE_INVALID_ASSETID", episode_path / "info.md",
                f"Episode AssetID '{episode_asset_id}' has invalid format", "ERROR"
            ))
            print(f"❌ HARD FAIL: Episode AssetID '{episode_asset_id}' has invalid format")
            return False
        
        # Check status - note if not "production" (don't stop the train)
        episode_status = episode_info.get('status', '').strip()
        if episode_status != 'production':
            print(f"📋 NOTE: Episode status is '{episode_status}' (not production-ready)")
            self.issues.append(CleanupIssue(
                "EPISODE_NOT_PRODUCTION_READY", episode_path / "info.md",
                f"Episode status is '{episode_status}' (not production-ready)", "INFO"
            ))
        
        # Check type exists
        episode_type = episode_info.get('type', '').strip()
        if not episode_type:
            print("⚠️  Episode type is not set")
            if not self.auto_confirm:
                try:
                    response = input("Show type not set. Is this the sunday_show? (y/N): ")
                    if response.lower() in ['y', 'yes']:
                        self._update_episode_type(episode_path, 'sunday_show')
                        episode_type = 'sunday_show'
                        print("✅ Updated episode type to 'sunday_show'")
                    else:
                        self.issues.append(CleanupIssue(
                            "EPISODE_MISSING_TYPE", episode_path / "info.md",
                            "Episode type is not set", "WARNING"
                        ))
                except EOFError:
                    self.issues.append(CleanupIssue(
                        "EPISODE_MISSING_TYPE", episode_path / "info.md",
                        "Episode type is not set (non-interactive)", "WARNING"
                    ))
            else:
                self.issues.append(CleanupIssue(
                    "EPISODE_MISSING_TYPE", episode_path / "info.md",
                    "Episode type is not set", "WARNING"
                ))
        
        # If type is sunday_show, check airdate is a Sunday
        episode_airdate = episode_info.get('airdate', '').strip().strip('"')
        if episode_type == 'sunday_show' and episode_airdate:
            if not self._is_sunday(episode_airdate):
                self.issues.append(CleanupIssue(
                    "SUNDAY_SHOW_NOT_SUNDAY", episode_path / "info.md",
                    f"Episode type is 'sunday_show' but airdate '{episode_airdate}' is not a Sunday", "ERROR"
                ))
                print(f"⚠️  Sunday show airdate '{episode_airdate}' is not a Sunday")
        
        # Check duration exists and is not zero
        episode_duration = episode_info.get('duration', '').strip()
        if not episode_duration:
            self.issues.append(CleanupIssue(
                "EPISODE_MISSING_DURATION", episode_path / "info.md",
                "Episode duration is missing", "ERROR"
            ))
            print("❌ HARD FAIL: Episode duration is missing")
            return False
        elif episode_duration in ['00:00', '00:00:00', '0']:
            self.issues.append(CleanupIssue(
                "EPISODE_ZERO_DURATION", episode_path / "info.md",
                f"Episode duration is zero: '{episode_duration}'", "ERROR"
            ))
            print(f"❌ HARD FAIL: Episode duration is zero: '{episode_duration}'")
            return False
        
        print("✅ Episode-level validation passed")
        return True
    
    def _is_sunday(self, date_str: str) -> bool:
        """Check if a date string (YYYY-MM-DD) falls on a Sunday."""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.weekday() == 6  # Sunday = 6
        except ValueError:
            return False
    
    def _update_episode_status(self, episode_path: Path, new_status: str):
        """Update episode status in info.md."""
        info_file = episode_path / "info.md"
        try:
            content = info_file.read_text(encoding='utf-8')
            updated_content = self._update_frontmatter_field(content, 'status', new_status)
            info_file.write_text(updated_content, encoding='utf-8')
        except Exception as e:
            print(f"❌ Failed to update episode status: {e}")
    
    def _update_episode_type(self, episode_path: Path, new_type: str):
        """Update episode type in info.md."""
        info_file = episode_path / "info.md"
        try:
            content = info_file.read_text(encoding='utf-8')
            updated_content = self._update_frontmatter_field(content, 'type', new_type)
            info_file.write_text(updated_content, encoding='utf-8')
        except Exception as e:
            print(f"❌ Failed to update episode type: {e}")
    
    def _update_frontmatter_field(self, content: str, field_name: str, new_value: str) -> str:
        """Update a specific field in YAML frontmatter."""
        lines = content.split('\n')
        updated_lines = []
        field_updated = False
        in_frontmatter = False
        
        for line in lines:
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    in_frontmatter = False
                    if not field_updated:
                        # Add field before closing ---
                        updated_lines.append(f'{field_name}: {new_value}')
                        field_updated = True
                updated_lines.append(line)
                continue
            
            if in_frontmatter:
                field_match = re.match(rf'^(\s*{field_name}:\s*)(.*?)(\s*)$', line)
                if field_match:
                    indent = field_match.group(1)
                    trailing_space = field_match.group(3)
                    updated_lines.append(f'{field_name}: {new_value}{trailing_space}')
                    field_updated = True
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        return '\n'.join(updated_lines)
    
    def _parse_all_segments(self, segment_files: List[Path]) -> List[SegmentData]:
        """Parse all segment files and extract frontmatter."""
        segments = []
        
        for segment_file in segment_files:
            try:
                content = segment_file.read_text(encoding='utf-8')
                frontmatter = self._extract_frontmatter(content)
                if frontmatter:
                    segments.append(SegmentData(segment_file, frontmatter))
            except Exception as e:
                self.issues.append(CleanupIssue(
                    "FILE_READ_ERROR", segment_file, 
                    f"Could not read file: {e}", "ERROR"
                ))
        
        return segments
    
    def _extract_frontmatter(self, content: str) -> Optional[Dict[str, str]]:
        """Extract YAML frontmatter from file content."""
        lines = content.split('\n')
        if not lines or lines[0].strip() != '---':
            return None
        
        frontmatter = {}
        in_frontmatter = False
        
        for line in lines[1:]:
            if line.strip() == '---':
                break
            
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip()
        
        return frontmatter
    
    def _check_system_messages(self, segments: List[SegmentData]):
        """Check for system_message fields and mark for removal."""
        for segment in segments:
            if 'system_message' in segment.frontmatter:
                self.issues.append(CleanupIssue(
                    "SYSTEM_MESSAGE", segment.file_path,
                    "Contains system_message field that should be removed"
                ))
    
    def _check_filename_order_mismatch(self, segments: List[SegmentData]):
        """Check if filename prefix matches frontmatter order field."""
        for segment in segments:
            filename_order = segment.filename_order
            frontmatter_order = segment.frontmatter.get('order', '').strip('"')
            
            if filename_order and frontmatter_order:
                if filename_order != frontmatter_order:
                    self.issues.append(CleanupIssue(
                        "ORDER_MISMATCH", segment.file_path,
                        f"Filename order '{filename_order}' != frontmatter order '{frontmatter_order}'"
                    ))
            elif filename_order and not frontmatter_order:
                self.issues.append(CleanupIssue(
                    "MISSING_ORDER", segment.file_path,
                    f"Has filename order '{filename_order}' but no frontmatter order field"
                ))
            elif not filename_order and frontmatter_order:
                self.issues.append(CleanupIssue(
                    "MISSING_FILENAME_ORDER", segment.file_path,
                    f"Has frontmatter order '{frontmatter_order}' but no filename order prefix"
                ))
    
    def _check_duplicate_orders(self, segments: List[SegmentData]):
        """Check for duplicate order values."""
        order_map: Dict[str, List[Path]] = {}
        
        for segment in segments:
            order = segment.frontmatter.get('order', '').strip('"')
            if order:
                if order not in order_map:
                    order_map[order] = []
                order_map[order].append(segment.file_path)
        
        for order, files in order_map.items():
            if len(files) > 1:
                file_names = [f.name for f in files]
                self.issues.append(CleanupIssue(
                    "DUPLICATE_ORDER", files[0],  # Log against first file
                    f"Order '{order}' is duplicated in files: {', '.join(file_names)}"
                ))
    
    def _check_zero_durations(self, segments: List[SegmentData]):
        """Check for zero or missing durations."""
        for segment in segments:
            duration = segment.frontmatter.get('duration', '').strip()
            if not duration:
                self.issues.append(CleanupIssue(
                    "MISSING_DURATION", segment.file_path,
                    "No duration field found"
                ))
            elif duration in ['00:00', '00:00:00', '0']:
                self.issues.append(CleanupIssue(
                    "ZERO_DURATION", segment.file_path,
                    f"Duration is zero: '{duration}'"
                ))
    
    def _check_title_case(self, segments: List[SegmentData]):
        """Check for proper title case formatting."""
        for segment in segments:
            title = segment.frontmatter.get('title', '').strip()
            if title:
                proper_title = self._to_title_case(title)
                if title != proper_title:
                    self.issues.append(CleanupIssue(
                        "TITLE_CASE", segment.file_path,
                        f"Title case issue: '{title}' should be '{proper_title}'"
                    ))
    
    def _to_title_case(self, text: str) -> str:
        """Convert text to proper title case."""
        words = text.split()
        title_words = []
        
        for i, word in enumerate(words):
            # Always capitalize first and last word
            if i == 0 or i == len(words) - 1:
                title_words.append(word.capitalize())
            # Check if word is in exceptions list
            elif word.lower() in self.title_case_exceptions:
                title_words.append(word.lower())
            # Capitalize all other words
            else:
                title_words.append(word.capitalize())
        
        return ' '.join(title_words)
    
    def _check_airdate_format(self, segments: List[SegmentData]):
        """Check airdate format (YYYY-MM-DD)."""
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        
        for segment in segments:
            airdate = segment.frontmatter.get('airdate', '').strip()
            if not airdate:
                self.issues.append(CleanupIssue(
                    "MISSING_AIRDATE", segment.file_path,
                    "No airdate field found"
                ))
            elif not date_pattern.match(airdate):
                self.issues.append(CleanupIssue(
                    "INVALID_AIRDATE_FORMAT", segment.file_path,
                    f"Airdate '{airdate}' is not in YYYY-MM-DD format"
                ))
    
    def _check_airdate_consistency(self, segments: List[SegmentData], episode_airdate: Optional[str]):
        """Check if segment airdates match episode airdate."""
        if not episode_airdate:
            return
        
        # Clean episode airdate (remove quotes)
        clean_episode_airdate = episode_airdate.strip('"')
        
        for segment in segments:
            segment_airdate = segment.frontmatter.get('airdate', '').strip().strip('"')
            if segment_airdate and segment_airdate != clean_episode_airdate:
                self.issues.append(CleanupIssue(
                    "AIRDATE_MISMATCH", segment.file_path,
                    f"Segment airdate '{segment_airdate}' != episode airdate '{clean_episode_airdate}'"
                ))
    
    def _check_segment_assetids(self, segments: List[SegmentData]):
        """Check segment AssetIDs for format and existence."""
        for segment in segments:
            asset_id = segment.frontmatter.get('AssetID', '').strip()
            if not asset_id:
                self.issues.append(CleanupIssue(
                    "MISSING_SEGMENT_ASSETID", segment.file_path,
                    "Segment AssetID is missing"
                ))
            elif not re.match(r'^[A-Z0-9]{17}$', asset_id):
                self.issues.append(CleanupIssue(
                    "INVALID_SEGMENT_ASSETID", segment.file_path,
                    f"Segment AssetID '{asset_id}' has invalid format"
                ))
            # TODO: Add database validation when available
    
    def _check_file_content(self, segments: List[SegmentData]):
        """Check that markdown files have actual content."""
        for segment in segments:
            try:
                content = segment.file_path.read_text(encoding='utf-8')
                # Split by frontmatter
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    body_content = parts[2].strip()
                else:
                    body_content = content.strip()
                
                # Remove common empty sections
                body_content = re.sub(r'^##\s*(Notes|Description|Script)\s*$', '', body_content, flags=re.MULTILINE)
                body_content = body_content.strip()
                
                if not body_content:
                    self.issues.append(CleanupIssue(
                        "EMPTY_CONTENT", segment.file_path,
                        "Segment file has no content beyond frontmatter"
                    ))
                elif len(body_content) < 50:  # Very short content
                    self.issues.append(CleanupIssue(
                        "MINIMAL_CONTENT", segment.file_path,
                        f"Segment has very little content ({len(body_content)} characters)"
                    ))
            except Exception as e:
                self.issues.append(CleanupIssue(
                    "CONTENT_READ_ERROR", segment.file_path,
                    f"Could not read file content: {e}", "ERROR"
                ))
    
    def _check_duration_consistency(self, segments: List[SegmentData], episode_info: Dict[str, str]):
        """Check duration consistency and reasonableness."""
        episode_duration_str = episode_info.get('duration', '').strip()
        if not episode_duration_str:
            return
        
        try:
            episode_duration_seconds = self._parse_duration_to_seconds(episode_duration_str)
            
            # Check episode duration reasonableness
            if episode_duration_seconds < self.min_episode_duration:
                self.issues.append(CleanupIssue(
                    "EPISODE_TOO_SHORT", Path(f"episodes/{self.episode_number}/info.md"),
                    f"Episode duration {episode_duration_str} is suspiciously short (< 5 min)"
                ))
            elif episode_duration_seconds > self.max_episode_duration:
                self.issues.append(CleanupIssue(
                    "EPISODE_TOO_LONG", Path(f"episodes/{self.episode_number}/info.md"),
                    f"Episode duration {episode_duration_str} is suspiciously long (> 4 hours)"
                ))
            
            # Calculate total segment durations
            total_segment_duration = 0
            valid_segments = 0
            
            for segment in segments:
                segment_duration_str = segment.frontmatter.get('duration', '').strip()
                if segment_duration_str and segment_duration_str not in ['00:00', '00:00:00', '0']:
                    try:
                        segment_duration_seconds = self._parse_duration_to_seconds(segment_duration_str)
                        
                        # Check segment duration reasonableness
                        if segment_duration_seconds < self.min_segment_duration:
                            self.issues.append(CleanupIssue(
                                "SEGMENT_TOO_SHORT", segment.file_path,
                                f"Segment duration {segment_duration_str} is suspiciously short (< 10 sec)"
                            ))
                        elif segment_duration_seconds > self.max_segment_duration:
                            self.issues.append(CleanupIssue(
                                "SEGMENT_TOO_LONG", segment.file_path,
                                f"Segment duration {segment_duration_str} is suspiciously long (> 2 hours)"
                            ))
                        
                        total_segment_duration += segment_duration_seconds
                        valid_segments += 1
                    except:
                        pass
            
            if valid_segments > 0:
                # Compare episode vs segment total (allow 10% variance)
                variance = abs(episode_duration_seconds - total_segment_duration)
                if variance > (episode_duration_seconds * 0.1):
                    episode_formatted = self._seconds_to_duration_string(episode_duration_seconds)
                    segments_formatted = self._seconds_to_duration_string(total_segment_duration)
                    self.issues.append(CleanupIssue(
                        "DURATION_MISMATCH", Path(f"episodes/{self.episode_number}/info.md"),
                        f"Episode duration ({episode_formatted}) vs segment total ({segments_formatted}) mismatch"
                    ))
        
        except Exception as e:
            self.issues.append(CleanupIssue(
                "DURATION_PARSE_ERROR", Path(f"episodes/{self.episode_number}/info.md"),
                f"Could not parse episode duration '{episode_duration_str}': {e}"
            ))
    
    def _check_segment_titles(self, segments: List[SegmentData]):
        """Check segment titles are lowercase with numerical prefix stripped."""
        for segment in segments:
            title = segment.frontmatter.get('title', '').strip()
            if not title:
                continue  # Skip empty titles (handled elsewhere)
            
            # Check if title has numerical prefix that should be stripped
            match = re.match(r'^(\d+\s*)(.*)', title)
            if match:
                prefix = match.group(1)
                rest = match.group(2).strip()
                
                # Title should be just the content without prefix, in lowercase
                if title != rest.lower():
                    proper_title = rest.lower()
                    self.issues.append(CleanupIssue(
                        "TITLE_NOT_LOWERCASE", segment.file_path,
                        f"Title should be lowercase without prefix: '{title}' -> '{proper_title}'"
                    ))
            else:
                # No numerical prefix found, just check if it's lowercase
                if title != title.lower():
                    self.issues.append(CleanupIssue(
                        "TITLE_NOT_LOWERCASE", segment.file_path,
                        f"Title should be lowercase: '{title}' -> '{title.lower()}'"
                    ))
    
    def _check_filename_casing(self, segments: List[SegmentData]):
        """Check that filenames are all lowercase."""
        for segment in segments:
            filename = segment.file_path.name
            filename_lower = filename.lower()
            
            if filename != filename_lower:
                self.issues.append(CleanupIssue(
                    "FILENAME_NOT_LOWERCASE", segment.file_path,
                    f"Filename should be lowercase: '{filename}' -> '{filename_lower}'"
                ))
    
    def _check_cue_block_whitespace(self, segments: List[SegmentData]):
        """Check for proper whitespace around cue blocks."""
        for segment in segments:
            try:
                content = segment.file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    # Check for text immediately following <!-- End Cue --> 
                    if '<!-- End Cue -->' in line and not line.strip().endswith('<!-- End Cue -->'):
                        # Text appears on same line as End Cue
                        self.issues.append(CleanupIssue(
                            "CUE_BLOCK_WHITESPACE", segment.file_path,
                            f"Line {i+1}: Text should not appear on same line as '<!-- End Cue -->'"
                        ))
                    
                    # Check for missing blank line after <!-- End Cue -->
                    elif line.strip() == '<!-- End Cue -->':
                        if i + 1 < len(lines) and lines[i + 1].strip() != '':
                            # Next line has content, should have blank line in between
                            self.issues.append(CleanupIssue(
                                "CUE_BLOCK_WHITESPACE", segment.file_path,
                                f"Line {i+1}: Missing blank line after '<!-- End Cue -->'"
                            ))
                    
                    # Check for missing blank line before <!-- Begin Cue -->
                    elif line.strip() == '<!-- Begin Cue -->':
                        if i > 0 and lines[i - 1].strip() != '':
                            # Previous line has content, should have blank line in between
                            self.issues.append(CleanupIssue(
                                "CUE_BLOCK_WHITESPACE", segment.file_path,
                                f"Line {i+1}: Missing blank line before '<!-- Begin Cue -->'"
                            ))
                            
            except Exception as e:
                self.issues.append(CleanupIssue(
                    "FILE_READ_ERROR", segment.file_path,
                    f"Could not read file for whitespace check: {e}"
                ))
    
    def _check_cue_blocks(self, segments: List[SegmentData]):
        """Check cue blocks for proper formatting and valid AssetIDs."""
        for segment in segments:
            try:
                content = segment.file_path.read_text(encoding='utf-8')
                cue_blocks = self._extract_cue_blocks(content)
                
                for cue_block in cue_blocks:
                    self._validate_cue_block(segment.file_path, cue_block)
                    
            except Exception as e:
                self.issues.append(CleanupIssue(
                    "CUE_BLOCK_READ_ERROR", segment.file_path,
                    f"Could not read cue blocks: {e}", "ERROR"
                ))
    
    def _extract_cue_blocks(self, content: str) -> List[Dict[str, str]]:
        """Extract all cue blocks from content."""
        cue_blocks = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if '<!-- Begin Cue -->' in line:
                cue_lines = []
                i += 1
                
                # Collect cue block lines
                while i < len(lines) and '<!-- End Cue -->' not in lines[i]:
                    cue_lines.append(lines[i])
                    i += 1
                
                if i < len(lines):
                    # Parse cue block fields
                    cue_data = {}
                    for cue_line in cue_lines:
                        cue_line = cue_line.strip()
                        field_match = re.match(r'^\[([^:]+):\s*(.*)\]$', cue_line)
                        if field_match:
                            field_name = field_match.group(1).strip()
                            field_value = field_match.group(2).strip()
                            cue_data[field_name] = field_value
                    
                    if cue_data:
                        cue_blocks.append(cue_data)
            
            i += 1
        
        return cue_blocks
    
    def _validate_cue_block(self, file_path: Path, cue_data: Dict[str, str]):
        """Validate a single cue block."""
        cue_type = cue_data.get('Type', '').strip()
        if not cue_type:
            self.issues.append(CleanupIssue(
                "CUE_MISSING_TYPE", file_path,
                "Cue block missing Type field"
            ))
            return
        
        # ADLIB cues don't need AssetIDs yet
        if cue_type != 'ADLIB':
            asset_id = cue_data.get('AssetID', '').strip()
            if not asset_id:
                self.issues.append(CleanupIssue(
                    "CUE_MISSING_ASSETID", file_path,
                    f"Cue block (type: {cue_type}) missing AssetID"
                ))
            elif not re.match(r'^[A-Z0-9]{17}$', asset_id):
                self.issues.append(CleanupIssue(
                    "CUE_INVALID_ASSETID", file_path,
                    f"Cue block AssetID '{asset_id}' has invalid format"
                ))
        
        # Type-specific validations
        if cue_type == 'FSQ':
            if not cue_data.get('Quote'):
                self.issues.append(CleanupIssue(
                    "FSQ_MISSING_QUOTE", file_path,
                    "FSQ cue block missing Quote field"
                ))
            if not cue_data.get('Attribution'):
                self.issues.append(CleanupIssue(
                    "FSQ_MISSING_ATTRIBUTION", file_path,
                    "FSQ cue block missing Attribution field"
                ))
        elif cue_type == 'SOT':
            if not cue_data.get('Duration'):
                self.issues.append(CleanupIssue(
                    "SOT_MISSING_DURATION", file_path,
                    "SOT cue block missing Duration field"
                ))
        elif cue_type == 'GFX':
            if not cue_data.get('MediaURL') and not cue_data.get('Description'):
                self.issues.append(CleanupIssue(
                    "GFX_MISSING_MEDIA", file_path,
                    "GFX cue block missing MediaURL or Description"
                ))
    
    def _parse_duration_to_seconds(self, duration_str: str) -> float:
        """Parse duration string to seconds."""
        if not duration_str:
            return 0.0
        
        # Handle HH:MM:SS or MM:SS format
        parts = duration_str.split(':')
        try:
            if len(parts) == 3:  # HH:MM:SS
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
        """Convert seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _apply_fixes(self):
        """Apply automatic fixes for certain issues."""
        print("🔧 Applying automatic fixes...")
        
        for issue in self.issues:
            if issue.issue_type == "SYSTEM_MESSAGE":
                if self._remove_system_message(issue.file_path):
                    self.fixes_applied += 1
                    print(f"✅ Fixed: Removed system_message from {issue.file_path.name}")
            
            elif issue.issue_type == "TITLE_CASE":
                if self._fix_title_case(issue.file_path):
                    self.fixes_applied += 1
                    print(f"✅ Fixed: Updated title case in {issue.file_path.name}")
            
            elif issue.issue_type == "TITLE_NOT_LOWERCASE":
                if self._fix_title_lowercase(issue.file_path):
                    self.fixes_applied += 1
                    print(f"✅ Fixed: Converted title to lowercase in {issue.file_path.name}")
            
            elif issue.issue_type == "TITLE_MISSING_NUMERIC_PREFIX":
                if self._fix_title_add_prefix(issue.file_path):
                    self.fixes_applied += 1
                    print(f"✅ Fixed: Added numeric prefix to title in {issue.file_path.name}")
            
            elif issue.issue_type == "FILENAME_NOT_LOWERCASE":
                if self._fix_filename_lowercase(issue.file_path):
                    self.fixes_applied += 1
                    print(f"✅ Fixed: Renamed file to lowercase: {issue.file_path.name}")
            
            elif issue.issue_type == "CUE_BLOCK_WHITESPACE":
                if self._fix_cue_block_whitespace(issue.file_path):
                    self.fixes_applied += 1
                    print(f"✅ Fixed: Cue block whitespace in {issue.file_path.name}")
    
    def _remove_system_message(self, file_path: Path) -> bool:
        """Remove system_message field from frontmatter."""
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            updated_lines = []
            
            for line in lines:
                if not line.strip().startswith('system_message:'):
                    updated_lines.append(line)
            
            updated_content = '\n'.join(updated_lines)
            if updated_content != content:
                file_path.write_text(updated_content, encoding='utf-8')
                return True
        except Exception:
            pass
        return False
    
    def _fix_title_case(self, file_path: Path) -> bool:
        """Fix title case in frontmatter."""
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            updated_lines = []
            
            for line in lines:
                if line.strip().startswith('title:'):
                    key, value = line.split(':', 1)
                    title = value.strip()
                    proper_title = self._to_title_case(title)
                    updated_lines.append(f"{key}: {proper_title}")
                else:
                    updated_lines.append(line)
            
            updated_content = '\n'.join(updated_lines)
            if updated_content != content:
                file_path.write_text(updated_content, encoding='utf-8')
                return True
        except Exception:
            pass
        return False
    
    def _fix_title_lowercase(self, file_path: Path) -> bool:
        """Fix title to be lowercase with numerical prefix stripped."""
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            updated_lines = []
            
            for line in lines:
                if line.strip().startswith('title:'):
                    key, value = line.split(':', 1)
                    title = value.strip()
                    
                    # Strip numerical prefix and convert to lowercase
                    match = re.match(r'^(\d+\s*)(.*)', title)
                    if match:
                        rest = match.group(2).strip()
                        proper_title = rest.lower()
                        updated_lines.append(f"{key}: {proper_title}")
                    else:
                        # No prefix found, just convert to lowercase
                        proper_title = title.lower()
                        updated_lines.append(f"{key}: {proper_title}")
                else:
                    updated_lines.append(line)
            
            updated_content = '\n'.join(updated_lines)
            if updated_content != content:
                file_path.write_text(updated_content, encoding='utf-8')
                return True
        except Exception:
            pass
        return False
    
    def _fix_title_add_prefix(self, file_path: Path) -> bool:
        """Add numerical prefix to title based on order field."""
        try:
            content = file_path.read_text(encoding='utf-8')
            frontmatter = self._extract_frontmatter(content)
            if not frontmatter:
                return False
            
            order = frontmatter.get('order', '').strip('"')
            if not order:
                return False
            
            lines = content.split('\n')
            updated_lines = []
            
            for line in lines:
                if line.strip().startswith('title:'):
                    key, value = line.split(':', 1)
                    title = value.strip()
                    
                    # Add order prefix and convert to lowercase
                    new_title = f"{order} {title.lower()}"
                    updated_lines.append(f"{key}: {new_title}")
                else:
                    updated_lines.append(line)
            
            updated_content = '\n'.join(updated_lines)
            if updated_content != content:
                file_path.write_text(updated_content, encoding='utf-8')
                return True
        except Exception:
            pass
        return False
    
    def _fix_filename_lowercase(self, file_path: Path) -> bool:
        """Rename file to lowercase."""
        try:
            new_filename = file_path.name.lower()
            new_file_path = file_path.parent / new_filename
            
            # Check if target file already exists
            if new_file_path.exists() and new_file_path != file_path:
                print(f"⚠️  Cannot rename {file_path.name}: target {new_filename} already exists")
                return False
            
            # Rename the file
            file_path.rename(new_file_path)
            return True
        except Exception as e:
            print(f"❌ Failed to rename {file_path.name}: {e}")
            return False
    
    def _fix_cue_block_whitespace(self, file_path: Path) -> bool:
        """Fix whitespace issues around cue blocks."""
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            updated_lines = []
            modified = False
            
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Fix text on same line as <!-- End Cue -->
                if '<!-- End Cue -->' in line and not line.strip().endswith('<!-- End Cue -->'):
                    # Split the line at <!-- End Cue -->
                    end_cue_pos = line.find('<!-- End Cue -->')
                    before_end_cue = line[:end_cue_pos + len('<!-- End Cue -->')]
                    after_end_cue = line[end_cue_pos + len('<!-- End Cue -->'):].strip()
                    
                    updated_lines.append(before_end_cue)
                    if after_end_cue:
                        updated_lines.append('')  # Add blank line
                        updated_lines.append(after_end_cue)
                    modified = True
                
                # Fix missing blank line after <!-- End Cue -->
                elif line.strip() == '<!-- End Cue -->':
                    updated_lines.append(line)
                    if i + 1 < len(lines) and lines[i + 1].strip() != '':
                        # Add blank line before next content
                        updated_lines.append('')
                        modified = True
                
                # Fix missing blank line before <!-- Begin Cue -->
                elif line.strip() == '<!-- Begin Cue -->':
                    if i > 0 and updated_lines and updated_lines[-1].strip() != '':
                        # Add blank line before Begin Cue
                        updated_lines.append('')
                        modified = True
                    updated_lines.append(line)
                
                else:
                    updated_lines.append(line)
                
                i += 1
            
            if modified:
                updated_content = '\n'.join(updated_lines)
                file_path.write_text(updated_content, encoding='utf-8')
                return True
                
        except Exception as e:
            print(f"❌ Failed to fix cue block whitespace in {file_path.name}: {e}")
        
        return False
    
    def _write_cleanup_log(self):
        """Write cleanup issues to log file."""
        log_file = Path(f"cleaner-{self.episode_number}.log")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Episode Cleanup Log - Episode {self.episode_number}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Total Issues: {len(self.issues)}\n")
            f.write("=" * 80 + "\n\n")
            
            if not self.issues:
                f.write("✅ No issues found!\n")
            else:
                # Group issues by type
                issue_types = {}
                for issue in self.issues:
                    if issue.issue_type not in issue_types:
                        issue_types[issue.issue_type] = []
                    issue_types[issue.issue_type].append(issue)
                
                for issue_type, issues in issue_types.items():
                    f.write(f"## {issue_type} ({len(issues)} issues)\n")
                    for issue in issues:
                        f.write(f"{issue.to_log_entry()}\n")
                    f.write("\n")
        
        print(f"📝 Cleanup log written to: {log_file}")
    
    def _print_summary(self):
        """Print cleanup summary."""
        print()
        print("=" * 60)
        print("📊 Episode Cleanup Summary")
        print("=" * 60)
        
        if not self.issues:
            print("🎉 No issues found! Episode is clean.")
        else:
            # Count issues by type
            issue_counts = {}
            for issue in self.issues:
                issue_counts[issue.issue_type] = issue_counts.get(issue.issue_type, 0) + 1
            
            print(f"📋 Total issues found: {len(self.issues)}")
            for issue_type, count in sorted(issue_counts.items()):
                print(f"   • {issue_type}: {count}")
        
        if self.fix_issues:
            print(f"🔧 Fixes applied: {self.fixes_applied}")
        
        print(f"📝 Episode: {self.episode_number}")


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive episode cleanup and validation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python episode-cleanup.py --episode=0236
  python episode-cleanup.py --episode=0236 --fix

Validation Checks:
Episode Level:
1. AssetID format validation
2. Status check (notes if not production-ready)
3. Type validation (prompts for sunday_show)
4. Sunday show airdate validation
5. Duration existence and reasonableness

Segment Level:
6. system_message fields (removes if --fix)
7. Filename order vs frontmatter order mismatch
8. Duplicate order values
9. Zero or missing durations
10. Improper title case (fixes if --fix)
11. Invalid airdate format (YYYY-MM-DD)
12. Airdate consistency with episode info.md
13. Segment AssetID validation
14. File content validation
15. Duration consistency (episode vs segments)
16. Segment title format (lowercase with numeric prefix, fixes if --fix)
17. Filename casing (all lowercase, renames files if --fix)
18. Cue block validation (can skip with --skip-cue-validation)

Output:
- Console summary with production-ready status
- Detailed log file: cleaner-{episode}.log
        """
    )
    
    parser.add_argument(
        '--episode',
        required=True,
        help='Episode number (e.g., 0236)'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Apply automatic fixes for certain issues'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Auto-confirm all prompts (non-interactive mode)'
    )
    parser.add_argument(
        '--skip-cue-validation',
        action='store_true',
        help='Skip cue block validation (faster processing)'
    )
    
    args = parser.parse_args()
    
    # Validate episode number format
    if not re.match(r'^\d{4}$', args.episode):
        print(f"❌ Invalid episode number format: {args.episode}")
        print("Episode number should be 4 digits (e.g., 0236)")
        sys.exit(1)
    
    print("🧹 Episode Cleanup Tool")
    print("=" * 60)
    print(f"📁 Episodes path: {EPISODES_ROOT}")
    print(f"🎯 Target episode: {args.episode}")
    if args.fix:
        print("🔧 Fix mode: ENABLED")
    print()
    
    try:
        cleanup = EpisodeCleanup(args.episode, args.fix, args.yes, args.skip_cue_validation)
        success = cleanup.run_cleanup()
        
        if success:
            exit_code = 0 if not cleanup.issues else 1
            print(f"\n🎉 Episode cleanup completed!")
            sys.exit(exit_code)
        else:
            print(f"\n💥 Episode cleanup failed")
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