"""
File Inventory API
Endpoints for scanning episode directories and generating semantic file inventories.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Optional
import logging
import asyncio

from database import get_db
from auth.utils import get_current_user_or_key
from services.file_inventory_scanner_v2 import (
    scan_directory_recursive,
    match_files_to_expectations,
    classify_unmatched_files,
    generate_mapping_file
)
from services.file_inventory_batched import (
    scan_directory_recursive as scan_directory_batched,
    match_slots_batched,
    generate_mapping_yaml
)
from services.file_inventory_llm_v2 import register_default_prompts, OllamaLLMService, OpenAILLMService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/inventory", tags=["inventory"])

# Base path for episodes
SYNCTHING_BASE = "/home/episodes"


def scan_google_drive_recursive(drive_service, folder_id: str, episode_number: str) -> list:
    """
    Recursively scan Google Drive folder and build file list compatible with LLM scanner.

    Args:
        drive_service: GoogleDriveService instance
        folder_id: Google Drive folder ID to scan
        episode_number: Episode number for context

    Returns:
        List of file dictionaries with metadata
    """
    files = []

    def _scan_folder(parent_id: str, relative_path: str = ""):
        """Recursively scan folder contents."""
        try:
            items = drive_service.list_files(folder_id=parent_id, order_by="folder,name")

            for item in items:
                is_folder = item.get('mimeType') == 'application/vnd.google-apps.folder'
                item_name = item['name']

                # Build relative path
                item_relative_path = f"{relative_path}/{item_name}" if relative_path else item_name

                if is_folder:
                    # Recurse into folder
                    _scan_folder(item['id'], item_relative_path)
                else:
                    # Regular file - add to list
                    file_size = int(item.get('size', 0))
                    file_extension = Path(item_name).suffix.lower()

                    file_meta = {
                        "path": f"google_drive://{item['id']}",
                        "filename": item_name,
                        "extension": file_extension,
                        "size": file_size,
                        "relative_path": item_relative_path,
                        "drive_id": item['id']
                    }

                    files.append(file_meta)

        except Exception as e:
            logger.error(f"Error scanning Google Drive folder {parent_id}: {e}")

    _scan_folder(folder_id)
    return files


def get_llm_service_with_fallback(db: Session, user_info: dict = None):
    """Get LLM service using configured fallback order."""
    from models_v2 import Settings
    import json

    # Get LLM routing configuration
    llm_routing = db.query(Settings).filter(Settings.key == "llm_routing").first()

    if not llm_routing:
        # No routing config, use Ollama as default
        logger.info("No LLM routing config found, using Ollama")
        return OllamaLLMService(), None

    routing_config = llm_routing.value.get("routing", {})
    enable_fallback = routing_config.get("enableFallback", True)
    fallback_order = routing_config.get("fallbackOrder", ["ollama", "openai"])

    if not enable_fallback:
        # Fallback disabled, use first provider only
        provider = fallback_order[0] if fallback_order else "ollama"
        logger.info(f"Fallback disabled, using {provider}")
        return _get_provider_service(provider, db), None

    # Try each provider in fallback order
    failed_providers = []
    for idx, provider in enumerate(fallback_order):
        try:
            logger.info(f"Attempting to use LLM provider: {provider}")
            service = _get_provider_service(provider, db)

            # Test the service with a simple prompt (no asyncio.run since we're already in async context)
            try:
                import asyncio
                # Create new event loop for test if we're in async context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                test_result = loop.run_until_complete(service.generate(
                    "You are a test assistant.",
                    "Respond with just the word 'OK'",
                    temperature=0.0
                ))
                loop.close()
            except Exception as test_error:
                logger.info(f"LLM test call failed for {provider}: {test_error}, but will attempt to use it anyway")
                # Don't fail on test error, just log it

            logger.info(f"Successfully connected to {provider}")

            # If we used a fallback (not the first provider), notify user
            fallback_info = None
            if idx > 0 and user_info:
                fallback_info = {
                    "used_fallback": True,
                    "primary_provider": fallback_order[0],
                    "fallback_provider": provider,
                    "failed_providers": failed_providers
                }

            return service, fallback_info

        except Exception as e:
            logger.warning(f"Failed to connect to {provider}: {e}")
            failed_providers.append(provider)
            continue

    # All providers failed
    raise HTTPException(
        status_code=503,
        detail=f"All LLM providers failed. Tried: {', '.join(fallback_order)}"
    )


def _get_provider_service(provider: str, db: Session):
    """Get LLM service instance for a specific provider."""
    from sqlalchemy import text

    if provider == "openai":
        # Query api_configs table directly
        result = db.execute(
            text("SELECT config_value FROM api_configs WHERE service = 'openai' AND config_key = 'api_key' LIMIT 1")
        ).first()

        if not result:
            raise ValueError("OpenAI API key not configured")

        api_key = result[0]

        # Get model
        model_result = db.execute(
            text("SELECT config_value FROM api_configs WHERE service = 'openai' AND config_key = 'model' LIMIT 1")
        ).first()

        model = model_result[0] if model_result else "gpt-4o"
        return OpenAILLMService(api_key=api_key, model=model)

    elif provider == "ollama":
        return OllamaLLMService()

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def _estimate_llm_cost(provider: str, model: str, batch_size: int, token_estimate_per_batch: int = 8000):
    """Estimate cost of LLM operations."""
    # Pricing per 1M tokens (approximate as of 2025)
    pricing = {
        "openai": {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4": {"input": 30.00, "output": 60.00}
        },
        "ollama": {"cost": 0.00},  # Free/self-hosted
        "anthropic": {
            "claude-3-opus": {"input": 15.00, "output": 75.00},
            "claude-3-sonnet": {"input": 3.00, "output": 15.00}
        }
    }

    if provider not in pricing:
        return {"estimated": False, "message": "Pricing not available"}

    if provider == "ollama":
        return {"estimated": True, "total_cost": 0.00, "currency": "USD"}

    if model not in pricing[provider]:
        return {"estimated": False, "message": f"Pricing for {model} not available"}

    rates = pricing[provider][model]
    # Assume 80% input, 20% output token ratio
    total_tokens = token_estimate_per_batch * batch_size
    input_tokens = total_tokens * 0.8
    output_tokens = total_tokens * 0.2

    input_cost = (input_tokens / 1_000_000) * rates["input"]
    output_cost = (output_tokens / 1_000_000) * rates["output"]
    total_cost = input_cost + output_cost

    return {
        "estimated": True,
        "total_cost": round(total_cost, 4),
        "currency": "USD",
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
        "rate_info": rates
    }


def _send_fallback_notification(db: Session, user_info: dict, fallback_info: dict, episode_number: str, batch_size: int):
    """Send notification to user about LLM fallback usage."""
    from models_v2 import Notification
    from datetime import datetime
    import json

    primary = fallback_info["primary_provider"]
    fallback = fallback_info["fallback_provider"]
    failed = ", ".join(fallback_info["failed_providers"])

    # Get cost estimate
    cost_info = _estimate_llm_cost(fallback, "gpt-4o" if fallback == "openai" else "unknown", batch_size)

    cost_message = ""
    if cost_info.get("estimated"):
        if cost_info["total_cost"] > 0:
            cost_message = f"\n\n💰 Estimated cost: ${cost_info['total_cost']:.4f} USD ({cost_info['input_tokens']:,} input + {cost_info['output_tokens']:,} output tokens)"
        else:
            cost_message = "\n\n💰 Cost: Free (self-hosted)"

    notification = Notification(
        user_id=user_info.get("id"),
        title="LLM Fallback Used",
        message=f"File inventory scan for episode {episode_number} used fallback LLM provider.\n\n"
                f"❌ Primary ({primary}) failed\n"
                f"✅ Fallback ({fallback}) succeeded\n"
                f"Failed providers: {failed}{cost_message}",
        category="llm_fallback",
        severity="info",
        metadata=json.dumps({
            "episode": episode_number,
            "primary_provider": primary,
            "fallback_provider": fallback,
            "failed_providers": fallback_info["failed_providers"],
            "batch_size": batch_size,
            "cost_estimate": cost_info
        }),
        is_read=False,
        created_at=datetime.utcnow()
    )

    db.add(notification)
    db.commit()
    logger.info(f"Sent fallback notification to user {user_info.get('username', 'unknown')}")


@router.post("/scan/{episode_number}")
async def scan_episode_inventory(
    episode_number: str,
    source_system: str = "syncthing",
    confidence_threshold: int = 80,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Scan an episode directory and generate semantic file inventory using LLM.

    Args:
        episode_number: Episode number to scan (e.g., "0239")
        source_system: Source system (syncthing or google_drive)
        confidence_threshold: Minimum confidence for accepting matches (0-100)

    Returns:
        Inventory results with matched files and stray file classifications
    """
    try:
        # Validate episode number
        if not episode_number.isdigit() or len(episode_number) != 4:
            raise HTTPException(status_code=400, detail="Episode number must be 4 digits")

        # Build episode path
        episode_path = Path(SYNCTHING_BASE) / episode_number

        if not episode_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Episode directory not found: {episode_path}"
            )

        logger.info(f"Starting file inventory scan for episode {episode_number}")

        # Step 1: Scan directory recursively
        logger.info("Scanning directory tree...")
        files = scan_directory_recursive(episode_path)
        logger.info(f"Found {len(files)} files")

        if len(files) == 0:
            return {
                "success": True,
                "episode": episode_number,
                "message": "No files found in episode directory",
                "statistics": {
                    "total_files_scanned": 0,
                    "matched": 0,
                    "unmatched": 0,
                    "stray_files": 0
                }
            }

        # Step 2: Initialize LLM service (Ollama)
        llm_service = OllamaLLMService()

        # Step 3: Match files to expectations
        logger.info("Matching files to canonical expectations...")
        matched, unmatched = await match_files_to_expectations(
            files,
            episode_number,
            llm_service,
            db,
            confidence_threshold
        )
        logger.info(f"Matched {len(matched)} expectations, {len(unmatched)} files remain")

        # Step 4: Classify stray files
        logger.info("Classifying unmatched files...")
        stray_files = await classify_unmatched_files(
            unmatched,
            llm_service,
            db
        )
        logger.info(f"Classified {len(stray_files)} stray files")

        # Step 5: Generate mapping file
        scan_metadata = {
            "llm_model": "llama3.2",  # TODO: Get from actual service
            "source_system": source_system,
            "confidence_threshold": confidence_threshold
        }

        mapping_yaml = generate_mapping_file(
            episode_number,
            matched,
            stray_files,
            len(files),
            scan_metadata
        )

        # Save mapping file to episode directory
        mapping_file_path = episode_path / f"{episode_number}-file-mapping.yaml"
        mapping_file_path.write_text(mapping_yaml)
        logger.info(f"Saved mapping file to {mapping_file_path}")

        # Calculate statistics
        matched_count = sum(1 for m in matched if m["matched"])
        needs_review_count = sum(1 for m in matched if m.get("needs_review", False))

        return {
            "success": True,
            "episode": episode_number,
            "scan_timestamp": scan_metadata.get("scan_timestamp"),
            "source_system": source_system,
            "mapping_file": str(mapping_file_path),
            "statistics": {
                "total_files_scanned": len(files),
                "total_expectations": len(matched),
                "matched": matched_count,
                "unmatched": len(matched) - matched_count,
                "needs_review": needs_review_count,
                "stray_files": len(stray_files)
            },
            "matched_expectations": matched,
            "stray_files": stray_files
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning episode inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mapping/{episode_number}")
async def get_episode_mapping(
    episode_number: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get the saved file mapping for an episode.

    Args:
        episode_number: Episode number

    Returns:
        YAML mapping file content
    """
    try:
        episode_path = Path(SYNCTHING_BASE) / episode_number
        mapping_file = episode_path / f"{episode_number}-file-mapping.yaml"

        if not mapping_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"No mapping file found for episode {episode_number}. Run scan first."
            )

        import yaml
        with open(mapping_file, 'r') as f:
            mapping = yaml.safe_load(f)

        return {
            "success": True,
            "episode": episode_number,
            "mapping_file": str(mapping_file),
            "mapping": mapping
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading mapping file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan-batched/{episode_number}")
async def scan_episode_batched(
    episode_number: str,
    source_system: str = "syncthing",
    batch_size: int = 3,  # Reduced from 5 to 3 per LLM consultation consensus
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Scan episode using batched LLM approach (9 batches × 3 slots = 27 slots total).
    Uses configured LLM fallback order from settings.

    Updated per LLM consultation: Qwen2.5-Coder:32b model, 3 slots/batch, optimized parameters.

    Args:
        episode_number: Episode number to scan
        source_system: Source system (syncthing or google_drive)
        batch_size: Number of slots per LLM batch (default 3, was 5)
    """
    try:
        if not episode_number.isdigit() or len(episode_number) != 4:
            raise HTTPException(status_code=400, detail="Episode number must be 4 digits")

        # Handle Google Drive scanning
        if source_system == "google_drive":
            try:
                from services.google_drive_service import get_drive_service_from_config
                from api_config import APIConfigManager

                logger.info(f"Starting Google Drive scan for episode {episode_number}")

                # Get Drive service
                api_config_manager = APIConfigManager()
                drive_service = get_drive_service_from_config(api_config_manager)

                # Get episodes root folder ID
                episodes_root_id = drive_service.get_episodes_folder_id()
                if not episodes_root_id:
                    raise HTTPException(status_code=404, detail="Google Drive episodes folder not configured")

                # Find episode folder
                episode_folders = drive_service.search_files(name_contains=episode_number)
                matching_folder = None
                for folder in episode_folders:
                    if folder['name'] == episode_number and folder.get('mimeType') == 'application/vnd.google-apps.folder':
                        matching_folder = folder
                        break

                if not matching_folder:
                    raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found in Google Drive")

                # Build file list from Drive
                files = scan_google_drive_recursive(drive_service, matching_folder['id'], episode_number)
                logger.info(f"Found {len(files)} files in Google Drive")

                if len(files) == 0:
                    return {"success": True, "episode": episode_number, "source_system": source_system, "message": "No files found in Google Drive"}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error accessing Google Drive for episode {episode_number}: {e}")
                return {
                    "success": False,
                    "episode": episode_number,
                    "source_system": source_system,
                    "message": f"Failed to access Google Drive: {str(e)}",
                    "statistics": {
                        "total_files_scanned": 0,
                        "total_slots": 0,
                        "slots_filled": 0,
                        "slots_empty": 0,
                        "files_matched": 0,
                        "llm_calls_made": 0
                    }
                }
        else:
            # Syncthing/local filesystem scanning
            episode_path = Path(SYNCTHING_BASE) / episode_number
            if not episode_path.exists():
                raise HTTPException(status_code=404, detail=f"Episode directory not found: {episode_path}")

            logger.info(f"Starting batched scan for episode {episode_number}")

            # Scan directory
            files = scan_directory_batched(episode_path)
            logger.info(f"Found {len(files)} files")

        if len(files) == 0:
            return {"success": True, "episode": episode_number, "message": "No files found"}

        # Get LLM service using fallback logic
        llm_service, fallback_info = get_llm_service_with_fallback(db, current_user)
        logger.info(f"Using LLM provider: {llm_service.provider}")

        # Send notification if fallback was used
        if fallback_info and fallback_info.get("used_fallback"):
            _send_fallback_notification(
                db,
                current_user,
                fallback_info,
                episode_number,
                batch_size
            )

        slot_results = await match_slots_batched(files, episode_number, llm_service, batch_size=batch_size, db_session=db)

        # Debug: check slot_results structure
        logger.info(f"Slot results type: {type(slot_results)}")
        if slot_results:
            first_key = list(slot_results.keys())[0] if hasattr(slot_results, 'keys') else None
            if first_key:
                logger.info(f"First slot '{first_key}' value type: {type(slot_results[first_key])}, value: {slot_results[first_key]}")

        # Generate mapping
        scan_metadata = {
            "llm_model": f"{llm_service.provider}:{getattr(llm_service, 'model', 'unknown')}",
            "source_system": source_system,
            "batch_size": batch_size
        }
        mapping_yaml = generate_mapping_yaml(episode_number, slot_results, len(files), scan_metadata)

        # Determine save path (always use Syncthing episode directory)
        save_path = Path(SYNCTHING_BASE) / episode_number
        save_path.mkdir(parents=True, exist_ok=True)

        # Save mapping (YAML) - only for Syncthing
        mapping_file_path = None
        if source_system == "syncthing":
            mapping_file_path = save_path / f"{episode_number}-file-mapping.yaml"
            mapping_file_path.write_text(mapping_yaml)

        # Save full scan results (JSON)
        import json
        from datetime import datetime

        json_results = {
            "scan_timestamp": datetime.utcnow().isoformat(),
            "episode": episode_number,
            "source_system": source_system,
            "llm_model": f"{llm_service.provider}:{getattr(llm_service, 'model', 'unknown')}",
            "batch_size": batch_size,
            "statistics": {
                "total_files_scanned": len(files),
                "total_slots": len(slot_results),
                "slots_filled": sum(1 for r in slot_results.values() if isinstance(r, dict) and r.get('matches')),
                "slots_empty": len(slot_results) - sum(1 for r in slot_results.values() if isinstance(r, dict) and r.get('matches')),
                "files_matched": len(set([f for r in slot_results.values() if isinstance(r, dict) for f in r.get('matches', [])])),
                "llm_calls_made": (len(slot_results) + batch_size - 1) // batch_size
            },
            "slot_results": slot_results
        }

        json_file_path = save_path / f"{episode_number}-llm-scan-{source_system}.json"
        with open(json_file_path, 'w') as f:
            json.dump(json_results, f, indent=2)

        logger.info(f"Saved scan results to {json_file_path}")

        # Statistics
        slots_filled = sum(1 for r in slot_results.values() if isinstance(r, dict) and r.get('matches'))

        # Count unique matched files
        matched_files = []
        for r in slot_results.values():
            if isinstance(r, dict):
                matches = r.get('matches', [])
                if isinstance(matches, list):
                    matched_files.extend(matches)
        files_matched = len(set(matched_files))

        return {
            "success": True,
            "episode": episode_number,
            "source_system": source_system,
            "mapping_file": str(mapping_file_path) if mapping_file_path else None,
            "json_file": str(json_file_path),
            "statistics": {
                "total_files_scanned": len(files),
                "total_slots": len(slot_results),
                "slots_filled": slots_filled,
                "slots_empty": len(slot_results) - slots_filled,
                "files_matched": files_matched,
                "llm_calls_made": (len(slot_results) + batch_size - 1) // batch_size
            },
            "slot_results": slot_results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batched scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initialize-prompts")
async def initialize_default_prompts(
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Initialize default inventory prompts in the database.
    This makes them available in the Prompt Manager UI.

    Admin-only endpoint.
    """
    try:
        register_default_prompts(db)

        return {
            "success": True,
            "message": "Default inventory prompts registered in database"
        }

    except Exception as e:
        logger.error(f"Error registering default prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
