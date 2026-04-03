#!/usr/bin/env python3
"""
Script to populate blueprint templates with default directory structure
Run this after migration to initialize the blueprint system
"""
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from database import get_db, engine
from models_episode import BlueprintTemplate, BlueprintNode

# Add the app directory to the path so we can import models
APP_DIR = Path(__file__).parent / "app"
sys.path.insert(0, str(APP_DIR))

def create_default_blueprint_structure(db: Session, template_id: int):
    """Create the default episode directory structure for a template"""
    
    # Directory structure based on existing blueprint
    structure = [
        {"name": "assets", "type": "directory", "children": [
            {"name": "audio", "type": "directory"},
            {"name": "graphics", "type": "directory"},
            {"name": "images", "type": "directory", "children": [
                {"name": "guest", "type": "directory"}
            ]},
            {"name": "quotes", "type": "directory"},
            {"name": "unlinked", "type": "directory"},
            {"name": "video", "type": "directory"}
        ]},
        {"name": "captures", "type": "directory"},
        {"name": "distribute", "type": "directory"},
        {"name": "exports", "type": "directory"},
        {"name": "preshow", "type": "directory", "children": [
            {"name": "preshow notes.md", "type": "file", "content": "# Preshow Notes\n\n## Technical Setup\n- [ ] Check audio levels\n- [ ] Verify video feed\n- [ ] Test streaming connection\n\n## Content Preparation\n- [ ] Review rundown\n- [ ] Prepare graphics\n- [ ] Check guest connection\n\n## Final Checklist\n- [ ] All systems operational\n- [ ] Backup equipment ready\n- [ ] Emergency contacts available\n"}
        ]},
        {"name": "rundown", "type": "directory"},
        {"name": "vmix", "type": "directory", "children": [
            {"name": "list1", "type": "directory"}
        ]}
    ]
    
    def create_nodes(items, parent_id=None, sort_order_start=0):
        """Recursively create blueprint nodes"""
        for i, item in enumerate(items):
            node = BlueprintNode(
                template_id=template_id,
                parent_id=parent_id,
                node_type=item["type"],
                name=item["name"],
                content=item.get("content"),
                sort_order=sort_order_start + i,
                is_required=True
            )
            db.add(node)
            db.flush()  # Get the ID for children
            
            # Create children if they exist
            if "children" in item:
                create_nodes(item["children"], node.id, 0)
    
    create_nodes(structure)

def populate_blueprints():
    """Populate blueprint templates with directory structures"""
    db = next(get_db())
    
    try:
        # Get all existing templates
        templates = db.query(BlueprintTemplate).all()
        
        for template in templates:
            print(f"Populating blueprint structure for: {template.name}")
            
            # Check if template already has nodes
            existing_nodes = db.query(BlueprintNode).filter(
                BlueprintNode.template_id == template.id
            ).count()
            
            if existing_nodes > 0:
                print(f"  Skipping {template.name} - already has {existing_nodes} nodes")
                continue
            
            # Create the directory structure
            create_default_blueprint_structure(db, template.id)
            
            print(f"  Created directory structure for {template.name}")
        
        db.commit()
        print("Blueprint population completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error populating blueprints: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    populate_blueprints()