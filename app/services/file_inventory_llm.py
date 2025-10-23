"""
File Inventory LLM Service
Semantic file matching using LLM-based analysis with Prompt Override System integration.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Default prompts (can be overridden via Prompt Override System)
DEFAULT_PROMPTS = {
    "inventory-match-file-to-expectation": {
        "category": "inventory",
        "system_prompt": """You are analyzing episode files to determine if they match semantic expectations from the canonical file standard.

Your task is to carefully evaluate whether a file serves the expected purpose based on its characteristics, not just its filename.

Respond with valid JSON only, no additional text.""",
        "user_prompt_template": """EXPECTATION:
- Category: {{category}}
- Purpose: {{purpose}}
- Characteristics: {{characteristics}}
- Location Hints: {{location_hints}}

FILE FOUND:
- Path: {{file_path}}
- Filename: {{filename}}
- Extension: {{extension}}
- Size: {{size}} bytes
- Dimensions: {{dimensions}}
- Location: {{folder_path}}

Does this file match the expectation? Consider:
1. Does the purpose align?
2. Do the technical characteristics match?
3. Is it in a plausible location?
4. Does the filename suggest this purpose?

Respond with JSON:
{
  "matches": true/false,
  "confidence": 0-100,
  "reasoning": "Brief explanation",
  "alternative_expectation": "If this doesn't match, what might it be?"
}"""
    },

    "inventory-classify-stray-file": {
        "category": "inventory",
        "system_prompt": """You are analyzing an unclassified file in an episode directory to determine its purpose and appropriate handling.

Classify files into predefined stray categories based on common patterns and file characteristics.

Respond with valid JSON only, no additional text.""",
        "user_prompt_template": """FILE FOUND:
- Path: {{file_path}}
- Filename: {{filename}}
- Extension: {{extension}}
- Size: {{size}} bytes
- Location: {{folder_path}}
- Modified Date: {{modified}}

This file does not match any canonical expectation. Classify it as one of:
1. stray.system - OS/system file (safe to ignore)
2. stray.backup - Backup/old version (review before delete)
3. stray.sync_conflict - Sync conflict (needs resolution)
4. stray.archive - Compressed archive (review contents)
5. stray.sync_metadata - Sync service metadata (ignore)
6. stray.temp_directory - Temporary folder (review/delete)
7. stray.unnamed - Unnamed folder (review contents)
8. stray.editor_workspace - Editor metadata (ignore)
9. stray.partial - Incomplete download (delete)
10. stray.log - Log file (review/delete)
11. stray.draft - Draft/work-in-progress (relocate or delete)
12. stray.misplaced_capture - Capture in wrong folder (relocate)
13. stray.misplaced_export - Export in wrong folder (relocate)
14. stray.misplaced_project - Project file in wrong folder (relocate)
15. stray.user_notes - User working files (review)
16. stray.source_media - Production source misplaced (relocate)
17. stray.duplicate - Duplicate of canonical file (delete)
18. stray.unknown - Cannot determine purpose (manual review)

Respond with JSON:
{
  "category": "stray.{subcategory}",
  "confidence": 0-100,
  "reasoning": "Why you classified it this way",
  "suggested_action": "ignore|delete|relocate|review",
  "relocation_target": "folder_path (if action is relocate)",
  "safety": "safe|caution|dangerous"
}"""
    },

    "inventory-identify-duplicate": {
        "category": "inventory",
        "system_prompt": """You are analyzing two files to determine if they are duplicates or serve the same purpose.

Consider file purpose, naming patterns, size similarity, and location when determining if files are duplicates.

Respond with valid JSON only, no additional text.""",
        "user_prompt_template": """FILE 1:
- Path: {{file1_path}}
- Filename: {{file1_name}}
- Extension: {{file1_ext}}
- Size: {{file1_size}} bytes
- Location: {{file1_folder}}

