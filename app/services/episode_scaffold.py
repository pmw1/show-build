"""
Episode scaffolding service - Creates new episodes from blueprint templates
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException

from models_episode import BlueprintTemplate, BlueprintNode
from models_episode import BlueprintCreate, BlueprintResponse, BlueprintTemplateResponse
from core.media_paths import MediaPathManager
import logging

logger = logging.getLogger(__name__)

class EpisodeScaffoldService:
    """Service for creating new episodes from blueprint templates"""
    
    def __init__(self, db: Session, media_paths: MediaPathManager):
        self.db = db
        self.media_paths = media_paths
    
    async def get_next_episode_number(self) -> str:
        """Generate next available episode number"""
        try:
            # Get highest episode number from main episodes table
            from models_v2 import Episode
            latest_episode = self.db.query(Episode).order_by(desc(Episode.episode_number)).first()

            if latest_episode:
                try:
                    latest_num = int(latest_episode.episode_number)
                    next_num = latest_num + 1
                except (ValueError, TypeError):
                    # Handle non-numeric episode numbers
                    logger.warning(f"Non-numeric episode number found: {latest_episode.episode_number}")
                    next_num = 1
            else:
                next_num = 1
            
            # Also check filesystem for conflicts
            episodes_root = self.media_paths.get_episodes_root()
            if episodes_root.exists():
                existing_dirs = [d.name for d in episodes_root.iterdir() if d.is_dir() and d.name.isdigit()]
                if existing_dirs:
                    fs_latest = max([int(d) for d in existing_dirs if d.isdigit()])
                    next_num = max(next_num, fs_latest + 1)
            
            return f"{next_num:04d}"
            
        except Exception as e:
            logger.error(f"Error generating next episode number: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate episode number")
    
    async def get_available_templates(self) -> List[BlueprintTemplateResponse]:
        """Get all active blueprint templates"""
        templates = self.db.query(BlueprintTemplate).filter(
            BlueprintTemplate.is_active == True,
            BlueprintTemplate.template_type == "episode"
        ).order_by(BlueprintTemplate.is_default.desc(), BlueprintTemplate.name).all()
        
        return [BlueprintTemplateResponse.from_orm(template) for template in templates]
    
    async def get_default_template(self) -> Optional[BlueprintTemplate]:
        """Get the default blueprint template"""
        return self.db.query(BlueprintTemplate).filter(
            BlueprintTemplate.is_active == True,
            BlueprintTemplate.is_default == True,
            BlueprintTemplate.template_type == "episode"
        ).first()
    
    async def validate_episode_number(self, episode_number: str) -> bool:
        """Validate that episode number is available"""
        # Check database
        from models_v2 import Episode
        existing_episode = self.db.query(Episode).filter(
            Episode.episode_number == int(episode_number)
        ).first()

        if existing_episode:
            return False

        # Check filesystem
        episode_path = self.media_paths.get_episode_path(episode_number)
        if episode_path.exists():
            return False

        return True
    
    async def get_episode_conflicts(self, episode_number: str) -> Dict[str, Any]:
        """Get detailed information about episode conflicts"""
        from models_v2 import Episode
        conflicts = []

        # Check episodes table
        existing_episode = self.db.query(Episode).filter(
            Episode.episode_number == int(episode_number)
        ).first()
        if existing_episode:
            conflicts.append(f"episodes database table (id: {existing_episode.id})")

        
        # Check filesystem
        episode_path = self.media_paths.get_episode_path(episode_number)
        if episode_path.exists():
            conflicts.append(f"filesystem directory: {episode_path}")
        
        return {
            "has_conflicts": len(conflicts) > 0,
            "conflicts": conflicts,
            "episode_number": episode_number
        }
    
    async def create_directory_structure(self, template: BlueprintTemplate, episode_path: Path) -> None:
        """Create directory structure from blueprint template"""
        try:
            # Get root nodes (no parent)
            root_nodes = self.db.query(BlueprintNode).filter(
                BlueprintNode.template_id == template.id,
                BlueprintNode.parent_id.is_(None)
            ).order_by(BlueprintNode.sort_order).all()
            
            # Create episode root directory
            episode_path.mkdir(parents=True, exist_ok=True)
            
            # Recursively create structure
            await self._create_node_structure(root_nodes, episode_path)
            
        except Exception as e:
            logger.error(f"Error creating directory structure: {e}")
            # Cleanup on failure
            if episode_path.exists():
                import shutil
                shutil.rmtree(episode_path, ignore_errors=True)
            raise HTTPException(status_code=500, detail=f"Failed to create directory structure: {e}")
    
    async def _create_node_structure(self, nodes: List[BlueprintNode], parent_path: Path) -> None:
        """Recursively create directory/file structure from nodes"""
        for node in nodes:
            node_path = parent_path / node.name
            
            if node.node_type == "directory":
                node_path.mkdir(exist_ok=True)
                
                # Get children of this node
                children = self.db.query(BlueprintNode).filter(
                    BlueprintNode.parent_id == node.id
                ).order_by(BlueprintNode.sort_order).all()
                
                if children:
                    await self._create_node_structure(children, node_path)
                    
            elif node.node_type == "file":
                # Create file with content
                content = node.content or ""
                node_path.write_text(content, encoding='utf-8')
    
    async def generate_info_md(self, template: BlueprintTemplate, episode_number: str, 
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """Generate info.md content with metadata"""
        # Start with template metadata
        info_metadata = template.template_metadata.copy() if template.template_metadata else {}
        
        # Update with provided metadata
        if metadata:
            info_metadata.update(metadata)
        
        # Set episode-specific fields
        info_metadata["episode_number"] = episode_number
        # Use AssetID if provided in metadata, otherwise use placeholder
        info_metadata["id"] = metadata.get("asset_id", "0") if metadata else "0"
        
        # Generate YAML frontmatter
        frontmatter_lines = ["---"]
        for key, value in info_metadata.items():
            if isinstance(value, str) and ("\n" in value or value.startswith(" ")):
                # Multi-line string
                frontmatter_lines.append(f"{key}: |")
                for line in value.split("\n"):
                    frontmatter_lines.append(f"  {line}")
            else:
                frontmatter_lines.append(f"{key}: \"{value}\"")
        frontmatter_lines.append("---")
        frontmatter_lines.append("")
        frontmatter_lines.append("## LLM Processing Notes")
        frontmatter_lines.append("**What you need to know:**")
        frontmatter_lines.append("- Frontmatter fields: Assume all key:value pairs contained in the Frontmatter YAML have values stored as strings.  Therefore numerical values stored in frontmatter will need to be converted to the proper type to process correctly if something other than string is needed.")
        frontmatter_lines.append("")
        
        return "\n".join(frontmatter_lines)
    
    async def create_episode(self, request: BlueprintCreate, user_id: Optional[int] = None,
                           organization_id: Optional[int] = None) -> BlueprintResponse:
        """Create a new episode from blueprint template with AssetID generation"""
        try:
            # Generate episode number if not provided
            episode_number = request.episode_number
            if not episode_number:
                episode_number = await self.get_next_episode_number()
            
            # Validate episode number with detailed conflict reporting
            conflict_info = await self.get_episode_conflicts(episode_number)
            if conflict_info["has_conflicts"]:
                conflicts_text = ", ".join(conflict_info["conflicts"])
                raise HTTPException(
                    status_code=409, 
                    detail=f"Episode {episode_number} already exists in: {conflicts_text}"
                )
            
            # Get template
            template = None
            if request.template_id:
                template = self.db.query(BlueprintTemplate).filter(
                    BlueprintTemplate.id == request.template_id,
                    BlueprintTemplate.is_active == True
                ).first()
                if not template:
                    raise HTTPException(status_code=404, detail="Blueprint template not found")
            else:
                template = await self.get_default_template()
                if not template:
                    raise HTTPException(status_code=404, detail="No default blueprint template found")
            
            # Generate AssetID via the unified endpoint (CRITICAL: all AssetIDs must be logged)
            from services.asset_id import AssetIDService
            user_identifier = str(user_id) if user_id else "episode_scaffold_service"
            
            asset_id = AssetIDService.request_asset_id(
                db=self.db,
                entity_type="episode",
                reason="episode_scaffold_create",
                requested_by=user_identifier,
                linked_to=[],
                context={
                    "episode_number": episode_number,
                    "template_id": template.id,
                    "template_name": template.name,
                    "title": request.title,
                    "source": "episode_scaffold_service",
                    "blueprint_template_type": template.template_type
                }
            )
            
            # Create episode directory structure
            episode_path = self.media_paths.get_episode_path(episode_number)
            await self.create_directory_structure(template, episode_path)
            
            # Prepare enhanced metadata with AssetID
            enhanced_metadata = request.episode_metadata.copy() if request.episode_metadata else {}
            enhanced_metadata.update({
                "asset_id": asset_id,
                "episode_number": episode_number,
                "template_id": template.id,
                "template_name": template.name
            })
            
            # Generate and write info.md with AssetID included
            info_content = await self.generate_info_md(template, episode_number, enhanced_metadata)
            info_file = episode_path / "info.md"
            info_file.write_text(info_content, encoding='utf-8')
            
            # Create record in main episodes table
            from models_v2 import Episode
            from datetime import datetime

            episodes_record = Episode(
                asset_id=asset_id,
                season_id=1,  # Default season
                episode_number=int(episode_number),
                title=request.title.strip() if request.title and request.title.strip() else f"Episode {episode_number}",  # Provide default title if None/empty
                slug=f"episode-{episode_number}",
                status="draft",
                template_type=template.template_type,
                template_name=template.name,
                # Store airdate if provided
                air_date=datetime.fromisoformat(enhanced_metadata['airdate']) if enhanced_metadata.get('airdate') else None,
                duration_formatted=enhanced_metadata.get('duration', '01:00:00')
            )

            self.db.add(episodes_record)
            self.db.commit()
            self.db.refresh(episodes_record)

            logger.info(f"Created episode {episode_number} with AssetID {asset_id} using template {template.name} in episodes table")

            # Create rundown items from template (with inheritance)
            await self.create_rundown_items_from_template(template, episodes_record.id, episode_number)

            # Return response based on the episodes record
            return BlueprintResponse(
                id=episodes_record.id,
                episode_number=episode_number,
                title=episodes_record.title,
                description="",
                template_id=template.id,
                status=episodes_record.status,
                created_by=user_id,
                organization_id=organization_id,
                file_path=str(episode_path),
                episode_metadata=enhanced_metadata,
                created_at=episodes_record.created_at,
                updated_at=episodes_record.updated_at
            )
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating episode: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create episode: {e}")
    
    async def get_episode_by_number(self, episode_number: str) -> Optional[BlueprintResponse]:
        """Get episode information by number"""
        from models_v2 import Episode
        episode = self.db.query(Episode).filter(
            Episode.episode_number == int(episode_number)
        ).first()

        if episode:
            # Convert Episode to BlueprintResponse format
            episode_path = self.media_paths.get_episode_path(episode_number)
            return BlueprintResponse(
                id=episode.id,
                episode_number=str(episode.episode_number).zfill(4),
                title=episode.title,
                description="",
                template_id=None,
                status=episode.status,
                created_by=None,
                organization_id=None,
                file_path=str(episode_path),
                episode_metadata={},
                created_at=episode.created_at,
                updated_at=episode.updated_at
            )
        return None
    
    async def list_episodes(self, skip: int = 0, limit: int = 100) -> List[BlueprintResponse]:
        """List all episodes"""
        from models_v2 import Episode
        episodes = self.db.query(Episode).order_by(
            desc(Episode.episode_number)
        ).offset(skip).limit(limit).all()

        results = []
        for episode in episodes:
            episode_path = self.media_paths.get_episode_path(str(episode.episode_number).zfill(4))
            results.append(BlueprintResponse(
                id=episode.id,
                episode_number=str(episode.episode_number).zfill(4),
                title=episode.title,
                description="",
                template_id=None,
                status=episode.status,
                created_by=None,
                organization_id=None,
                file_path=str(episode_path),
                episode_metadata={},
                created_at=episode.created_at,
                updated_at=episode.updated_at
            ))
        return results

    async def create_rundown_items_from_template(self, template: BlueprintTemplate, episode_id: int, episode_number: str):
        """
        Create rundown items from blueprint template nodes (with cascading inheritance support).

        Args:
            template: The blueprint template (may have parent templates)
            episode_id: The episode record ID
            episode_number: Episode number string
        """
        from models_v2 import RundownItem

        # Get resolved nodes (includes inherited nodes from parent templates)
        resolved_nodes = template.get_resolved_nodes(self.db)

        # Filter for rundown_item type nodes only
        rundown_nodes = [node for node in resolved_nodes.values() if node.node_type == 'rundown_item']

        if not rundown_nodes:
            logger.info(f"No rundown item templates found in template {template.name}")
            return

        # Sort by sort_order
        rundown_nodes.sort(key=lambda n: n.sort_order)

        # Create rundown items
        created_count = 0
        for idx, node in enumerate(rundown_nodes):
            metadata = node.rundown_item_metadata or {}

            # Build script content with YAML frontmatter
            frontmatter_data = {
                'slug': metadata.get('slug', node.name.lower().replace(' ', '-')),
                'type': metadata.get('item_type', 'segment'),
                'order': (idx + 1) * 10,  # Spacing of 10 for future insertions
                'index': (idx + 1) * 10,
                'duration': metadata.get('duration', '00:05:00'),
                'status': metadata.get('status', 'draft'),
                'title': node.name
            }

            # Add YAML frontmatter to content
            script_content = "---\n"
            for key, value in frontmatter_data.items():
                if isinstance(value, str):
                    script_content += f"{key}: \"{value}\"\n"
                else:
                    script_content += f"{key}: {value}\n"
            script_content += "---\n\n"

            # Add template content if provided
            if node.content:
                script_content += node.content
            else:
                script_content += f"# {node.name}\n\n[Content to be added]\n"

            # Create rundown item
            rundown_item = RundownItem(
                episode_id=episode_id,
                title=node.name,
                slug=frontmatter_data['slug'],
                item_type=frontmatter_data['type'],
                order_in_rundown=frontmatter_data['order'],
                duration=frontmatter_data['duration'],
                status=frontmatter_data['status'],
                script_content=script_content
            )

            self.db.add(rundown_item)
            created_count += 1

        self.db.commit()
        logger.info(f"Created {created_count} rundown items for episode {episode_number} from template {template.name}")