"""
Duration Analysis Router
API endpoint to analyze media duration using FFprobe and update duration fields
"""

import os
import subprocess
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import frontmatter
from sqlalchemy.orm import Session

from auth.utils import get_current_user_or_key
from database import get_db
from models_assetid import AssetIDRegistry

router = APIRouter(prefix="/api/duration", tags=["Duration Analysis"])

class DurationResponse(BaseModel):
    success: bool
    asset_id: str
    asset_type: str
    durations_updated: int = 0
    results: List[Dict[str, Any]] = []
    message: str

def get_duration_with_ffprobe(file_path: str) -> Optional[float]:
    """Use FFprobe to get duration of media file"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return None
            
        data = json.loads(result.stdout)
        duration = float(data['format']['duration'])
        return duration
        
    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, ValueError):
        return None

def seconds_to_timecode(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def extract_media_url_from_cue(cue_content: str) -> Optional[str]:
    """Extract MediaURL from cue block content"""
    # Look for MediaURL in various formats
    patterns = [
        r'MediaURL:\s*([^\n\r]+)',
        r'media_url:\s*([^\n\r]+)',
        r'url:\s*([^\n\r]+)',
        r'file:\s*([^\n\r]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, cue_content, re.IGNORECASE)
        if match:
            return match.group(1).strip().strip('"\'')
    
    return None

def update_cue_duration_in_markdown(markdown_path: Path, asset_id: str, duration_timecode: str) -> bool:
    """Update duration field in specific cue block within markdown file.
    Gracefully handles missing files (filesystem may not exist if DB-first)."""
    try:
        if not markdown_path.exists():
            return False

        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the cue block with this AssetID
        cue_pattern = rf'```cue\s+{re.escape(asset_id)}.*?```'
        cue_match = re.search(cue_pattern, content, re.DOTALL | re.IGNORECASE)

        if not cue_match:
            return False

        cue_block = cue_match.group(0)

        # Update duration field in the cue block
        duration_patterns = [
            (r'Duration:\s*[^\n\r]*', f'Duration: {duration_timecode}'),
            (r'duration:\s*[^\n\r]*', f'duration: {duration_timecode}')
        ]

        updated_block = cue_block
        duration_updated = False

        for pattern, replacement in duration_patterns:
            if re.search(pattern, updated_block, re.IGNORECASE):
                updated_block = re.sub(pattern, replacement, updated_block, flags=re.IGNORECASE)
                duration_updated = True
                break

        # If no duration field found, add one
        if not duration_updated:
            # Insert duration field before the closing ```
            updated_block = updated_block.replace('```', f'Duration: {duration_timecode}\n```')

        # Replace the old cue block with updated one
        updated_content = content.replace(cue_block, updated_block)

        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        return True

    except Exception:
        return False

def update_rundown_item_duration(markdown_path: Path, duration_timecode: str) -> bool:
    """Update duration field in markdown frontmatter.
    Gracefully handles missing files (filesystem may not exist if DB-first)."""
    try:
        if not markdown_path.exists():
            return False

        with open(markdown_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        # Update duration in frontmatter
        post.metadata['duration'] = duration_timecode

        # Write back to file
        with open(markdown_path, 'w', encoding='utf-8') as f:
            frontmatter.dump(post, f)

        return True

    except Exception:
        return False


def update_rundown_item_duration_in_db(db: Session, asset_id: str, duration_timecode: str) -> bool:
    """Update duration field on RundownItem in the database."""
    try:
        from models_v2 import RundownItem
        db_item = db.query(RundownItem).filter(
            RundownItem.asset_id == str(asset_id)
        ).first()
        if db_item:
            db_item.duration = duration_timecode
            db.commit()
            return True
        return False
    except Exception:
        db.rollback()
        return False

def find_cue_blocks_in_rundown_item(markdown_path: Path) -> List[Dict[str, str]]:
    """Find all cue blocks with AssetIDs in a rundown item"""
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all cue blocks
        cue_pattern = r'```cue\s+([^\s]+).*?```'
        cue_matches = re.finditer(cue_pattern, content, re.DOTALL | re.IGNORECASE)
        
        cue_blocks = []
        for match in cue_matches:
            asset_id = match.group(1).strip()
            cue_content = match.group(0)
            media_url = extract_media_url_from_cue(cue_content)
            
            if media_url:
                cue_blocks.append({
                    'asset_id': asset_id,
                    'content': cue_content,
                    'media_url': media_url
                })
        
        return cue_blocks
        
    except Exception:
        return []

@router.post("/getDuration", response_model=DurationResponse)
async def get_duration(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_or_key)
):
    """
    Get duration for AssetID - handles both cue SOTs and rundown items
    """
    try:
        # Look up AssetID in registry
        asset_record = db.query(AssetIDRegistry).filter(
            AssetIDRegistry.asset_id == asset_id
        ).first()
        
        if not asset_record:
            raise HTTPException(status_code=404, detail=f"AssetID '{asset_id}' not found in registry")
        
        results = []
        durations_updated = 0
        
        # Determine asset type and process accordingly
        if asset_record.asset_type.lower() in ['cue', 'sot']:
            # Single cue/SOT processing
            result = await process_single_cue(asset_record, db)
            results.append(result)
            if result.get('updated', False):
                durations_updated += 1
                
        elif asset_record.asset_type.lower() in ['segment', 'rundown_item']:
            # Batch process all cues in the rundown item
            batch_results = await process_rundown_item_batch(asset_record, db)
            results.extend(batch_results)
            durations_updated = sum(1 for r in batch_results if r.get('updated', False))
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported asset type: {asset_record.asset_type}")
        
        return DurationResponse(
            success=True,
            asset_id=asset_id,
            asset_type=asset_record.asset_type,
            durations_updated=durations_updated,
            results=results,
            message=f"Processed {len(results)} items, updated {durations_updated} duration fields"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing duration: {str(e)}")

async def process_single_cue(asset_record: AssetIDRegistry, db: Session) -> Dict[str, Any]:
    """Process a single cue/SOT AssetID.
    Updates both filesystem (if files exist) and database."""
    try:
        # Construct file path from asset record
        file_path = asset_record.file_path
        if not file_path:
            return {
                'asset_id': asset_record.asset_id,
                'error': 'No file path in asset record',
                'updated': False
            }

        # If relative path, make it absolute
        if not file_path.startswith('/'):
            episode_dir = Path(f"/home/episodes/{asset_record.episode_number}")
            file_path = str(episode_dir / file_path)

        # Check if file exists
        if not Path(file_path).exists():
            return {
                'asset_id': asset_record.asset_id,
                'file_path': file_path,
                'error': 'Media file not found',
                'updated': False
            }

        # Get duration with FFprobe
        duration_seconds = get_duration_with_ffprobe(file_path)
        if duration_seconds is None:
            return {
                'asset_id': asset_record.asset_id,
                'file_path': file_path,
                'error': 'Could not analyze duration with FFprobe',
                'updated': False
            }

        duration_timecode = seconds_to_timecode(duration_seconds)

        # Update the cue block in the markdown file (graceful if missing)
        file_updated = False
        if asset_record.markdown_file_path:
            markdown_path = Path(asset_record.markdown_file_path)
            if not markdown_path.is_absolute():
                episode_dir = Path(f"/home/episodes/{asset_record.episode_number}")
                markdown_path = episode_dir / markdown_path
            file_updated = update_cue_duration_in_markdown(markdown_path, asset_record.asset_id, duration_timecode)

        # Also update duration in DB
        db_updated = update_rundown_item_duration_in_db(db, asset_record.asset_id, duration_timecode)

        return {
            'asset_id': asset_record.asset_id,
            'file_path': file_path,
            'duration_seconds': duration_seconds,
            'duration_timecode': duration_timecode,
            'updated': file_updated or db_updated,
            'file_updated': file_updated,
            'db_updated': db_updated
        }

    except Exception as e:
        return {
            'asset_id': asset_record.asset_id,
            'error': f'Error processing cue: {str(e)}',
            'updated': False
        }

async def process_rundown_item_batch(asset_record: AssetIDRegistry, db: Session) -> List[Dict[str, Any]]:
    """Process all cue blocks within a rundown item"""
    try:
        results = []
        
        # Get the markdown file for this rundown item
        if not asset_record.markdown_file_path:
            return [{
                'asset_id': asset_record.asset_id,
                'error': 'No markdown file path in asset record',
                'updated': False
            }]
        
        markdown_path = Path(asset_record.markdown_file_path)
        if not markdown_path.is_absolute():
            episode_dir = Path(f"/home/episodes/{asset_record.episode_number}")
            markdown_path = episode_dir / markdown_path
        
        if not markdown_path.exists():
            return [{
                'asset_id': asset_record.asset_id,
                'error': f'Markdown file not found: {markdown_path}',
                'updated': False
            }]
        
        # Find all cue blocks in the rundown item
        cue_blocks = find_cue_blocks_in_rundown_item(markdown_path)
        
        if not cue_blocks:
            return [{
                'asset_id': asset_record.asset_id,
                'message': 'No cue blocks found in rundown item',
                'updated': False
            }]
        
        total_duration_seconds = 0.0
        
        # Process each cue block
        for cue_block in cue_blocks:
            cue_asset_id = cue_block['asset_id']
            media_url = cue_block['media_url']
            
            # Resolve media URL to actual file path
            if not media_url.startswith('/'):
                episode_dir = Path(f"/home/episodes/{asset_record.episode_number}")
                file_path = str(episode_dir / "assets" / media_url)
            else:
                file_path = media_url
            
            # Get duration
            duration_seconds = get_duration_with_ffprobe(file_path)
            if duration_seconds:
                duration_timecode = seconds_to_timecode(duration_seconds)
                updated = update_cue_duration_in_markdown(markdown_path, cue_asset_id, duration_timecode)
                total_duration_seconds += duration_seconds
                
                results.append({
                    'asset_id': cue_asset_id,
                    'file_path': file_path,
                    'duration_seconds': duration_seconds,
                    'duration_timecode': duration_timecode,
                    'updated': updated
                })
            else:
                results.append({
                    'asset_id': cue_asset_id,
                    'file_path': file_path,
                    'error': 'Could not analyze duration',
                    'updated': False
                })
        
        # Update the rundown item's total duration in both file and DB
        if total_duration_seconds > 0:
            total_timecode = seconds_to_timecode(total_duration_seconds)
            file_updated = update_rundown_item_duration(markdown_path, total_timecode)
            db_updated = update_rundown_item_duration_in_db(db, asset_record.asset_id, total_timecode)

            results.append({
                'asset_id': asset_record.asset_id,
                'type': 'rundown_total',
                'duration_seconds': total_duration_seconds,
                'duration_timecode': total_timecode,
                'updated': file_updated or db_updated,
                'file_updated': file_updated,
                'db_updated': db_updated
            })
        
        return results
        
    except Exception as e:
        return [{
            'asset_id': asset_record.asset_id,
            'error': f'Error processing rundown item: {str(e)}',
            'updated': False
        }]