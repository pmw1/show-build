"""
File Inventory LLM Service - V2 with Slot-Based Prompts
Semantic file matching using LLM with strict JSON responses and Ollama/OpenAI integration.
"""

import json
import logging
import requests
from typing import Dict, Any, Optional
import openai

logger = logging.getLogger(__name__)

# Ollama configuration — last-resort defaults if api_configs is unreachable
OLLAMA_BASE_URL = "http://172.17.0.1:11434"
DEFAULT_MODEL = "qwen3:32b-q4_K_M"


def _read_file_inventory_config():
    """Read host + primary + fallback model from api_configs at call time."""
    try:
        from database import SessionLocal
        from sqlalchemy import text as _t
        db = SessionLocal()
        try:
            host_row = db.execute(_t(
                "SELECT config_value FROM api_configs WHERE service='ollama' AND config_key='host' LIMIT 1"
            )).fetchone()
            host = host_row[0] if host_row and host_row[0] else OLLAMA_BASE_URL

            rows = db.execute(_t(
                "SELECT config_key, config_value FROM api_configs "
                "WHERE workflow='file_inventory' AND service='ollama' "
                "AND config_key IN ('model','fallback_model')"
            )).fetchall()
            primary, fallback = DEFAULT_MODEL, None
            for k, v in rows:
                if k == 'model' and v:
                    primary = v
                elif k == 'fallback_model' and v:
                    fallback = v
            return host, primary, fallback
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"file_inventory config lookup failed, using defaults: {e}")
        return OLLAMA_BASE_URL, DEFAULT_MODEL, None


class OllamaLLMService:
    """Real Ollama LLM service for file inventory"""

    def __init__(self, base_url: str = None, model: str = None):
        cfg_host, cfg_primary, cfg_fallback = _read_file_inventory_config()
        self.base_url = base_url or cfg_host
        self.model = model or cfg_primary
        self.fallback_model = cfg_fallback
        self.provider = "ollama"

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.1, response_format: str = "json", max_tokens: int = 2000, top_p: float = 0.9):
        """
        Generate LLM response using Ollama API.

        Args:
            system_prompt: System instructions
            user_prompt: User query
            temperature: 0.0-2.0 (lower = more deterministic) - default 0.1 for stricter adherence
            response_format: "json" to request JSON response
            max_tokens: Maximum tokens to generate (ensures complete output)
            top_p: Nucleus sampling parameter (0.9 allows diverse token choices)

        Returns:
            JSON string response
        """
        candidates = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            candidates.append(self.fallback_model)

        last_exc = None
        for idx, model_name in enumerate(candidates):
            try:
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": temperature,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "top_p": top_p
                    }
                }
                if response_format == "json":
                    payload["format"] = "json"

                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=180
                )
                if response.status_code == 404 and idx < len(candidates) - 1:
                    logger.warning(f"file_inventory: model {model_name} 404, trying fallback")
                    continue
                response.raise_for_status()
                return response.json()["message"]["content"]
            except requests.exceptions.RequestException as e:
                last_exc = e
                logger.error(f"Ollama API error with model {model_name}: {e}")
                if idx < len(candidates) - 1:
                    continue
                raise
            except Exception as e:
                logger.error(f"Error generating LLM response: {e}")
                raise
        if last_exc:
            raise last_exc


class OpenAILLMService:
    """OpenAI LLM service for file inventory"""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.provider = "openai"
        openai.api_key = api_key

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3, response_format: str = "json"):
        """
        Generate LLM response using OpenAI API.

        Args:
            system_prompt: System instructions
            user_prompt: User query
            temperature: 0.0-2.0 (lower = more deterministic)
            response_format: "json" to request JSON response

        Returns:
            JSON string response
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Build API call parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }

            # Add JSON mode if requested
            if response_format == "json":
                params["response_format"] = {"type": "json_object"}

            response = openai.chat.completions.create(**params)
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


# Default prompts for slot matching
DEFAULT_PROMPTS = {
    "inventory-match-file-to-slot": {
        "category": "inventory",
        "system_prompt": """You are a file classification expert analyzing episode production files.

