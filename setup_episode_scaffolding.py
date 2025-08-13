#!/usr/bin/env python3
"""
Setup script for episode scaffolding system
Run this to initialize blueprint templates
"""
import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from sqlalchemy import text
from database import engine, get_db

def setup_episode_scaffolding():
    """Setup episode scaffolding system"""
    
    print("Setting up episode scaffolding system...")
    
    # Get database session
    db = next(get_db())
    
    try:
        print("1. Creating blueprint templates...")
        
        # Insert default templates
        db.execute(text("""
            INSERT INTO blueprint_templates (name, description, template_type, is_default, metadata)
            VALUES 
                ('Sunday Show', 'Standard weekly Sunday show format with full rundown structure', 'episode', true, '{"type": "sunday_show", "duration": "01:00:00", "omnystudio_program_id": "6960f124-9e8a-4716-a88c-acfe00399fd7"}'),
                ('Sunday Live', 'Live Sunday show format with streaming optimizations', 'episode', false, '{"type": "sunday_live", "duration": "01:30:00", "streaming": true}'),
                ('Generic Live', 'General purpose live show format', 'episode', false, '{"type": "generic_live", "duration": "01:00:00", "streaming": true}')
            ON CONFLICT (name) DO NOTHING;
        """))
        
        print("2. Creating directory structure templates...")
        
        # Get template IDs
        result = db.execute(text("SELECT id, name FROM blueprint_templates ORDER BY id"))
        templates = result.fetchall()
        
        for template_id, template_name in templates:
            print(f"   Setting up structure for: {template_name}")
            
            # Check if template already has nodes
            node_count = db.execute(text(
                "SELECT COUNT(*) FROM blueprint_nodes WHERE template_id = :template_id"
            ), {"template_id": template_id}).scalar()
            
            if node_count > 0:
                print(f"   Skipping {template_name} - already has {node_count} nodes")
                continue
            
            # Create basic directory structure
            directories = [
                ('assets', None, 0),
                ('audio', 'assets', 0),
                ('graphics', 'assets', 1),
                ('images', 'assets', 2),
                ('guest', 'images', 0),
                ('quotes', 'assets', 3),
                ('unlinked', 'assets', 4),
                ('video', 'assets', 5),
                ('captures', None, 1),
                ('distribute', None, 2),
                ('exports', None, 3),
                ('preshow', None, 4),
                ('rundown', None, 5),
                ('vmix', None, 6),
                ('list1', 'vmix', 0)
            ]
            
            # Create nodes
            node_map = {}
            
            for name, parent_name, sort_order in directories:
                parent_id = node_map.get(parent_name) if parent_name else None
                
                result = db.execute(text("""
                    INSERT INTO blueprint_nodes (template_id, parent_id, node_type, name, sort_order, is_required)
                    VALUES (:template_id, :parent_id, 'directory', :name, :sort_order, true)
                    RETURNING id
                """), {
                    "template_id": template_id,
                    "parent_id": parent_id,
                    "name": name,
                    "sort_order": sort_order
                })
                
                node_id = result.scalar()
                node_map[name] = node_id
            
            # Add preshow notes file
            if 'preshow' in node_map:
                db.execute(text("""
                    INSERT INTO blueprint_nodes (template_id, parent_id, node_type, name, content, sort_order, is_required)
                    VALUES (:template_id, :parent_id, 'file', 'preshow notes.md', :content, 0, true)
                """), {
                    "template_id": template_id,
                    "parent_id": node_map['preshow'],
                    "content": """# Preshow Notes

## Technical Setup
- [ ] Check audio levels
- [ ] Verify video feed
- [ ] Test streaming connection

## Content Preparation
- [ ] Review rundown
- [ ] Prepare graphics
- [ ] Check guest connection

## Final Checklist
- [ ] All systems operational
- [ ] Backup equipment ready
- [ ] Emergency contacts available
"""
                })
        
        db.commit()
        print("✅ Episode scaffolding setup completed successfully!")
        print("\nAvailable templates:")
        
        result = db.execute(text("SELECT name, description FROM blueprint_templates ORDER BY is_default DESC, name"))
        for name, description in result.fetchall():
            print(f"  • {name}: {description}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error setting up episode scaffolding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    setup_episode_scaffolding()