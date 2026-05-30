#!/usr/bin/env python3
"""
Update Episode Blueprint Template to match EPISODE_DIRECTORY_STANDARD.md
This script updates the default episode blueprint template to create the canonical directory structure
"""
import sys
import os
sys.path.insert(0, '/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_episode import BlueprintTemplate, BlueprintNode
from models_user import User
from models_v2 import Organization
from database import get_db

# Get database session
db = next(get_db())

def update_blueprint_structure():
    """Update the default 'Sunday Show' template to match canonical structure"""

    # Get the default template
    template = db.query(BlueprintTemplate).filter(
        BlueprintTemplate.name == "Sunday Show",
        BlueprintTemplate.is_default == True
    ).first()

    if not template:
        print("❌ Default template 'Sunday Show' not found")
        return False

    print(f"✅ Found template: {template.name} (ID: {template.id})")

    # Delete existing nodes for this template
    db.query(BlueprintNode).filter(BlueprintNode.template_id == template.id).delete()
    db.commit()
    print("🗑️  Deleted old blueprint structure")

    # Define canonical structure per EPISODE_DIRECTORY_STANDARD.md
    nodes = []

    # Root level directories (no parent)
    root_dirs = [
        {"name": "projects", "sort_order": 1},
        {"name": "captures", "sort_order": 2},
        {"name": "thumbnails", "sort_order": 3},
        {"name": "assets", "sort_order": 4},
        {"name": "rundown", "sort_order": 5},
        {"name": "scripts", "sort_order": 6},
        {"name": "exports", "sort_order": 7},
    ]

    # Create root directories
    root_nodes = {}
    for dir_info in root_dirs:
        node = BlueprintNode(
            template_id=template.id,
            parent_id=None,
            node_type="directory",
            name=dir_info["name"],
            sort_order=dir_info["sort_order"],
            is_required=True
        )
        db.add(node)
        db.flush()  # Get ID immediately
        root_nodes[dir_info["name"]] = node
        nodes.append(node)

    print(f"✅ Created {len(root_dirs)} root directories")

    # projects/ subdirectories
    projects_subdirs = [
        {"name": "teasers", "sort_order": 1},
        {"name": "graphics", "sort_order": 2},
    ]
    for subdir in projects_subdirs:
        node = BlueprintNode(
            template_id=template.id,
            parent_id=root_nodes["projects"].id,
            node_type="directory",
            name=subdir["name"],
            sort_order=subdir["sort_order"],
            is_required=False
        )
        db.add(node)
        nodes.append(node)

    # assets/ subdirectories (per canonical spec)
    assets_subdirs = [
        {"name": "video", "sort_order": 1},
        {"name": "images", "sort_order": 2},
        {"name": "audio", "sort_order": 3},
        {"name": "graphics", "sort_order": 4},
    ]
    for subdir in assets_subdirs:
        node = BlueprintNode(
            template_id=template.id,
            parent_id=root_nodes["assets"].id,
            node_type="directory",
            name=subdir["name"],
            sort_order=subdir["sort_order"],
            is_required=True
        )
        db.add(node)
        nodes.append(node)

    # rundown/media-list/ subdirectory
    media_list_node = BlueprintNode(
        template_id=template.id,
        parent_id=root_nodes["rundown"].id,
        node_type="directory",
        name="media-list",
        sort_order=1,
        is_required=True
    )
    db.add(media_list_node)
    nodes.append(media_list_node)

    # scripts/ subdirectories
    scripts_subdirs = [
        {"name": "versions", "sort_order": 1},
        {"name": "current", "sort_order": 2},
    ]
    for subdir in scripts_subdirs:
        node = BlueprintNode(
            template_id=template.id,
            parent_id=root_nodes["scripts"].id,
            node_type="directory",
            name=subdir["name"],
            sort_order=subdir["sort_order"],
            is_required=True
        )
        db.add(node)
        nodes.append(node)

    # Commit all nodes
    db.commit()

    print(f"✅ Created {len(nodes)} total blueprint nodes")

    # Verify structure
    verification_query = db.query(BlueprintNode).filter(
        BlueprintNode.template_id == template.id,
        BlueprintNode.parent_id.is_(None)
    ).count()

    print(f"✅ Verification: {verification_query} root directories")

    # Update template metadata to reflect canonical spec
    template.template_metadata = {
        "specification": "EPISODE_DIRECTORY_STANDARD.md v1.0",
        "updated": "2025-10-14",
        "canonical_structure": True,
        "airdate": "",
        "duration": "01:00:00",
        "status": "draft",
        "description": "Standard episode directory structure per canonical specification"
    }
    db.commit()

    print("✅ Updated template metadata")

    return True

if __name__ == "__main__":
    try:
        success = update_blueprint_structure()
        if success:
            print("\n✅ Blueprint update complete - matches EPISODE_DIRECTORY_STANDARD.md")
            sys.exit(0)
        else:
            print("\n❌ Blueprint update failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
