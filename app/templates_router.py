# app/templates_router.py

from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
from auth.utils import get_current_user_or_key
import os
import json
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import datetime

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use an environment variable for the base path, with a fallback for development
TEMPLATES_BASE_PATH = Path(os.getenv("TEMPLATES_ROOT", "/app/storage/templates"))

# Ensure the templates directory exists
TEMPLATES_BASE_PATH.mkdir(parents=True, exist_ok=True)

class Template(BaseModel):
    id: str = Field(..., description="Unique identifier for the template")
    name: str = Field(..., description="Name of the template")
    type: str = Field(..., description="Type of template (e.g., script, rundown)")
    content: str = Field(..., description="The actual template content")
    description: Optional[str] = Field(None, description="A brief description of the template")
    tags: List[str] = Field([], description="Tags for categorization")
    created: str = Field(description="Creation timestamp in ISO format")
    modified: str = Field(description="Last modification timestamp in ISO format")

def _read_template_file(file_path: Path) -> Dict[str, Any]:
    """Reads and parses a single JSON template file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _write_template_file(file_path: Path, data: Dict[str, Any]):
    """Writes data to a single JSON template file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

@router.get("/templates", response_model=List[Template], dependencies=[Depends(get_current_user_or_key)])
async def list_templates():
    """
    List all available templates.
    """
    templates = []
    try:
        for item in sorted(TEMPLATES_BASE_PATH.iterdir()):
            if item.is_file() and item.name.endswith('.json'):
                template_data = _read_template_file(item)
                templates.append(Template(**template_data))
        return templates
    except Exception as e:
        logger.error(f"Error listing templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while listing templates.")

@router.post("/templates", response_model=Template, status_code=201, dependencies=[Depends(get_current_user_or_key)])
async def create_template(template_data: Dict[str, Any] = Body(...)):
    """
    Create a new template.
    """
    try:
        now = datetime.datetime.utcnow().isoformat()
        # Generate a unique ID, e.g., based on timestamp
        template_id = str(int(datetime.datetime.utcnow().timestamp() * 1000))
        
        new_template = Template(
            id=template_id,
            name=template_data.get("name", "Untitled Template"),
            type=template_data.get("type", "script"),
            content=template_data.get("content", ""),
            description=template_data.get("description"),
            tags=template_data.get("tags", []),
            created=now,
            modified=now
        )
        
        file_path = TEMPLATES_BASE_PATH / f"{template_id}.json"
        _write_template_file(file_path, new_template.dict())
        
        logger.info(f"Template created: {file_path}")
        return new_template
    except Exception as e:
        logger.error(f"Error creating template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create template.")

@router.put("/templates/{template_id}", response_model=Template, dependencies=[Depends(get_current_user_or_key)])
async def update_template(template_id: str, template_data: Dict[str, Any] = Body(...)):
    """
    Update an existing template.
    """
    try:
        file_path = TEMPLATES_BASE_PATH / f"{template_id}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Template not found.")

        existing_data = _read_template_file(file_path)
        
        updated_template_data = existing_data.copy()
        updated_template_data.update(template_data)
        updated_template_data["modified"] = datetime.datetime.utcnow().isoformat()
        
        # Ensure ID and created timestamp are not overwritten
        updated_template_data["id"] = template_id
        updated_template_data["created"] = existing_data.get("created")

        updated_template = Template(**updated_template_data)
        
        _write_template_file(file_path, updated_template.dict())
        
        logger.info(f"Template updated: {file_path}")
        return updated_template
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating template '{template_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update template.")

@router.delete("/templates/{template_id}", status_code=204, dependencies=[Depends(get_current_user_or_key)])
async def delete_template(template_id: str):
    """
    Delete a template.
    """
    try:
        file_path = TEMPLATES_BASE_PATH / f"{template_id}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Template not found.")
        
        file_path.unlink()
        logger.info(f"Template deleted: {file_path}")
        return None # No content response
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting template '{template_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete template.")