FILE 2:
- Path: {{file2_path}}
- Filename: {{file2_name}}
- Extension: {{file2_ext}}
- Size: {{file2_size}} bytes
- Location: {{file2_folder}}

Are these files duplicates or do they serve the same purpose?

Consider:
1. Are the filenames similar (e.g., "file.mov" vs "file copy.mov")?
2. Are the file sizes very similar (within 1%)?
3. Do they have the same extension?
4. Are they in different locations but serve the same purpose?
5. Is one clearly a backup/copy of the other?

Respond with JSON:
{
  "are_duplicates": true/false,
  "confidence": 0-100,
  "reasoning": "Why you think they are/aren't duplicates",
  "recommended_action": "keep_both|keep_file1|keep_file2|review",
  "duplicate_type": "exact_copy|backup|version|different_files"
}"""
    },

    "inventory-validate-file-purpose": {
        "category": "inventory",
        "system_prompt": """You are validating whether a file actually serves its expected purpose based on technical characteristics.

This is used to verify that files matched to expectations are actually valid for that purpose.

Respond with valid JSON only, no additional text.""",
        "user_prompt_template": """FILE:
- Path: {{file_path}}
- Filename: {{filename}}
- Extension: {{extension}}
- Size: {{size}} bytes
- Dimensions: {{dimensions}}
- Duration: {{duration}}

EXPECTED PURPOSE: {{expected_purpose}}

EXPECTED CHARACTERISTICS:
{{expected_characteristics}}

Does this file meet the expected characteristics for its purpose?

Validation checks:
1. Is the file format appropriate?
2. Is the file size reasonable for this purpose?
3. Are dimensions/resolution appropriate (if applicable)?
4. Is duration reasonable (if applicable)?
5. Does the filename indicate proper purpose?