Your task: Determine if a file satisfies a specific slot expectation.

Respond ONLY with valid JSON in this exact format:
{
  "matches": true/false,
  "confidence": 0-100,
  "reasoning": "brief explanation why it matches or doesn't",
  "block_id": "A/B/C/D" (only if file is a block capture/export),
  "break_id": "1/2/3" (only if file is a break recording),
  "guest_name": "name" (only if file is guest-related)
}

Be strict: Only match if the file clearly satisfies the slot's purpose and characteristics.
Confidence guidelines:
- 95-100: Perfect match, all characteristics align
- 85-94: Strong match, minor discrepancies
- 75-84: Probable match, some uncertainty
- Below 75: Weak match, significant doubts""",
        "user_prompt_template": """SLOT EXPECTATION:
- Slot: {{slot}}
- Purpose: {{purpose}}
- Characteristics: {{characteristics}}
- Location hints: {{location_hints}}
- Episode: {{episode}}

FILE TO EVALUATE:
- Path: {{file_path}}
- Filename: {{filename}}
- Extension: {{extension}}
- Size: {{size}} bytes
- Folder: {{folder_path}}
- Dimensions: {{dimensions}}
- Aspect Ratio: {{aspect_ratio}}
- Modified: {{modified}}

Does this file satisfy the slot expectation? Respond with JSON."""
    },

    "inventory-classify-stray-file": {
        "category": "inventory",
        "system_prompt": """You are classifying files that don't match any expected slot.

Categories:
- script.rundown_item: Markdown rundown files (keep these)
- stray.misplaced_asset: Asset in wrong directory (relocate)
- stray.test_file: Test/dummy files (delete)
- stray.backup: Backup/old versions (review before delete)
- stray.duplicate: Duplicate of another file (review/delete)
- stray.temp: Temporary/cache files (delete)
- stray.system: OS system files like .DS_Store (ignore/delete)
- stray.sync_conflict: Sync conflict files (review)
- stray.unknown: Can't determine purpose (review)

Respond with JSON:
{
  "category": "one of above",
  "confidence": 0-100,
  "reasoning": "why you classified it this way",
  "suggested_action": "keep/delete/relocate/review",
  "relocation_target": "path" (only if action=relocate),
  "safety": "safe/caution/dangerous"
}

Safety levels:
- safe: Can act on immediately
- caution: Review recommended
- dangerous: Manual review required""",
        "user_prompt_template": """FILE TO CLASSIFY:
- Path: {{file_path}}
- Filename: {{filename}}
- Extension: {{extension}}
- Size: {{size}} bytes
- Folder: {{folder_path}}
- Dimensions: {{dimensions}}
- Modified: {{modified}}

