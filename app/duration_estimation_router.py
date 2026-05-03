"""
Duration Estimation Router - Calculates segment durations based on content analysis
Analyzes word counts, cue blocks, SOTs, FSQs, and ad-libs to estimate total segment duration.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from auth.utils import get_current_user_or_key
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging
import os
import re
from pathlib import Path

# Import file management utilities
from convert_assetid_router import FileManager

router = APIRouter(tags=["Duration Estimation"])
logger = logging.getLogger(__name__)

# Configuration
EPISODES_ROOT = Path("/home/episodes")
DEFAULT_WPM = 150  # Default words per minute for speech
DEFAULT_FSQ_WPM = 120  # Slightly slower for full-screen quotes (more dramatic)


class DurationSettings(BaseModel):
    """Settings for duration calculation."""
    speech_wpm: int = DEFAULT_WPM
    fsq_wpm: int = DEFAULT_FSQ_WPM
    include_adlibs: bool = True
    include_sots: bool = True
    include_fsqs: bool = True


class CueAnalysis(BaseModel):
    """Analysis result for a single cue."""
    cue_type: str
    asset_id: Optional[str] = None
    original_duration: Optional[str] = None
    calculated_duration: Optional[str] = None
    word_count: Optional[int] = None
    notes: str = ""


class SegmentDurationResult(BaseModel):
    """Result of segment duration analysis."""
    success: bool
    message: str
    file_path: str
    segment_name: str
    original_duration: Optional[str] = None
    calculated_duration: str
    
    # Breakdown components
    speech_word_count: int
    speech_duration_seconds: float
    sot_duration_seconds: float
    fsq_duration_seconds: float
    adlib_duration_seconds: float
    total_duration_seconds: float
    
    # Detailed analysis
    cues_analyzed: List[CueAnalysis]
    settings_used: DurationSettings
    
    # Update status
    duration_updated: bool = False


class EpisodeDurationResult(BaseModel):
    """Result of episode-wide duration analysis."""
    success: bool
    message: str
    episode_number: str
    total_segments: int
    segments_processed: int
    segments_updated: int
    total_episode_duration: str
    
    segment_results: List[SegmentDurationResult]
    settings_used: DurationSettings


class DurationEstimator:
    """Handles duration estimation for segments and episodes."""
    
    def __init__(self, db: Session, user_id: str, settings: DurationSettings):
        self.db = db
        self.user_id = user_id
        self.settings = settings
    
    def estimate_segment_duration_by_assetid(self, asset_id: str,
                                           update_file: bool = True) -> SegmentDurationResult:
        """Estimate duration for a single segment by AssetID.

        Database-first: looks up RundownItem by asset_id in DB.
        Falls back to filesystem scan only if DB lookup fails.
        """
        from models_v2 import RundownItem, Rundown, Episode

        try:
            # Database-first: find by asset_id
            db_item = self.db.query(RundownItem).filter(
                RundownItem.asset_id == str(asset_id)
            ).first()

            if db_item and db_item.script_content:
                return self._estimate_from_db_item(db_item, update_file)

            if not db_item:
                raise HTTPException(status_code=404, detail=f"Segment with AssetID {asset_id} not found in database")

            # DB item exists but has no script_content - try filesystem fallback
            segment_file_info = self._find_segment_by_assetid(asset_id)
            if segment_file_info and segment_file_info['file_path'].exists():
                logger.info(f"AssetID {asset_id} has no script_content in DB, falling back to filesystem")
                return self._estimate_segment_duration_common(
                    segment_file_info['file_path'],
                    segment_file_info['segment_name'],
                    segment_file_info['episode_number'],
                    update_file
                )

            raise HTTPException(status_code=404, detail=f"Segment with AssetID {asset_id} has no content in DB or filesystem")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to estimate duration for AssetID {asset_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Duration estimation failed: {str(e)}")
    
    def estimate_segment_duration(self, episode_number: str, segment_name: str, 
                                update_file: bool = True) -> SegmentDurationResult:
        """Estimate duration for a single segment by episode/segment name (legacy method)."""
        try:
            # Find segment file
            episode_path = EPISODES_ROOT / episode_number
            rundown_path = episode_path / "rundown"
            segment_file = rundown_path / f"{segment_name}.md"
            
            if not segment_file.exists():
                raise HTTPException(status_code=404, detail=f"Segment file {segment_name}.md not found")
            
            # Use the common estimation logic
            return self._estimate_segment_duration_common(segment_file, segment_name, episode_number, update_file)
            
        except Exception as e:
            logger.error(f"Failed to estimate duration for segment {segment_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Duration estimation failed: {str(e)}")
    
    def _estimate_from_db_item(self, db_item, update_db: bool = True) -> SegmentDurationResult:
        """Estimate duration from a database RundownItem's script_content."""
        from models_v2 import RundownItem, Rundown, Episode

        content = db_item.script_content or ''
        segment_name = db_item.slug or db_item.title or f"item-{db_item.id}"
        original_duration = db_item.duration

        # Find episode number for the result
        episode_number = "unknown"
        if db_item.rundown:
            rundown = db_item.rundown
            if rundown.episode:
                episode_number = rundown.episode.episode_number or "unknown"

        # Parse content into body and cue blocks
        body_content, cue_blocks = self._parse_segment_content(content)

        # Calculate speech duration
        speech_word_count = self._count_words(body_content)
        speech_duration = speech_word_count / self.settings.speech_wpm * 60

        # Analyze cue blocks
        cue_analyses = []
        sot_duration = 0.0
        fsq_duration = 0.0
        adlib_duration = 0.0

        for cue_data in cue_blocks:
            analysis = self._analyze_cue_block(cue_data)
            cue_analyses.append(analysis)

            if analysis.cue_type == "SOT" and self.settings.include_sots:
                if analysis.calculated_duration:
                    sot_duration += self._parse_duration_to_seconds(analysis.calculated_duration)
            elif analysis.cue_type == "FSQ" and self.settings.include_fsqs:
                if analysis.calculated_duration:
                    fsq_duration += self._parse_duration_to_seconds(analysis.calculated_duration)
            elif analysis.cue_type == "ADLIB" and self.settings.include_adlibs:
                if analysis.calculated_duration:
                    adlib_duration += self._parse_duration_to_seconds(analysis.calculated_duration)

        total_seconds = speech_duration + sot_duration + fsq_duration + adlib_duration
        total_duration_formatted = self._seconds_to_duration_string(total_seconds)

        # Update duration in database
        duration_updated = False
        if update_db:
            try:
                db_item.duration = total_duration_formatted
                self.db.commit()
                duration_updated = True
                logger.info(f"Updated duration in DB for {segment_name}: {total_duration_formatted}")
            except Exception as e:
                logger.error(f"Failed to update duration in DB: {e}")
                self.db.rollback()

        return SegmentDurationResult(
            success=True,
            message=f"Calculated duration for segment {segment_name} (from database)",
            file_path=f"database:rundown_items.id={db_item.id}",
            segment_name=segment_name,
            original_duration=original_duration,
            calculated_duration=total_duration_formatted,
            speech_word_count=speech_word_count,
            speech_duration_seconds=speech_duration,
            sot_duration_seconds=sot_duration,
            fsq_duration_seconds=fsq_duration,
            adlib_duration_seconds=adlib_duration,
            total_duration_seconds=total_seconds,
            cues_analyzed=cue_analyses,
            settings_used=self.settings,
            duration_updated=duration_updated
        )

    def _find_segment_by_assetid(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Find segment file path by AssetID by scanning filesystem."""
        if not EPISODES_ROOT.exists():
            return None
        
        # Scan all episodes for the AssetID
        for episode_dir in EPISODES_ROOT.iterdir():
            if not episode_dir.is_dir() or not episode_dir.name.isdigit():
                continue
            
            episode_number = episode_dir.name
            rundown_path = episode_dir / "rundown"
            
            if not rundown_path.exists():
                continue
            
            # Check all segment files in this episode
            for segment_file in rundown_path.glob("*.md"):
                try:
                    content = FileManager.read_file(segment_file)
                    file_asset_id = FileManager.extract_asset_id_from_frontmatter(content)
                    
                    if file_asset_id == asset_id:
                        return {
                            'file_path': segment_file,
                            'segment_name': segment_file.stem,
                            'episode_number': episode_number,
                            'asset_id': asset_id
                        }
                except Exception as e:
                    logger.warning(f"Error reading segment file {segment_file}: {e}")
                    continue
        
        return None
    
    def _estimate_segment_duration_common(self, segment_file: Path, segment_name: str, 
                                        episode_number: str, update_file: bool) -> SegmentDurationResult:
        """Common logic for segment duration estimation."""
        try:
            # Read segment content
            content = FileManager.read_file(segment_file)
            
            # Extract original duration from frontmatter
            original_duration = self._extract_duration_from_frontmatter(content)
            
            # Parse content into body and cue blocks
            body_content, cue_blocks = self._parse_segment_content(content)
            
            # Calculate speech duration (body content excluding cue blocks)
            speech_word_count = self._count_words(body_content)
            speech_duration = speech_word_count / self.settings.speech_wpm * 60  # seconds
            
            # Analyze cue blocks
            cue_analyses = []
            sot_duration = 0.0
            fsq_duration = 0.0
            adlib_duration = 0.0
            
            for cue_data in cue_blocks:
                analysis = self._analyze_cue_block(cue_data)
                cue_analyses.append(analysis)
                
                if analysis.cue_type == "SOT" and self.settings.include_sots:
                    if analysis.calculated_duration:
                        sot_duration += self._parse_duration_to_seconds(analysis.calculated_duration)
                
                elif analysis.cue_type == "FSQ" and self.settings.include_fsqs:
                    if analysis.calculated_duration:
                        fsq_duration += self._parse_duration_to_seconds(analysis.calculated_duration)
                
                elif analysis.cue_type == "ADLIB" and self.settings.include_adlibs:
                    if analysis.calculated_duration:
                        adlib_duration += self._parse_duration_to_seconds(analysis.calculated_duration)
            
            # Calculate total duration
            total_seconds = speech_duration + sot_duration + fsq_duration + adlib_duration
            total_duration_formatted = self._seconds_to_duration_string(total_seconds)
            
            # Update file if requested
            duration_updated = False
            if update_file:
                updated_content = self._update_segment_duration(content, total_duration_formatted, cue_analyses)
                FileManager.write_file(segment_file, updated_content)
                duration_updated = True
                logger.info(f"Updated duration for segment {segment_name}: {total_duration_formatted}")
            
            return SegmentDurationResult(
                success=True,
                message=f"Calculated duration for segment {segment_name}",
                file_path=str(segment_file),
                segment_name=segment_name,
                original_duration=original_duration,
                calculated_duration=total_duration_formatted,
                speech_word_count=speech_word_count,
                speech_duration_seconds=speech_duration,
                sot_duration_seconds=sot_duration,
                fsq_duration_seconds=fsq_duration,
                adlib_duration_seconds=adlib_duration,
                total_duration_seconds=total_seconds,
                cues_analyzed=cue_analyses,
                settings_used=self.settings,
                duration_updated=duration_updated
            )
            
        except Exception as e:
            logger.error(f"Failed to estimate duration for segment {segment_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Duration estimation failed: {str(e)}")
    
    def estimate_episode_duration(self, episode_number: str, update_files: bool = True) -> EpisodeDurationResult:
        """Estimate durations for all segments in an episode.

        Database-first: queries RundownItems from DB.
        Falls back to filesystem if no DB rundown found.
        """
        from models_v2 import RundownItem, Rundown, Episode

        try:
            segment_results = []
            total_episode_seconds = 0.0
            segments_updated = 0

            # Database-first: find episode and its rundown items
            episode = self.db.query(Episode).filter(
                Episode.episode_number == episode_number
            ).first()

            db_items = []
            if episode:
                rundown = self.db.query(Rundown).filter(
                    Rundown.episode_id == episode.id
                ).first()
                if rundown:
                    db_items = self.db.query(RundownItem).filter(
                        RundownItem.rundown_id == rundown.id
                    ).order_by(RundownItem.order_in_rundown).all()

            if db_items:
                # Process from database
                for db_item in db_items:
                    if not db_item.script_content:
                        continue
                    try:
                        result = self._estimate_from_db_item(db_item, update_files)
                        segment_results.append(result)
                        total_episode_seconds += result.total_duration_seconds
                        if result.duration_updated:
                            segments_updated += 1
                    except Exception as e:
                        logger.warning(f"Failed to process DB item {db_item.asset_id}: {e}")
                        continue
            else:
                # Filesystem fallback
                episode_path = EPISODES_ROOT / episode_number
                rundown_path = episode_path / "rundown"

                if not rundown_path.exists():
                    raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found in database or filesystem")

                logger.info(f"No DB rundown for episode {episode_number}, falling back to filesystem")
                for segment_file in sorted(rundown_path.glob("*.md")):
                    segment_name = segment_file.stem
                    try:
                        result = self.estimate_segment_duration(episode_number, segment_name, update_files)
                        segment_results.append(result)
                        total_episode_seconds += result.total_duration_seconds
                        if result.duration_updated:
                            segments_updated += 1
                    except Exception as e:
                        logger.warning(f"Failed to process segment {segment_name}: {e}")
                        continue

            total_episode_duration = self._seconds_to_duration_string(total_episode_seconds)

            return EpisodeDurationResult(
                success=True,
                message=f"Processed {len(segment_results)} segments in episode {episode_number}",
                episode_number=episode_number,
                total_segments=len(segment_results),
                segments_processed=len(segment_results),
                segments_updated=segments_updated,
                total_episode_duration=total_episode_duration,
                segment_results=segment_results,
                settings_used=self.settings
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to estimate episode duration for {episode_number}: {e}")
            raise HTTPException(status_code=500, detail=f"Episode duration estimation failed: {str(e)}")
    
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
                
                # Map common field names
                if field_name.lower() == 'type':
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
        asset_id = cue_data.get('AssetID')
        original_duration = cue_data.get('duration')
        calculated_duration = None
        word_count = None
        notes = ""
        
        if cue_type == "SOT":
            # For SOTs, use existing duration or default
            calculated_duration = original_duration or "00:00:30"  # Default 30 seconds
            notes = "Using existing duration" if original_duration else "Using default SOT duration"
        
        elif cue_type == "FSQ":
            # For FSQs, calculate based on quote word count
            quote_text = cue_data.get('quote', '')
            if quote_text:
                word_count = self._count_words(quote_text)
                duration_seconds = word_count / self.settings.fsq_wpm * 60
                calculated_duration = self._seconds_to_duration_string(duration_seconds)
                notes = f"Calculated from {word_count} words at {self.settings.fsq_wpm} WPM"
            else:
                calculated_duration = "00:00:10"  # Default for empty quotes
                notes = "No quote text found, using default duration"
        
        elif cue_type == "ADLIB":
            # For ADLIBs, use existing duration or default
            calculated_duration = original_duration or "00:01:00"  # Default 1 minute
            notes = "Using existing duration" if original_duration else "Using default ad-lib duration"
        
        else:
            # Other cue types don't contribute to spoken duration
            notes = f"Cue type {cue_type} not included in duration calculation"
        
        return CueAnalysis(
            cue_type=cue_type,
            asset_id=asset_id,
            original_duration=original_duration,
            calculated_duration=calculated_duration,
            word_count=word_count,
            notes=notes
        )
    
    def _count_words(self, text: str) -> int:
        """Count words in text, excluding markdown formatting."""
        if not text:
            return 0
        
        # Remove markdown formatting
        # Remove headers (# ## ###)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        
        # Remove bold/italic markers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)        # *italic*
        text = re.sub(r'__([^_]+)__', r'\1', text)          # __bold__
        text = re.sub(r'_([^_]+)_', r'\1', text)            # _italic_
        
        # Remove links [text](url)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Split into words and count
        words = text.split()
        return len(words)
    
    def _parse_duration_to_seconds(self, duration_str: str) -> float:
        """Parse duration string (HH:MM:SS or MM:SS) to seconds."""
        if not duration_str:
            return 0.0
        
        # Handle different formats
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
            logger.warning(f"Could not parse duration: {duration_str}")
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
    
    def _extract_duration_from_frontmatter(self, content: str) -> Optional[str]:
        """Extract duration field from YAML frontmatter."""
        frontmatter, _, _ = FileManager.extract_frontmatter(content)
        if not frontmatter:
            return None
        
        match = re.search(r'^duration:\s*(.+)$', frontmatter, re.MULTILINE)
        if match:
            return match.group(1).strip().strip('"\'')
        return None
    
    def _update_segment_duration(self, content: str, new_duration: str, 
                                cue_analyses: List[CueAnalysis]) -> str:
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
                    # Add duration field if not found
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
    
    def _update_cue_block_duration(self, cue_lines: List[str], 
                                  cue_analyses: List[CueAnalysis]) -> List[str]:
        """Update duration field in FSQ cue blocks."""
        # Extract cue type to find matching analysis
        cue_type = None
        asset_id = None
        
        for line in cue_lines:
            type_match = re.search(r'^\[Type:\s*(.+)\]$', line.strip())
            if type_match:
                cue_type = type_match.group(1).strip()
            
            id_match = re.search(r'^\[AssetID:\s*(.+)\]$', line.strip())
            if id_match:
                asset_id = id_match.group(1).strip()
        
        # Find matching analysis
        matching_analysis = None
        for analysis in cue_analyses:
            if analysis.cue_type == cue_type:
                if asset_id and analysis.asset_id == asset_id:
                    matching_analysis = analysis
                    break
                elif not asset_id:  # Match by type if no AssetID
                    matching_analysis = analysis
                    break
        
        # Update duration field for FSQ cues
        if matching_analysis and cue_type == "FSQ" and matching_analysis.calculated_duration:
            updated_lines = []
            duration_updated = False
            
            for line in cue_lines:
                if re.match(r'^\[Duration:\s*.*\]$', line.strip()):
                    updated_lines.append(f"[Duration: {matching_analysis.calculated_duration}]")
                    duration_updated = True
                else:
                    updated_lines.append(line)
            
            # Add duration field if not found
            if not duration_updated and cue_type == "FSQ":
                # Insert before the end comment
                for i, line in enumerate(updated_lines):
                    if '<!-- End Cue -->' in line:
                        updated_lines.insert(i, f"[Duration: {matching_analysis.calculated_duration}]")
                        break
            
            return updated_lines
        
        return cue_lines


@router.post("/estimateDuration/assetid/{asset_id}")
async def estimate_segment_duration_by_assetid(
    asset_id: str,
    update_file: bool = Query(True, description="Whether to update the segment file with calculated duration"),
    speech_wpm: int = Query(DEFAULT_WPM, description="Words per minute for speech"),
    fsq_wpm: int = Query(DEFAULT_FSQ_WPM, description="Words per minute for full-screen quotes"),
    include_adlibs: bool = Query(True, description="Include ad-lib durations"),
    include_sots: bool = Query(True, description="Include SOT durations"),
    include_fsqs: bool = Query(True, description="Include FSQ durations"),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> SegmentDurationResult:
    """
    Estimate duration for a single segment by AssetID.
    
    **Primary endpoint** for duration estimation using the AssetID system.
    
    **Analysis includes:**
    - Word count of segment text (excluding cue blocks)
    - SOT cue durations
    - FSQ word count converted to duration
    - Ad-lib durations
    
    **Process:**
    1. Locate segment file by scanning filesystem for AssetID
    2. Count words in segment body (speech content)
    3. Calculate speech duration using WPM
    4. Add SOT durations from cue blocks
    5. Calculate FSQ durations from quote word counts
    6. Add ad-lib durations
    7. Update frontmatter duration field
    """
    user_id = current_user.get("username", current_user.get("client_name", "api_user"))
    
    settings = DurationSettings(
        speech_wpm=speech_wpm,
        fsq_wpm=fsq_wpm,
        include_adlibs=include_adlibs,
        include_sots=include_sots,
        include_fsqs=include_fsqs
    )
    
    estimator = DurationEstimator(db, user_id, settings)
    return estimator.estimate_segment_duration_by_assetid(asset_id, update_file)


@router.post("/estimateDuration/segment/{episode_number}/{segment_name}")
async def estimate_segment_duration(
    episode_number: str,
    segment_name: str,
    update_file: bool = Query(True, description="Whether to update the segment file with calculated duration"),
    speech_wpm: int = Query(DEFAULT_WPM, description="Words per minute for speech"),
    fsq_wpm: int = Query(DEFAULT_FSQ_WPM, description="Words per minute for full-screen quotes"),
    include_adlibs: bool = Query(True, description="Include ad-lib durations"),
    include_sots: bool = Query(True, description="Include SOT durations"),
    include_fsqs: bool = Query(True, description="Include FSQ durations"),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> SegmentDurationResult:
    """
    Estimate duration for a single segment based on content analysis.
    
    **Analysis includes:**
    - Word count of segment text (excluding cue blocks)
    - SOT cue durations
    - FSQ word count converted to duration
    - Ad-lib durations
    
    **Process:**
    1. Count words in segment body (speech content)
    2. Calculate speech duration using WPM
    3. Add SOT durations from cue blocks
    4. Calculate FSQ durations from quote word counts
    5. Add ad-lib durations
    6. Update frontmatter duration field
    """
    user_id = current_user.get("username", current_user.get("client_name", "api_user"))
    
    settings = DurationSettings(
        speech_wpm=speech_wpm,
        fsq_wpm=fsq_wpm,
        include_adlibs=include_adlibs,
        include_sots=include_sots,
        include_fsqs=include_fsqs
    )
    
    estimator = DurationEstimator(db, user_id, settings)
    return estimator.estimate_segment_duration(episode_number, segment_name, update_file)


@router.post("/estimateDuration/episode/{episode_number}")
async def estimate_episode_duration(
    episode_number: str,
    update_files: bool = Query(True, description="Whether to update segment files with calculated durations"),
    speech_wpm: int = Query(DEFAULT_WPM, description="Words per minute for speech"),
    fsq_wpm: int = Query(DEFAULT_FSQ_WPM, description="Words per minute for full-screen quotes"),
    include_adlibs: bool = Query(True, description="Include ad-lib durations"),
    include_sots: bool = Query(True, description="Include SOT durations"), 
    include_fsqs: bool = Query(True, description="Include FSQ durations"),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> EpisodeDurationResult:
    """
    Estimate durations for all segments in an episode.
    
    **Processes all segments** in the episode rundown directory and provides:
    - Individual segment duration breakdowns
    - Total episode duration
    - Update status for each segment
    - Detailed cue analysis
    """
    user_id = current_user.get("username", current_user.get("client_name", "api_user"))
    
    settings = DurationSettings(
        speech_wpm=speech_wpm,
        fsq_wpm=fsq_wpm,
        include_adlibs=include_adlibs,
        include_sots=include_sots,
        include_fsqs=include_fsqs
    )
    
    estimator = DurationEstimator(db, user_id, settings)
    return estimator.estimate_episode_duration(episode_number, update_files)


@router.get("/estimateDuration/preview/assetid/{asset_id}")
async def preview_segment_duration_by_assetid(
    asset_id: str,
    speech_wpm: int = Query(DEFAULT_WPM, description="Words per minute for speech"),
    fsq_wpm: int = Query(DEFAULT_FSQ_WPM, description="Words per minute for full-screen quotes"),
    include_adlibs: bool = Query(True, description="Include ad-lib durations"),
    include_sots: bool = Query(True, description="Include SOT durations"),
    include_fsqs: bool = Query(True, description="Include FSQ durations"),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> SegmentDurationResult:
    """
    Preview segment duration calculation by AssetID without updating files.
    
    **Read-only analysis** that shows what the duration would be without making changes.
    Uses AssetID to locate the segment file.
    """
    user_id = current_user.get("username", current_user.get("client_name", "api_user"))
    
    settings = DurationSettings(
        speech_wpm=speech_wpm,
        fsq_wpm=fsq_wpm,
        include_adlibs=include_adlibs,
        include_sots=include_sots,
        include_fsqs=include_fsqs
    )
    
    estimator = DurationEstimator(db, user_id, settings)
    return estimator.estimate_segment_duration_by_assetid(asset_id, update_file=False)


@router.get("/estimateDuration/preview/{episode_number}/{segment_name}")
async def preview_segment_duration(
    episode_number: str,
    segment_name: str,
    speech_wpm: int = Query(DEFAULT_WPM, description="Words per minute for speech"),
    fsq_wpm: int = Query(DEFAULT_FSQ_WPM, description="Words per minute for full-screen quotes"),
    include_adlibs: bool = Query(True, description="Include ad-lib durations"),
    include_sots: bool = Query(True, description="Include SOT durations"),
    include_fsqs: bool = Query(True, description="Include FSQ durations"),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> SegmentDurationResult:
    """
    Preview segment duration calculation without updating files.
    
    **Read-only analysis** that shows what the duration would be without making changes.
    """
    user_id = current_user.get("username", current_user.get("client_name", "api_user"))
    
    settings = DurationSettings(
        speech_wpm=speech_wpm,
        fsq_wpm=fsq_wpm,
        include_adlibs=include_adlibs,
        include_sots=include_sots,
        include_fsqs=include_fsqs
    )
    
    estimator = DurationEstimator(db, user_id, settings)
    return estimator.estimate_segment_duration(episode_number, segment_name, update_file=False)