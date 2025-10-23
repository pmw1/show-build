#!/usr/bin/env python3
"""
Update Episode Blueprint to Match EPISODE_DIRECTORY_STANDARD.md

This script updates the database blueprint template to create the canonical
episode directory structure as defined in docs/EPISODE_DIRECTORY_STANDARD.md

Usage:
    python update_episode_blueprint_canonical.py
"""

import sys
from pathlib import Path
from sqlalchemy.orm import Session
from database import SessionLocal

# Import all model files to ensure SQLAlchemy can resolve all relationships
from models_episode import BlueprintTemplate, BlueprintNode
import models_user
import models_v2
import models_rbac
import models_assetid
import models_speakers

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# Canonical episode directory structure from EPISODE_DIRECTORY_STANDARD.md
CANONICAL_STRUCTURE = {
    "name": "Canonical Episode Structure",
    "description": "Standard episode directory structure per EPISODE_DIRECTORY_STANDARD.md v1.0",
    "directories": [
        # Root level files are created separately (info.md, {EPISODE}-rundown.json)

        # projects/ - Production software project files
        {
            "name": "projects",
            "description": "Production software project files (vMix, After Effects)",
            "children": [
                {
                    "name": "teasers",
                    "description": "Guest teaser After Effects projects",
                    "children": []
                },
                {
                    "name": "graphics",
                    "description": "Other After Effects graphics projects",
                    "children": []
                }
            ]
        },

        # captures/ - Raw vMix recordings
        {
            "name": "captures",
            "description": "Raw vMix recordings (BLOCK-A.mov, BREAK-1.mov, etc.)",
            "children": []
        },

        # thumbnails/ - Master artwork sources
        {
            "name": "thumbnails",
            "description": "Master artwork sources (PSD/PNG for 16x9 and square)",
            "children": []
        },

        # assets/ - Final production assets
        {
            "name": "assets",
            "description": "Final production assets organized by type",
            "children": [
                {
                    "name": "video",
                    "description": "Video clips with AssetID naming",
                    "children": []
                },
                {
                    "name": "images",
                    "description": "Image files with AssetID naming",
                    "children": []
                },
                {
                    "name": "audio",
                    "description": "Audio files with AssetID naming",
                    "children": []
                },
                {
                    "name": "graphics",
                    "description": "Graphic assets with AssetID naming",
                    "children": []
                }
            ]
        },

        # rundown/ - Rundown organization
        {
            "name": "rundown",
            "description": "Rundown organization (reserved for future filesystem sync)",
            "children": [
                {
                    "name": "media-list",
                    "description": "vMix playlist (symlinks to assets with enumeration)",
                    "children": []
                }
            ]
        },

        # scripts/ - Generated script versions
        {
            "name": "scripts",
            "description": "Generated script versions with timestamped snapshots",
            "children": [
                {
                    "name": "versions",
                    "description": "Timestamped script versions (YYYYMMDD_HHMMSS/)",
                    "children": []
                },
                {
                    "name": "current",
                    "description": "Symlinks to latest script version",
                    "children": []
                }
            ]
        },

        # exports/ - Distribution-ready content
        {
            "name": "exports",
            "description": "Distribution-ready content (blocks, full episode, audio, thumbnails)",
            "children": []
        }
    ]
}


def delete_existing_template(db: Session) -> None:
    """Delete existing episode blueprint templates"""
    logger.info("Checking for existing episode templates...")

    templates = db.query(BlueprintTemplate).filter(
        BlueprintTemplate.template_type == "episode"
    ).all()

    if templates:
        logger.info(f"Found {len(templates)} existing episode template(s)")
        for template in templates:
            logger.info(f"  Deleting template: {template.name} (id: {template.id})")

            # Delete associated nodes first
            node_count = db.query(BlueprintNode).filter(
                BlueprintNode.template_id == template.id
            ).delete()
            logger.info(f"    Deleted {node_count} blueprint nodes")

            # Delete template
            db.delete(template)

        db.commit()
        logger.info("✓ Existing templates deleted")
    else:
        logger.info("No existing episode templates found")


