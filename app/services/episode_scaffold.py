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
from models_episode import EpisodeTemplate
from models_episode import EpisodeTemplateCreate, EpisodeTemplateResponse, BlueprintTemplateResponse
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
            # Get highest episode number from database
            latest_episode = self.db.query(EpisodeTemplate).order_by(desc(EpisodeTemplate.episode_number)).first()
            
            if latest_episode:
                try:
                    latest_num = int(latest_episode.episode_number)
                    next_num = latest_num + 1
                except ValueError:
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
        existing_episode = self.db.query(EpisodeTemplate).filter(
            EpisodeTemplate.episode_number == episode_number
        ).first()
        
        if existing_episode:
            return False
        
        # Check filesystem
        episode_path = self.media_paths.get_episode_path(episode_number)
        if episode_path.exists():
            return False
        
        return True
    
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
        info_metadata["id"] = "0"  # Placeholder, will be updated by other systems
        
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
    
    async def create_episode(self, request: EpisodeTemplateCreate, user_id: Optional[int] = None, 
                           organization_id: Optional[int] = None) -> EpisodeTemplateResponse:
        """Create a new episode from blueprint template"""
        try:
            # Generate episode number if not provided
            episode_number = request.episode_number
            if not episode_number:
                episode_number = await self.get_next_episode_number()
            
            # Validate episode number
            if not await self.validate_episode_number(episode_number):
                raise HTTPException(status_code=409, detail=f"Episode {episode_number} already exists")
            
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
            
            # Create episode directory structure
            episode_path = self.media_paths.get_episode_path(episode_number)
            await self.create_directory_structure(template, episode_path)
            
            # Generate and write info.md
            info_content = await self.generate_info_md(template, episode_number, request.episode_metadata)
            info_file = episode_path / "info.md"
            info_file.write_text(info_content, encoding='utf-8')
            
            # Create database record
            episode = EpisodeTemplate(
                episode_number=episode_number,
                title=request.title,
                description=request.description,
                episode_metadata=request.episode_metadata,
                template_id=template.id,
                status="draft",
                created_by=user_id,
                organization_id=organization_id,
                file_path=str(episode_path)
            )
            
            self.db.add(episode)
            self.db.commit()
            self.db.refresh(episode)
            
            logger.info(f"Created episode {episode_number} using template {template.name}")
            
            return EpisodeTemplateResponse.from_orm(episode)
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating episode: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create episode: {e}")
    
    async def get_episode_by_number(self, episode_number: str) -> Optional[EpisodeTemplateResponse]:
        """Get episode information by number"""
        episode = self.db.query(EpisodeTemplate).filter(
            EpisodeTemplate.episode_number == episode_number
        ).first()
        
        if episode:
            return EpisodeTemplateResponse.from_orm(episode)
        return None
    
    async def list_episodes(self, skip: int = 0, limit: int = 100) -> List[EpisodeTemplateResponse]:
        """List all episodes"""
        episodes = self.db.query(EpisodeTemplate).order_by(
            desc(EpisodeTemplate.episode_number)
        ).offset(skip).limit(limit).all()
        
        return [EpisodeTemplateResponse.from_orm(episode) for episode in episodes]