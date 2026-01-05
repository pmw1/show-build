"""
Rundown Templates API Router
Manages rundown templates for automatic episode population
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from database import get_db
from auth.utils import get_current_user_or_key
from models_episode import (
    RundownTemplate,
    RundownTemplateItem,
    RundownTemplateCreate,
    RundownTemplateUpdate,
    RundownTemplateResponse,
    RundownTemplateItemCreate,
    RundownTemplateItemUpdate,
    RundownTemplateItemResponse,
    RundownTemplateClone,
    RundownTemplateExport,
    RundownTemplateImport
)
from typing import List, Optional
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(tags=["rundown-templates"])


@router.get("/", response_model=List[RundownTemplateResponse])
async def list_rundown_templates(
    organization_id: Optional[int] = None,
    episode_template_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """List all rundown templates with optional filtering"""
    try:
        query = db.query(RundownTemplate)

        if organization_id:
            query = query.filter(RundownTemplate.organization_id == organization_id)

        if episode_template_id:
            query = query.filter(RundownTemplate.episode_template_id == episode_template_id)

        if is_active is not None:
            query = query.filter(RundownTemplate.is_active == is_active)

        templates = query.order_by(RundownTemplate.sort_order, RundownTemplate.name).all()
        return templates

    except Exception as e:
        logger.error(f"Error listing rundown templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}", response_model=RundownTemplateResponse)
async def get_rundown_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Get a specific rundown template by ID"""
    try:
        template = db.query(RundownTemplate).filter(RundownTemplate.id == template_id).first()

        if not template:
            raise HTTPException(status_code=404, detail=f"Rundown template {template_id} not found")

        return template

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rundown template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=RundownTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_rundown_template(
    template_data: RundownTemplateCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Create a new rundown template"""
    try:
        # Check for duplicate name within organization and episode template
        existing = db.query(RundownTemplate).filter(
            and_(
                RundownTemplate.organization_id == template_data.organization_id,
                RundownTemplate.episode_template_id == template_data.episode_template_id,
                RundownTemplate.name == template_data.name
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Template '{template_data.name}' already exists for this organization and episode template"
            )

        # If this is set as default, unset other defaults
        if template_data.is_default:
            db.query(RundownTemplate).filter(
                and_(
                    RundownTemplate.organization_id == template_data.organization_id,
                    RundownTemplate.episode_template_id == template_data.episode_template_id,
                    RundownTemplate.is_default == True
                )
            ).update({"is_default": False})

        # Create template
        template = RundownTemplate(**template_data.model_dump())
        db.add(template)
        db.commit()
        db.refresh(template)

        logger.info(f"Created rundown template: {template.name} (ID: {template.id})")
        return template

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating rundown template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}", response_model=RundownTemplateResponse)
async def update_rundown_template(
    template_id: int,
    template_data: RundownTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Update an existing rundown template"""
    try:
        template = db.query(RundownTemplate).filter(RundownTemplate.id == template_id).first()

        if not template:
            raise HTTPException(status_code=404, detail=f"Rundown template {template_id} not found")

        # Check for name conflict if name is being changed
        if template_data.name and template_data.name != template.name:
            existing = db.query(RundownTemplate).filter(
                and_(
                    RundownTemplate.organization_id == template.organization_id,
                    RundownTemplate.episode_template_id == template.episode_template_id,
                    RundownTemplate.name == template_data.name,
                    RundownTemplate.id != template_id
                )
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Template '{template_data.name}' already exists"
                )

        # If setting as default, unset other defaults
        if template_data.is_default:
            db.query(RundownTemplate).filter(
                and_(
                    RundownTemplate.organization_id == template.organization_id,
                    RundownTemplate.episode_template_id == template.episode_template_id,
                    RundownTemplate.is_default == True,
                    RundownTemplate.id != template_id
                )
            ).update({"is_default": False})

        # Update template
        for field, value in template_data.model_dump(exclude_unset=True).items():
            setattr(template, field, value)

        db.commit()
        db.refresh(template)

        logger.info(f"Updated rundown template: {template.name} (ID: {template.id})")
        return template

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating rundown template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rundown_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Delete a rundown template"""
    try:
        template = db.query(RundownTemplate).filter(RundownTemplate.id == template_id).first()

        if not template:
            raise HTTPException(status_code=404, detail=f"Rundown template {template_id} not found")

        template_name = template.name
        db.delete(template)
        db.commit()

        logger.info(f"Deleted rundown template: {template_name} (ID: {template_id})")
        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting rundown template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Template Items Endpoints

@router.get("/{template_id}/items", response_model=List[RundownTemplateItemResponse])
async def get_template_items(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Get all items for a specific template"""
    try:
        template = db.query(RundownTemplate).filter(RundownTemplate.id == template_id).first()

        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

        items = db.query(RundownTemplateItem).filter(
            RundownTemplateItem.rundown_template_id == template_id
        ).order_by(RundownTemplateItem.sort_order).all()

        return items

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template items for template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/items", response_model=RundownTemplateItemResponse, status_code=status.HTTP_201_CREATED)
async def create_template_item(
    template_id: int,
    item_data: RundownTemplateItemCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Add a new item to a template"""
    try:
        template = db.query(RundownTemplate).filter(RundownTemplate.id == template_id).first()

        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

        item = RundownTemplateItem(
            rundown_template_id=template_id,
            **item_data.model_dump()
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        logger.info(f"Added item to template {template_id}: {item.title or item.item_type}")
        return item

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating template item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/items/{item_id}", response_model=RundownTemplateItemResponse)
async def update_template_item(
    item_id: int,
    item_data: RundownTemplateItemUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Update a template item"""
    try:
        item = db.query(RundownTemplateItem).filter(RundownTemplateItem.id == item_id).first()

        if not item:
            raise HTTPException(status_code=404, detail=f"Template item {item_id} not found")

        for field, value in item_data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)

        db.commit()
        db.refresh(item)

        logger.info(f"Updated template item {item_id}")
        return item

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating template item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Delete a template item"""
    try:
        item = db.query(RundownTemplateItem).filter(RundownTemplateItem.id == item_id).first()

        if not item:
            raise HTTPException(status_code=404, detail=f"Template item {item_id} not found")

        db.delete(item)
        db.commit()

        logger.info(f"Deleted template item {item_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting template item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/items/reorder", response_model=List[RundownTemplateItemResponse])
async def reorder_template_items(
    template_id: int,
    item_ids: List[int],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Reorder template items"""
    try:
        template = db.query(RundownTemplate).filter(RundownTemplate.id == template_id).first()

        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

        # Update sort_order for each item
        for index, item_id in enumerate(item_ids):
            item = db.query(RundownTemplateItem).filter(
                and_(
                    RundownTemplateItem.id == item_id,
                    RundownTemplateItem.rundown_template_id == template_id
                )
            ).first()

            if item:
                item.sort_order = index

        db.commit()

        # Return updated items
        items = db.query(RundownTemplateItem).filter(
            RundownTemplateItem.rundown_template_id == template_id
        ).order_by(RundownTemplateItem.sort_order).all()

        logger.info(f"Reordered items for template {template_id}")
        return items

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error reordering template items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Clone Template

@router.post("/{template_id}/clone", response_model=RundownTemplateResponse, status_code=status.HTTP_201_CREATED)
async def clone_rundown_template(
    template_id: int,
    clone_data: RundownTemplateClone,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Clone an existing rundown template"""
    try:
        # Get original template
        original = db.query(RundownTemplate).filter(RundownTemplate.id == template_id).first()

        if not original:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

        # Check for name conflict
        existing = db.query(RundownTemplate).filter(
            and_(
                RundownTemplate.organization_id == original.organization_id,
                RundownTemplate.episode_template_id == original.episode_template_id,
                RundownTemplate.name == clone_data.name
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Template '{clone_data.name}' already exists"
            )

        # Create new template
        new_template = RundownTemplate(
            name=clone_data.name,
            description=clone_data.description or f"Cloned from {original.name}",
            organization_id=original.organization_id,
            episode_template_id=original.episode_template_id,
            is_default=False,  # Clones are never default
            is_active=True,
            sort_order=original.sort_order
        )
        db.add(new_template)
        db.flush()  # Get the new template ID

        # Clone all items
        original_items = db.query(RundownTemplateItem).filter(
            RundownTemplateItem.rundown_template_id == template_id
        ).order_by(RundownTemplateItem.sort_order).all()

        for item in original_items:
            new_item = RundownTemplateItem(
                rundown_template_id=new_template.id,
                item_type=item.item_type,
                title=item.title,
                slug=item.slug,
                script_content=item.script_content,
                duration=item.duration,
                sort_order=item.sort_order,
                metadata=item.metadata
            )
            db.add(new_item)

        db.commit()
        db.refresh(new_template)

        logger.info(f"Cloned template {template_id} to new template {new_template.id} ('{new_template.name}')")
        return new_template

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cloning template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export/Import

@router.get("/{template_id}/export", response_model=RundownTemplateExport)
async def export_rundown_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Export a rundown template as JSON"""
    try:
        template = db.query(RundownTemplate).filter(RundownTemplate.id == template_id).first()

        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

        items = db.query(RundownTemplateItem).filter(
            RundownTemplateItem.rundown_template_id == template_id
        ).order_by(RundownTemplateItem.sort_order).all()

        return RundownTemplateExport(
            template=template,
            items=items
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=RundownTemplateResponse, status_code=status.HTTP_201_CREATED)
async def import_rundown_template(
    import_data: RundownTemplateImport,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Import a rundown template from JSON"""
    try:
        # Check for name conflict
        existing = db.query(RundownTemplate).filter(
            and_(
                RundownTemplate.organization_id == import_data.organization_id,
                RundownTemplate.episode_template_id == import_data.episode_template_id,
                RundownTemplate.name == import_data.name
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Template '{import_data.name}' already exists"
            )

        # Create template
        template = RundownTemplate(
            name=import_data.name,
            description=import_data.description,
            organization_id=import_data.organization_id,
            episode_template_id=import_data.episode_template_id,
            is_default=False,
            is_active=True,
            sort_order=0
        )
        db.add(template)
        db.flush()

        # Create items
        for item_data in import_data.items:
            item = RundownTemplateItem(
                rundown_template_id=template.id,
                **item_data.model_dump()
            )
            db.add(item)

        db.commit()
        db.refresh(template)

        logger.info(f"Imported template: {template.name} (ID: {template.id})")
        return template

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing template: {e}")
        raise HTTPException(status_code=500, detail=str(e))