def create_canonical_template(db: Session) -> BlueprintTemplate:
    """Create canonical episode blueprint template"""
    logger.info("Creating canonical episode template...")

    # Create template
    template = BlueprintTemplate(
        name="Canonical Episode Structure",
        description="Standard episode directory structure per EPISODE_DIRECTORY_STANDARD.md v1.0 (2025-10-13)",
        template_type="episode",
        is_active=True,
        is_default=True,
        template_metadata={
            "source": "EPISODE_DIRECTORY_STANDARD.md",
            "version": "1.0",
            "date": "2025-10-13",
            "authority": "Authoritative - Single Source of Truth"
        }
    )

    db.add(template)
    db.flush()  # Get template ID

    logger.info(f"✓ Created template (id: {template.id})")

    return template


def create_directory_node(db: Session, template_id: int, dir_info: dict,
                         parent_id: int = None, sort_order: int = 0) -> BlueprintNode:
    """Recursively create directory nodes"""

    # Create directory node
    node = BlueprintNode(
        template_id=template_id,
        parent_id=parent_id,
        name=dir_info["name"],
        node_type="directory",
        sort_order=sort_order,
        is_required=True,
        content=None  # Description stored at template level, not node level
    )

    db.add(node)
    db.flush()  # Get node ID for children

    # Create children
    if "children" in dir_info and dir_info["children"]:
        for idx, child in enumerate(dir_info["children"]):
            create_directory_node(db, template_id, child, parent_id=node.id, sort_order=idx)

    return node


def build_canonical_structure(db: Session, template: BlueprintTemplate) -> None:
    """Build canonical directory structure in database"""
    logger.info("Building canonical directory structure...")

    structure = CANONICAL_STRUCTURE["directories"]

    for idx, dir_info in enumerate(structure):
        logger.info(f"  Creating: {dir_info['name']}/")
        create_directory_node(db, template.id, dir_info, parent_id=None, sort_order=idx)

    logger.info("✓ Directory structure created")


def verify_structure(db: Session, template_id: int) -> None:
    """Verify created structure"""
    logger.info("\nVerifying created structure...")

    # Count nodes
    total_nodes = db.query(BlueprintNode).filter(
        BlueprintNode.template_id == template_id
    ).count()

    root_nodes = db.query(BlueprintNode).filter(
        BlueprintNode.template_id == template_id,
        BlueprintNode.parent_id.is_(None)
    ).count()

    logger.info(f"  Total nodes: {total_nodes}")
    logger.info(f"  Root directories: {root_nodes}")

    # List root directories
    roots = db.query(BlueprintNode).filter(
        BlueprintNode.template_id == template_id,
        BlueprintNode.parent_id.is_(None)
    ).order_by(BlueprintNode.sort_order).all()

    logger.info("\n  Root structure:")
    for root in roots:
        # Count children
        children_count = db.query(BlueprintNode).filter(
            BlueprintNode.parent_id == root.id
        ).count()

        child_suffix = f" ({children_count} children)" if children_count > 0 else ""
        logger.info(f"    /{root.name}/{child_suffix}")

    logger.info("\n✓ Structure verified")


def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("UPDATING EPISODE BLUEPRINT TO CANONICAL STRUCTURE")
    logger.info("="*80)
    logger.info(f"Source: docs/EPISODE_DIRECTORY_STANDARD.md")
    logger.info("")

    db = SessionLocal()

    try:
        # Step 1: Delete existing templates
        delete_existing_template(db)

        # Step 2: Create canonical template
        template = create_canonical_template(db)

        # Step 3: Build directory structure
        build_canonical_structure(db, template)

        # Step 4: Verify
        verify_structure(db, template.id)

        # Commit all changes
        db.commit()

        logger.info("\n" + "="*80)
        logger.info("✓ BLUEPRINT UPDATE COMPLETE")
        logger.info("="*80)
        logger.info(f"\nTemplate ID: {template.id}")
        logger.info(f"Template Name: {template.name}")
        logger.info(f"Status: Active, Default")
        logger.info("\nNew episodes will now be created with the canonical structure.")

        return 0

    except Exception as e:
        db.rollback()
        logger.error(f"\n❌ ERROR: {e}")
        logger.error("\nRolling back changes...")
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