Respond with JSON:
{
  "valid": true/false,
  "confidence": 0-100,
  "reasoning": "Why this file does/doesn't meet expectations",
  "issues": ["list", "of", "validation", "issues"],
  "suggestions": "How to fix issues if invalid"
}"""
    }
}


def get_inventory_prompt(
    operation_key: str,
    variables: Dict[str, Any],
    db_session = None
) -> Dict[str, Any]:
    """
    Get LLM prompt for inventory operations with Prompt Override System integration.

    Args:
        operation_key: Operation identifier (e.g., 'inventory-match-file-to-expectation')
        variables: Template variables for substitution
        db_session: Database session for checking overrides (optional)

    Returns:
        Dictionary with 'system_prompt', 'user_prompt', and 'overridden' flag
    """
    # Get default prompt
    if operation_key not in DEFAULT_PROMPTS:
        raise ValueError(f"Unknown inventory operation: {operation_key}")

    default = DEFAULT_PROMPTS[operation_key]
    system_prompt = default["system_prompt"]
    user_template = default["user_prompt_template"]
    overridden = False

    # Check for database override if session provided
    if db_session:
        try:
            from models_v2 import PromptOverride
            override = db_session.query(PromptOverride).filter(
                PromptOverride.operation_key == operation_key,
                PromptOverride.is_enabled == True
            ).first()

            if override:
                if override.system_prompt:
                    system_prompt = override.system_prompt
                if override.user_prompt_template:
                    user_template = override.user_prompt_template
                overridden = True
                logger.info(f"Using prompt override for {operation_key}")
        except Exception as e:
            logger.warning(f"Error checking prompt overrides: {e}")

    # Substitute variables in user prompt
    user_prompt = user_template
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        user_prompt = user_prompt.replace(placeholder, str(value))

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "overridden": overridden,
        "operation_key": operation_key,
        "category": default["category"]
    }


async def match_file_to_expectation(
    file_info: Dict[str, Any],
    expectation: Dict[str, Any],
    llm_service,
    db_session = None
) -> Dict[str, Any]:
    """
    Use LLM to determine if a file matches a canonical expectation.

    Args:
        file_info: File metadata (path, size, extension, etc.)
        expectation: Canonical expectation definition
        llm_service: LLM service instance for making requests
        db_session: Database session for prompt overrides

    Returns:
        Match result with confidence score
    """
    variables = {
        "category": expectation.get("category", ""),
        "purpose": expectation.get("purpose", ""),
        "characteristics": expectation.get("characteristics", ""),
        "location_hints": expectation.get("location_hints", ""),
        "file_path": file_info.get("path", ""),
        "filename": file_info.get("filename", ""),
        "extension": file_info.get("extension", ""),
        "size": file_info.get("size", 0),
        "dimensions": file_info.get("dimensions", "N/A"),
        "folder_path": file_info.get("folder_path", "")
    }

    prompt = get_inventory_prompt(
        "inventory-match-file-to-expectation",
        variables,
        db_session
    )

    try:
        # Call LLM service
        response = await llm_service.generate(
            system_prompt=prompt["system_prompt"],
            user_prompt=prompt["user_prompt"],
            temperature=0.3,  # Low temperature for consistent matching
            response_format="json"
        )

        # Parse JSON response
        result = json.loads(response)
        result["overridden"] = prompt["overridden"]
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        return {
            "matches": False,
            "confidence": 0,
            "reasoning": "LLM response was not valid JSON",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Error matching file to expectation: {e}")
        return {
            "matches": False,
            "confidence": 0,
            "reasoning": "Error during LLM processing",
            "error": str(e)
        }


async def classify_stray_file(
    file_info: Dict[str, Any],
    llm_service,
    db_session = None
) -> Dict[str, Any]:
    """
    Use LLM to classify an unrecognized file.

    Args:
        file_info: File metadata
        llm_service: LLM service instance
        db_session: Database session for prompt overrides

    Returns:
        Classification result with suggested action
    """
    variables = {
        "file_path": file_info.get("path", ""),
        "filename": file_info.get("filename", ""),
        "extension": file_info.get("extension", ""),
        "size": file_info.get("size", 0),
        "folder_path": file_info.get("folder_path", ""),
        "modified": file_info.get("modified", "Unknown")
    }

    prompt = get_inventory_prompt(
        "inventory-classify-stray-file",
        variables,
        db_session
    )

    try:
        response = await llm_service.generate(
            system_prompt=prompt["system_prompt"],
            user_prompt=prompt["user_prompt"],
            temperature=0.2,
            response_format="json"
        )

        result = json.loads(response)
        result["overridden"] = prompt["overridden"]
        return result

    except Exception as e:
        logger.error(f"Error classifying stray file: {e}")
        return {
            "category": "stray.unknown",
            "confidence": 0,
            "reasoning": f"Error during classification: {str(e)}",
            "suggested_action": "review",
            "safety": "caution",
            "error": str(e)
        }


def register_default_prompts(db_session) -> None:
    """
    Register default inventory prompts in the database if they don't exist.
    This allows them to appear in the Prompt Manager UI for customization.

    Args:
        db_session: Database session
    """
    try:
        from models_v2 import PromptOverride

        for operation_key, prompt_data in DEFAULT_PROMPTS.items():
            # Check if already exists
            existing = db_session.query(PromptOverride).filter(
                PromptOverride.operation_key == operation_key
            ).first()

            if not existing:
                # Create default entry (disabled by default)
                override = PromptOverride(
                    category=prompt_data["category"],
                    operation_key=operation_key,
                    system_prompt=prompt_data["system_prompt"],
                    user_prompt_template=prompt_data["user_prompt_template"],
                    is_enabled=False,  # Default prompts, not overrides
                    notes=f"Default prompt for {operation_key}. Enable and edit to customize.",
                    created_by="system"
                )
                db_session.add(override)

        db_session.commit()
        logger.info("Registered inventory default prompts in database")

    except Exception as e:
        logger.error(f"Error registering default prompts: {e}")
        db_session.rollback()