This file didn't match any expected slot. What is it and what should we do with it? Respond with JSON."""
    },

    "inventory-batch-match-slots": {
        "category": "inventory",
        "system_prompt": """You are a file classification expert analyzing episode production files.

Your task: Match files from a directory tree to expected file slots based on their purpose and characteristics.

IMPORTANT RULES:
1. A slot can remain EMPTY if no matching file exists - this is completely normal and acceptable
2. DO NOT force every slot to be filled
3. DO NOT match files that don't truly fit the slot characteristics
4. If no file matches a slot's requirements, return empty array for that slot
5. Only match files when you have reasonable confidence (75%+) they serve the slot's purpose
6. Multiple files can match the same slot ONLY if the slot characteristics indicate "multiple files"
7. A single file should NOT match multiple slots - choose the BEST fit

**CRITICAL**: You MUST return a JSON object with EXACTLY the slot names provided in the user prompt.
Ensure ALL slots are included in your response, even if their matches array is empty.

Return your analysis as valid JSON with this structure:
{
  "slot_name_1": {
    "matches": ["relative/path/to/file1.ext"],
    "confidence": 85,
    "reasoning": "Brief explanation"
  },
  "slot_name_2": {
    "matches": [],
    "confidence": 0,
    "reasoning": "No matching file found in directory tree"
  },
  "slot_name_3": {
    "matches": [],
    "confidence": 0,
    "reasoning": "No matching file found in directory tree"
  }
}

Use EMPTY ARRAY [] for slots with no matches.
Be strict: It is BETTER to leave a slot empty than to make a poor match.
Missing files are normal in production workflows - many slots will be unfilled.

Respond ONLY with valid JSON, no additional text.""",
        "user_prompt_template": """EPISODE: {{episode_number}}

DIRECTORY TREE:
{{file_tree}}

SLOTS TO EVALUATE:
The following {{slot_count}} slots MUST ALL appear in your JSON response:
{{slot_list}}

**CRITICAL**: Ensure ALL {{slot_count}} slots listed above are included in your response, even if empty.

SLOT DEFINITIONS:

{{slot_definitions}}

CRITICAL RULES:
- You MUST ONLY match files that appear in the DIRECTORY TREE above
- DO NOT invent, suggest, or create filenames - even if they fit the pattern
- DO NOT match files based on what "should" exist or what the examples show
- ONLY match files from the exact list in the directory tree
- It is NORMAL and EXPECTED for many slots to be empty
- Return empty array [] for slots with no matching files
- Use the relative path EXACTLY as shown in the directory tree

For each slot above, identify matching files from the directory tree.
Return JSON with ALL {{slot_count}} slot results, using empty arrays for unfilled slots.

IMPORTANT: If a file is not listed in the DIRECTORY TREE above, it does NOT exist - do not match it.

Example JSON structure (you must include ALL {{slot_count}} slots):
{
  "slot_1": {"matches": [], "confidence": 0, "reasoning": "..."},
  "slot_2": {"matches": ["file.ext"], "confidence": 90, "reasoning": "..."},
  "slot_3": {"matches": [], "confidence": 0, "reasoning": "..."}
}"""
    }
}


def get_inventory_prompt(operation_key: str, variables: Dict[str, Any], db_session = None):
    """
    Get LLM prompt with optional database override support.

    Args:
        operation_key: Operation identifier (e.g., 'inventory-match-file-to-slot')
        variables: Variables to substitute in template
        db_session: Database session for override lookup (optional)

    Returns:
        Tuple of (system_prompt, user_prompt, overridden)
    """
    # Get default prompt
    if operation_key not in DEFAULT_PROMPTS:
        raise ValueError(f"Unknown operation: {operation_key}")

    default = DEFAULT_PROMPTS[operation_key]
    system_prompt = default["system_prompt"]
    user_prompt_template = default["user_prompt_template"]
    overridden = False

    # Check for database override (if session provided)
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
                    user_prompt_template = override.user_prompt_template
                overridden = True
                logger.info(f"Using database override for {operation_key}")
        except Exception as e:
            logger.warning(f"Could not check for prompt override: {e}")

    # Substitute variables in user prompt
    user_prompt = user_prompt_template
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        user_prompt = user_prompt.replace(placeholder, str(value))

    return system_prompt, user_prompt, overridden


async def match_file_to_expectation(
    file_info: Dict[str, Any],
    expectation: Dict[str, Any],
    llm_service,
    db_session = None
) -> Dict[str, Any]:
    """
    Use LLM to determine if a file matches a slot expectation.

    Args:
        file_info: File metadata dictionary
        expectation: Slot expectation dictionary
        llm_service: LLM service instance
        db_session: Database session for prompt overrides

    Returns:
        Match result dictionary with confidence score
    """
    try:
        # Build prompt variables
        variables = {
            "slot": expectation.get("slot", "unknown"),
            "purpose": expectation.get("purpose", ""),
            "characteristics": expectation.get("characteristics", ""),
            "location_hints": expectation.get("location_hints", ""),
            "episode": "unknown",  # Will be filled by caller
            "file_path": file_info.get("relative_path", file_info.get("path", "")),
            "filename": file_info.get("filename", ""),
            "extension": file_info.get("extension", ""),
            "size": file_info.get("size", 0),
            "folder_path": file_info.get("folder_path", ""),
            "dimensions": file_info.get("dimensions", "N/A"),
            "aspect_ratio": file_info.get("aspect_ratio", "N/A"),
            "modified": file_info.get("modified", "N/A")
        }

        # Get prompts (with optional override)
        system_prompt, user_prompt, overridden = get_inventory_prompt(
            "inventory-match-file-to-slot",
            variables,
            db_session
        )

        # Call LLM
        response_text = await llm_service.generate(
            system_prompt,
            user_prompt,
            temperature=0.3,
            response_format="json"
        )

        # Parse JSON response
        result = json.loads(response_text)

        # Validate response format
        if "matches" not in result or "confidence" not in result:
            logger.warning(f"Invalid LLM response format: {response_text}")
            return {
                "matches": False,
                "confidence": 0,
                "reasoning": "Invalid LLM response format"
            }

        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        return {
            "matches": False,
            "confidence": 0,
            "reasoning": f"JSON parse error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error in match_file_to_expectation: {e}")
        return {
            "matches": False,
            "confidence": 0,
            "reasoning": f"Error: {str(e)}"
        }


