"""
AssetID Conversion Router - Backend equivalent of Obsidian plugin conversion logic
Converts local AssetIDs to server-registered AssetIDs via API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth.utils import get_current_user_or_key
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging
import os
import re
from pathlib import Path
from typing import List

# Import AssetID service and models
from services.asset_id import AssetIDService
from new_assetid_router import NewAssetIDRequest, create_new_asset_id

router = APIRouter(tags=["AssetID Conversion"])
logger = logging.getLogger(__name__)

# Configuration - adjust these paths based on your setup
EPISODES_ROOT = Path("/home/episodes")


class ConversionResponse(BaseModel):
    """Response model for AssetID conversion."""
    success: bool
    message: str
    old_asset_id: Optional[str] = None
    new_asset_id: Optional[str] = None
    file_path: Optional[str] = None
    context_type: str
    conversions_count: int = 0


class AssetIDScanResult(BaseModel):
    """Individual AssetID found during scan."""
    asset_id: str
    file_path: str
    context_type: str  # episode, segment, cue
    episode_number: Optional[str] = None
    segment_name: Optional[str] = None
    cue_type: Optional[str] = None
    is_server_asset: bool
    needs_conversion: bool
    conversion_api_call: Optional[str] = None  # Suggested API endpoint


class ScanResponse(BaseModel):
    """Response model for AssetID scanning."""
    success: bool
    message: str
    total_assets_found: int
    server_assets_count: int
    local_assets_count: int
    conversion_needed_count: int
    assets: List[AssetIDScanResult]
    suggested_conversions: List[str]  # List of API calls to run


class FileManager:
    """Handles file operations similar to Obsidian vault operations."""
    
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
        """Extract AssetID from YAML frontmatter - matches Obsidian plugin logic."""
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
    
    @staticmethod
    def extract_episode_number_from_frontmatter(content: str) -> Optional[int]:
        """Extract episode number from frontmatter - matches plugin logic."""
        frontmatter, _, _ = FileManager.extract_frontmatter(content)
        if not frontmatter:
            return None
        
        # Try both episode_number and episode fields
        for field_name in ['episode_number', 'episode']:
            pattern = f'^{field_name}:\\s*(.+)$'
            match = re.search(pattern, frontmatter, re.MULTILINE)
            if match:
                try:
                    return int(match.group(1).strip())
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def extract_slug_from_frontmatter(content: str) -> Optional[str]:
        """Extract slug from frontmatter."""
        frontmatter, _, _ = FileManager.extract_frontmatter(content)
        if not frontmatter:
            return None
        
        match = re.search(r'^slug:\s*(.+)$', frontmatter, re.MULTILINE)
        if match:
            return match.group(1).strip().strip('"\'')
        return None
    
    @staticmethod
    def replace_asset_id_in_frontmatter(content: str, old_asset_id: Optional[str], new_asset_id: str) -> str:
        """Replace AssetID in frontmatter and add system message."""
        lines = content.split('\n')
        updated_lines = []
        in_frontmatter = False
        asset_id_found = False
        system_message_found = False
        
        for i, line in enumerate(lines):
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                    updated_lines.append(line)
                    # Add system message after opening ---
                    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    if old_asset_id:
                        message = f"system_message: {timestamp}: Converted AssetID {old_asset_id} to server AssetID {new_asset_id}"
                    else:
                        message = f"system_message: {timestamp}: Generated new server AssetID {new_asset_id}"
                    updated_lines.append(message)
                    continue
                else:
                    # End of frontmatter
                    in_frontmatter = False
                    # Add AssetID if not found
                    if not asset_id_found:
                        updated_lines.append(f"AssetID: {new_asset_id}")
                    updated_lines.append(line)
                    continue
            
            if in_frontmatter:
                trimmed = line.strip()
                if trimmed.startswith('AssetID:'):
                    # Replace existing AssetID
                    updated_lines.append(f"AssetID: {new_asset_id}")
                    asset_id_found = True
                elif trimmed.startswith('system_message:'):
                    # Replace existing system message
                    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    if old_asset_id:
                        message = f"system_message: {timestamp}: Converted AssetID {old_asset_id} to server AssetID {new_asset_id}"
                    else:
                        message = f"system_message: {timestamp}: Generated new server AssetID {new_asset_id}"
                    updated_lines.append(message)
                    system_message_found = True
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        return '\n'.join(updated_lines)


class AssetIDConverter:
    """Handles AssetID conversion logic similar to Obsidian plugin."""
    
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
    
    async def convert_episode_asset_id(self, episode_number: str) -> ConversionResponse:
        """Convert episode AssetID - equivalent to plugin's episode context."""
        try:
            # Find episode info.md file
            episode_path = EPISODES_ROOT / episode_number
            info_file = episode_path / "info.md"
            
            if not info_file.exists():
                raise HTTPException(status_code=404, detail=f"Episode {episode_number} info.md not found")
            
            # Read current content
            content = FileManager.read_file(info_file)
            
            # Extract current AssetID
            current_asset_id = FileManager.extract_asset_id_from_frontmatter(content)
            episode_num = FileManager.extract_episode_number_from_frontmatter(content)
            slug = FileManager.extract_slug_from_frontmatter(content)
            
            # Check if already a server AssetID
            if current_asset_id and self._is_server_asset_id(current_asset_id):
                return ConversionResponse(
                    success=True,
                    message=f"Episode {episode_number} already has server AssetID: {current_asset_id}",
                    old_asset_id=current_asset_id,
                    new_asset_id=current_asset_id,
                    file_path=str(info_file),
                    context_type="episode",
                    conversions_count=0
                )
            
            # Generate new server AssetID
            request = NewAssetIDRequest(
                asset_type="episode",
                episode_number=episode_num or int(episode_number),
                slug=slug,
                context={"conversion_source": "backend_api", "file_path": str(info_file)}
            )
            
            # Use existing unified endpoint
            result = await create_new_asset_id(request, {"username": self.user_id}, self.db)
            new_asset_id = result["asset_id"]
            
            # Update file content
            updated_content = FileManager.replace_asset_id_in_frontmatter(
                content, current_asset_id, new_asset_id
            )
            
            # Write back to file
            FileManager.write_file(info_file, updated_content)
            
            logger.info(f"Converted episode {episode_number} AssetID: {current_asset_id} -> {new_asset_id}")
            
            return ConversionResponse(
                success=True,
                message=f"Converted episode {episode_number} AssetID",
                old_asset_id=current_asset_id,
                new_asset_id=new_asset_id,
                file_path=str(info_file),
                context_type="episode",
                conversions_count=1
            )
            
        except Exception as e:
            logger.error(f"Failed to convert episode {episode_number} AssetID: {e}")
            raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    
    async def convert_segment_asset_id(self, episode_number: str, segment_filename: str) -> ConversionResponse:
        """Convert segment AssetID - equivalent to plugin's segment context."""
        try:
            # Find segment file
            episode_path = EPISODES_ROOT / episode_number
            rundown_path = episode_path / "rundown"
            segment_file = rundown_path / f"{segment_filename}.md"
            
            if not segment_file.exists():
                raise HTTPException(status_code=404, detail=f"Segment file {segment_filename}.md not found")
            
            # Read current content
            content = FileManager.read_file(segment_file)
            
            # Extract current AssetID and metadata
            current_asset_id = FileManager.extract_asset_id_from_frontmatter(content)
            slug = FileManager.extract_slug_from_frontmatter(content)
            
            # Check if already a server AssetID
            if current_asset_id and self._is_server_asset_id(current_asset_id):
                return ConversionResponse(
                    success=True,
                    message=f"Segment {segment_filename} already has server AssetID: {current_asset_id}",
                    old_asset_id=current_asset_id,
                    new_asset_id=current_asset_id,
                    file_path=str(segment_file),
                    context_type="segment",
                    conversions_count=0
                )
            
            # Find parent episode AssetID
            parent_asset_id = await self._find_parent_episode_asset_id(episode_number)
            
            # Generate new server AssetID
            request = NewAssetIDRequest(
                asset_type="segment",
                slug=slug or segment_filename,
                parent_asset_id=parent_asset_id,
                context={"conversion_source": "backend_api", "file_path": str(segment_file)}
            )
            
            # Use existing unified endpoint
            result = await create_new_asset_id(request, {"username": self.user_id}, self.db)
            new_asset_id = result["asset_id"]
            
            # Update file content
            updated_content = FileManager.replace_asset_id_in_frontmatter(
                content, current_asset_id, new_asset_id
            )
            
            # Write back to file
            FileManager.write_file(segment_file, updated_content)
            
            logger.info(f"Converted segment {segment_filename} AssetID: {current_asset_id} -> {new_asset_id}")
            
            return ConversionResponse(
                success=True,
                message=f"Converted segment {segment_filename} AssetID",
                old_asset_id=current_asset_id,
                new_asset_id=new_asset_id,
                file_path=str(segment_file),
                context_type="segment",
                conversions_count=1
            )
            
        except Exception as e:
            logger.error(f"Failed to convert segment {segment_filename} AssetID: {e}")
            raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    
    async def convert_cue_asset_ids(self, episode_number: str, segment_filename: str) -> ConversionResponse:
        """Convert all cue AssetIDs in a segment file."""
        try:
            # Find segment file
            episode_path = EPISODES_ROOT / episode_number
            rundown_path = episode_path / "rundown"
            segment_file = rundown_path / f"{segment_filename}.md"
            
            if not segment_file.exists():
                raise HTTPException(status_code=404, detail=f"Segment file {segment_filename}.md not found")
            
            # Read current content
            content = FileManager.read_file(segment_file)
            
            # Find parent segment AssetID
            parent_asset_id = FileManager.extract_asset_id_from_frontmatter(content)
            if not parent_asset_id:
                raise HTTPException(status_code=400, detail="Segment must have AssetID before converting cues")
            
            # Extract all cue blocks
            cue_blocks = self._extract_cue_blocks(content)
            
            if not cue_blocks:
                return ConversionResponse(
                    success=True,
                    message="No cue blocks found to convert",
                    file_path=str(segment_file),
                    context_type="cue",
                    conversions_count=0
                )
            
            # Convert each cue block
            updated_content = content
            conversions = 0
            
            for cue_data in cue_blocks:
                if cue_data.get('AssetID'):
                    # Check if already a server AssetID
                    if self._is_server_asset_id(cue_data['AssetID']):
                        continue  # Skip already converted cues
                    
                    # Generate new server AssetID for cue
                    request = NewAssetIDRequest(
                        asset_type="cue",
                        slug=cue_data.get('slug', 'cue'),
                        parent_asset_id=parent_asset_id,
                        cue_type=cue_data.get('type', 'UNKNOWN'),
                        context={"conversion_source": "backend_api", "file_path": str(segment_file)}
                    )
                    
                    result = await create_new_asset_id(request, {"username": self.user_id}, self.db)
                    new_cue_asset_id = result["asset_id"]
                    
                    # Replace in content
                    old_line = f"[AssetID: {cue_data['AssetID']}]"
                    new_line = f"[AssetID: {new_cue_asset_id}]"
                    updated_content = updated_content.replace(old_line, new_line)
                    conversions += 1
            
            # Write back to file
            FileManager.write_file(segment_file, updated_content)
            
            logger.info(f"Converted {conversions} cue AssetIDs in {segment_filename}")
            
            return ConversionResponse(
                success=True,
                message=f"Converted {conversions} cue AssetIDs in {segment_filename}",
                file_path=str(segment_file),
                context_type="cue",
                conversions_count=conversions
            )
            
        except Exception as e:
            logger.error(f"Failed to convert cue AssetIDs in {segment_filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    
    async def _find_parent_episode_asset_id(self, episode_number: str) -> Optional[str]:
        """Find parent episode AssetID."""
        episode_path = EPISODES_ROOT / episode_number
        info_file = episode_path / "info.md"
        
        if info_file.exists():
            content = FileManager.read_file(info_file)
            return FileManager.extract_asset_id_from_frontmatter(content)
        
        return None
    
    def _extract_cue_blocks(self, content: str) -> list[Dict[str, Any]]:
        """Extract cue block data from content."""
        cue_blocks = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if '<!-- Begin Cue -->' in line:
                # Found start of cue block
                cue_data = {}
                i += 1
                
                # Parse cue fields until End Cue
                while i < len(lines) and '<!-- End Cue -->' not in lines[i]:
                    cue_line = lines[i].strip()
                    # Match [Field: Value] pattern
                    field_match = re.match(r'^\[(\w+):\s*(.+)\]$', cue_line)
                    if field_match:
                        field_name = field_match.group(1)
                        field_value = field_match.group(2).strip()
                        
                        # Map fields (similar to cueBlockParser.ts)
                        if field_name.lower() == 'type':
                            cue_data['type'] = field_value
                        elif field_name.lower() == 'assetid':
                            cue_data['AssetID'] = field_value
                        elif field_name.lower() == 'slug':
                            cue_data['slug'] = field_value
                        elif field_name.lower() == 'description':
                            cue_data['description'] = field_value
                        elif field_name.lower() == 'mediaurl':
                            cue_data['MediaURL'] = field_value
                    
                    i += 1
                
                if cue_data:
                    cue_blocks.append(cue_data)
            
            i += 1
        
        return cue_blocks
    
    def _is_server_asset_id(self, asset_id: str) -> bool:
        """
        Check if AssetID is from server (vs local).
        Server AssetIDs are typically longer, uppercase, alphanumeric strings.
        Local AssetIDs are typically shorter with underscores, lowercase, date patterns.
        """
        if not asset_id:
            return False
        
        # Server AssetIDs typically:
        # - Are 10+ characters long
        # - Contain mostly uppercase letters and numbers
        # - Don't contain common local patterns (underscores, dates)
        
        # Check for common local patterns
        local_patterns = [
            r'^\w+_\d{8}_\d+$',  # gfx_20250816_001
            r'^LOCAL-',           # LOCAL- prefix
            r'^\w+_\d{4}$',      # type_year pattern
            r'^\w+\d{4}$',       # type+year pattern
        ]
        
        for pattern in local_patterns:
            if re.match(pattern, asset_id):
                return False
        
        # Server AssetIDs are typically long and mostly uppercase
        if len(asset_id) >= 10 and asset_id.isupper() and asset_id.isalnum():
            return True
        
        # Check if exists in AssetID registry (most reliable check)
        try:
            from models_assetid import AssetIDRegistry
            registry_entry = self.db.query(AssetIDRegistry).filter(
                AssetIDRegistry.asset_id == asset_id
            ).first()
            return registry_entry is not None
        except Exception:
            # If database check fails, fall back to pattern matching
            pass
        
        return False


class AssetIDScanner:
    """Scans filesystem for AssetIDs and identifies conversion needs."""
    
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.converter = AssetIDConverter(db, user_id)
    
    async def scan_all_assets(self, episode_filter: Optional[str] = None) -> ScanResponse:
        """
        Scan all episodes for AssetIDs and identify conversion needs.
        
        Args:
            episode_filter: Optional episode number to scan only that episode
        """
        try:
            assets_found = []
            
            if episode_filter:
                # Scan specific episode
                episode_assets = await self._scan_episode(episode_filter)
                assets_found.extend(episode_assets)
            else:
                # Scan all episodes
                if EPISODES_ROOT.exists():
                    for episode_dir in EPISODES_ROOT.iterdir():
                        if episode_dir.is_dir() and episode_dir.name.isdigit():
                            episode_assets = await self._scan_episode(episode_dir.name)
                            assets_found.extend(episode_assets)
            
            # Analyze results
            total_count = len(assets_found)
            server_count = sum(1 for asset in assets_found if asset.is_server_asset)
            local_count = sum(1 for asset in assets_found if not asset.is_server_asset)
            needs_conversion_count = sum(1 for asset in assets_found if asset.needs_conversion)
            
            # Generate suggested API calls
            suggested_conversions = []
            for asset in assets_found:
                if asset.needs_conversion and asset.conversion_api_call:
                    if asset.conversion_api_call not in suggested_conversions:
                        suggested_conversions.append(asset.conversion_api_call)
            
            message = f"Scanned {total_count} AssetIDs: {server_count} server, {local_count} local, {needs_conversion_count} need conversion"
            
            return ScanResponse(
                success=True,
                message=message,
                total_assets_found=total_count,
                server_assets_count=server_count,
                local_assets_count=local_count,
                conversion_needed_count=needs_conversion_count,
                assets=assets_found,
                suggested_conversions=suggested_conversions
            )
            
        except Exception as e:
            logger.error(f"Failed to scan AssetIDs: {e}")
            raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
    
    async def _scan_episode(self, episode_number: str) -> List[AssetIDScanResult]:
        """Scan a specific episode for AssetIDs."""
        assets = []
        episode_path = EPISODES_ROOT / episode_number
        
        if not episode_path.exists():
            return assets
        
        # Scan episode info.md
        info_file = episode_path / "info.md"
        if info_file.exists():
            episode_asset = await self._scan_episode_info(episode_number, info_file)
            if episode_asset:
                assets.append(episode_asset)
        
        # Scan rundown segments
        rundown_path = episode_path / "rundown"
        if rundown_path.exists():
            for segment_file in rundown_path.glob("*.md"):
                segment_name = segment_file.stem
                
                # Scan segment frontmatter
                segment_asset = await self._scan_segment_file(episode_number, segment_name, segment_file)
                if segment_asset:
                    assets.append(segment_asset)
                
                # Scan cue blocks in segment
                cue_assets = await self._scan_cue_blocks(episode_number, segment_name, segment_file)
                assets.extend(cue_assets)
        
        return assets
    
    async def _scan_episode_info(self, episode_number: str, info_file: Path) -> Optional[AssetIDScanResult]:
        """Scan episode info.md for AssetID."""
        try:
            content = FileManager.read_file(info_file)
            asset_id = FileManager.extract_asset_id_from_frontmatter(content)
            
            if not asset_id:
                return None
            
            is_server = self.converter._is_server_asset_id(asset_id)
            needs_conversion = not is_server
            
            conversion_call = None
            if needs_conversion:
                conversion_call = f"POST /api/convertID/episode/{episode_number}"
            
            return AssetIDScanResult(
                asset_id=asset_id,
                file_path=str(info_file),
                context_type="episode",
                episode_number=episode_number,
                is_server_asset=is_server,
                needs_conversion=needs_conversion,
                conversion_api_call=conversion_call
            )
            
        except Exception as e:
            logger.warning(f"Error scanning episode {episode_number}: {e}")
            return None
    
    async def _scan_segment_file(self, episode_number: str, segment_name: str, segment_file: Path) -> Optional[AssetIDScanResult]:
        """Scan segment file frontmatter for AssetID."""
        try:
            content = FileManager.read_file(segment_file)
            asset_id = FileManager.extract_asset_id_from_frontmatter(content)
            
            if not asset_id:
                return None
            
            is_server = self.converter._is_server_asset_id(asset_id)
            needs_conversion = not is_server
            
            conversion_call = None
            if needs_conversion:
                conversion_call = f"POST /api/convertID/segment/{episode_number}/{segment_name}"
            
            return AssetIDScanResult(
                asset_id=asset_id,
                file_path=str(segment_file),
                context_type="segment",
                episode_number=episode_number,
                segment_name=segment_name,
                is_server_asset=is_server,
                needs_conversion=needs_conversion,
                conversion_api_call=conversion_call
            )
            
        except Exception as e:
            logger.warning(f"Error scanning segment {segment_name}: {e}")
            return None
    
    async def _scan_cue_blocks(self, episode_number: str, segment_name: str, segment_file: Path) -> List[AssetIDScanResult]:
        """Scan cue blocks in segment file for AssetIDs."""
        assets = []
        
        try:
            content = FileManager.read_file(segment_file)
            cue_blocks = self.converter._extract_cue_blocks(content)
            
            segment_has_cues_needing_conversion = False
            
            for cue_data in cue_blocks:
                asset_id = cue_data.get('AssetID')
                if not asset_id:
                    continue
                
                is_server = self.converter._is_server_asset_id(asset_id)
                needs_conversion = not is_server
                
                if needs_conversion:
                    segment_has_cues_needing_conversion = True
                
                # For cues, we batch convert per segment, so all cues point to same API call
                conversion_call = None
                if segment_has_cues_needing_conversion:
                    conversion_call = f"POST /api/convertID/cues/{episode_number}/{segment_name}"
                
                assets.append(AssetIDScanResult(
                    asset_id=asset_id,
                    file_path=str(segment_file),
                    context_type="cue",
                    episode_number=episode_number,
                    segment_name=segment_name,
                    cue_type=cue_data.get('type', 'UNKNOWN'),
                    is_server_asset=is_server,
                    needs_conversion=needs_conversion,
                    conversion_api_call=conversion_call
                ))
            
        except Exception as e:
            logger.warning(f"Error scanning cue blocks in {segment_name}: {e}")
        
        return assets


@router.get("/scanAssetIDs")
async def scan_asset_ids(
    episode: Optional[str] = None,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> ScanResponse:
    """
    Scan filesystem for AssetIDs and identify conversion needs.
    
    **Parameters:**
    - `episode`: Optional episode number to scan only that episode (e.g., "0236")
    
    **Returns:**
    - Complete inventory of all AssetIDs found
    - Classification of server vs local AssetIDs  
    - List of suggested API calls for conversion
    - Database verification of server AssetIDs
    
    **Example Usage:**
    - `GET /api/scanAssetIDs` - Scan all episodes
    - `GET /api/scanAssetIDs?episode=0236` - Scan only episode 0236
    """
    user_id = current_user.get("username", current_user.get("client_name", "api_user"))
    scanner = AssetIDScanner(db, user_id)
    return await scanner.scan_all_assets(episode)


@router.get("/scanAssetIDs/{episode_number}")
async def scan_episode_asset_ids(
    episode_number: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> ScanResponse:
    """
    Scan specific episode for AssetIDs and identify conversion needs.
    
    **Convenience endpoint** for scanning a single episode.
    """
    user_id = current_user.get("username", current_user.get("client_name", "api_user"))
    scanner = AssetIDScanner(db, user_id)
    return await scanner.scan_all_assets(episode_number)


@router.post("/convertID/episode/{episode_number}")
async def convert_episode_asset_id(
    episode_number: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> ConversionResponse:
    """
    Convert episode AssetID from local to server-registered.
    
    **Equivalent to**: Obsidian plugin Alt+9 on episode info.md
    """
    user_id = current_user.get("username", current_user.get("client_name", "api_user"))
    converter = AssetIDConverter(db, user_id)
    return await converter.convert_episode_asset_id(episode_number)


@router.post("/convertID/segment/{episode_number}/{segment_filename}")
async def convert_segment_asset_id(
    episode_number: str,
    segment_filename: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> ConversionResponse:
    """
    Convert segment AssetID from local to server-registered.
    
    **Equivalent to**: Obsidian plugin Alt+9 on segment frontmatter
    """
    user_id = current_user.get("username", current_user.get("client_name", "api_user"))
    converter = AssetIDConverter(db, user_id)
    return await converter.convert_segment_asset_id(episode_number, segment_filename)


@router.post("/convertID/cues/{episode_number}/{segment_filename}")
async def convert_cue_asset_ids(
    episode_number: str,
    segment_filename: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> ConversionResponse:
    """
    Convert all cue AssetIDs in a segment from local to server-registered.
    
    **Equivalent to**: Obsidian plugin Alt+9 on each cue block
    """
    user_id = current_user.get("username", current_user.get("client_name", "api_user"))
    converter = AssetIDConverter(db, user_id)
    return await converter.convert_cue_asset_ids(episode_number, segment_filename)


@router.post("/convertID/all/{episode_number}")
async def convert_all_asset_ids(
    episode_number: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> ConversionResponse:
    """
    Convert ALL AssetIDs in an episode (episode + all segments + all cues).
    
    **Comprehensive conversion**: Episode info.md + all rundown items + all cue blocks
    """
    user_id = current_user.get("username", current_user.get("client_name", "api_user"))
    converter = AssetIDConverter(db, user_id)
    
    try:
        total_conversions = 0
        results = []
        
        # 1. Convert episode AssetID
        episode_result = await converter.convert_episode_asset_id(episode_number)
        results.append(f"Episode: {episode_result.message}")
        total_conversions += episode_result.conversions_count
        
        # 2. Find all segment files
        episode_path = EPISODES_ROOT / episode_number / "rundown"
        if episode_path.exists():
            for segment_file in episode_path.glob("*.md"):
                segment_name = segment_file.stem
                
                # Convert segment AssetID
                segment_result = await converter.convert_segment_asset_id(episode_number, segment_name)
                results.append(f"Segment {segment_name}: {segment_result.message}")
                total_conversions += segment_result.conversions_count
                
                # Convert cue AssetIDs
                cue_result = await converter.convert_cue_asset_ids(episode_number, segment_name)
                if cue_result.conversions_count > 0:
                    results.append(f"Cues in {segment_name}: {cue_result.message}")
                    total_conversions += cue_result.conversions_count
        
        return ConversionResponse(
            success=True,
            message=f"Converted all AssetIDs in episode {episode_number}. Details: " + "; ".join(results),
            file_path=str(EPISODES_ROOT / episode_number),
            context_type="all",
            conversions_count=total_conversions
        )
        
    except Exception as e:
        logger.error(f"Failed to convert all AssetIDs in episode {episode_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk conversion failed: {str(e)}")