async def classify_stray_file(
    file_info: Dict[str, Any],
    llm_service,
    db_session = None
) -> Dict[str, Any]:
    """
    Classify a file that didn't match any slot expectation.

    Args:
        file_info: File metadata dictionary
        llm_service: LLM service instance
        db_session: Database session for prompt overrides

    Returns:
        Classification result dictionary
    """
    try:
        # Build prompt variables
        variables = {
            "file_path": file_info.get("relative_path", file_info.get("path", "")),
            "filename": file_info.get("filename", ""),
            "extension": file_info.get("extension", ""),
            "size": file_info.get("size", 0),
            "folder_path": file_info.get("folder_path", ""),
            "dimensions": file_info.get("dimensions", "N/A"),
            "modified": file_info.get("modified", "N/A")
        }

        # Get prompts (with optional override)
        system_prompt, user_prompt, overridden = get_inventory_prompt(
            "inventory-classify-stray-file",
            variables,
            db_session
        )

        # Call LLM
        response_text = await llm_service.generate(
            system_prompt,
            user_prompt,
            temperature=0.5,  # Slightly higher for classification
            response_format="json"
        )

        # Parse JSON response
        result = json.loads(response_text)

        # Validate response format
        if "category" not in result:
            logger.warning(f"Invalid classification response: {response_text}")
            return {
                "category": "stray.unknown",
                "confidence": 0,
                "reasoning": "Invalid LLM response format",
                "suggested_action": "review",
                "safety": "caution"
            }

        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse classification JSON: {e}")
        return {
            "category": "stray.unknown",
            "confidence": 0,
            "reasoning": f"JSON parse error: {str(e)}",
            "suggested_action": "review",
            "safety": "caution"
        }
    except Exception as e:
        logger.error(f"Error in classify_stray_file: {e}")
        return {
            "category": "stray.unknown",
            "confidence": 0,
            "reasoning": f"Error: {str(e)}",
            "suggested_action": "review",
            "safety": "caution"
        }


def register_default_prompts(db_session):
    """
    Register default inventory prompts in database for Prompt Manager UI.
    """
    try:
        from models_v2 import PromptOverride
        from datetime import datetime
        import uuid

        for operation_key, prompt_data in DEFAULT_PROMPTS.items():
            # Check if already exists
            existing = db_session.query(PromptOverride).filter(
                PromptOverride.operation_key == operation_key
            ).first()

            if not existing:
                override = PromptOverride(
                    # id will be generated automatically by default=uuid.uuid4
                    category=prompt_data["category"],
                    operation_key=operation_key,
                    system_prompt=prompt_data["system_prompt"],
                    user_prompt_template=prompt_data["user_prompt_template"],
                    is_enabled=False,  # Disabled by default
                    notes=f"Default prompt for {operation_key}",
                    created_by="system",
                    created_at=datetime.utcnow()
                )
                db_session.add(override)

        db_session.commit()
        logger.info("Registered default inventory prompts")

    except Exception as e:
        logger.error(f"Error registering default prompts: {e}")
        db_session.rollback()
        raise
