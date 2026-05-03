"""
Segment LLM Extractor Service - Entity extraction from segment content

This service handles the extraction of entities, summaries, and quotes from
segment content using LLM APIs. Extracted data is stored in segment_llm_data
for efficient reuse in downstream AI operations.

Part of the LLM Preprocessing Layer (UFDP-compliant).
"""

import hashlib
import json
import logging
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from models_segment_llm import SegmentLLMData
from models_v2 import RundownItem
from services.asset_id import AssetIDService

logger = logging.getLogger(__name__)

# Default extraction prompt templates
DEFAULT_SYSTEM_PROMPT = """You are an expert content analyst for broadcast media production. Your task is to extract structured data from segment scripts to support downstream LLM operations like episode descriptions and social media posts.

Return valid JSON only. Be precise with entity names and roles. Extract meaningful quotes that capture key points.

Guidelines:
- People: Include name, role, their relation to the story being told, and X/Twitter handle if known
- Organizations: Include company names, media outlets, agencies, their relevance to the story
- Institutions: Include universities, government bodies, courts, non-profits
- Topics: Extract 3-7 main topics discussed
- Quotes: Select 2-5 notable, quotable statements that capture key points"""

DEFAULT_USER_PROMPT = """Analyze this segment content and extract structured data:

SEGMENT: {{segment_title}}
EPISODE: {{episode_number}}

CONTENT:
{{content}}

Return JSON in this exact format:
{
  "llm_summary": "1-2 sentence summary optimized for LLM context",
  "llm_description": "Detailed description for AI processing (3-5 sentences)",
  "extracted_people": [
    {
      "name": "Full Name",
      "role": "Guest|Host|Expert|Subject|Victim|Perpetrator|Witness|Official",
      "relation_to_story": "How this person relates to the story being told",
      "x_handle": "@username or null if unknown"
    }
  ],
  "extracted_organizations": [
    {
      "name": "Organization Name",
      "type": "company|media|agency|ngo|political|religious",
      "relation_to_story": "How this org relates to the story",
      "x_handle": "@username or null if unknown"
    }
  ],
  "extracted_institutions": [
    {
      "name": "Institution Name",
      "type": "university|government|court|military|law_enforcement|healthcare",
      "relation_to_story": "How this institution relates to the story"
    }
  ],
  "extracted_topics": ["topic1", "topic2", "topic3"],
  "key_quotes": ["Notable quote 1", "Notable quote 2"],
  "confidence": 0.85
}

Return ONLY valid JSON, no explanations or markdown."""


class SegmentLLMExtractor:
    """Service for extracting LLM data from segment content."""

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """Compute SHA256 hash of content for stale detection."""
        if not content:
            return ""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @staticmethod
    def get_extraction_prompt(db: Session, operation_key: str = "extract-segment-llm-data") -> Tuple[str, str, Dict]:
        """
        Get extraction prompts from database overrides or defaults.

        Returns:
            Tuple of (system_prompt, user_prompt_template, settings_dict)
        """
        try:
            result = db.execute(text("""
                SELECT system_prompt, user_prompt_template, temperature, max_tokens,
                       suggested_service, suggested_model
                FROM prompt_overrides
                WHERE category = 'extract' AND operation_key = :operation_key AND is_enabled = TRUE
            """), {"operation_key": operation_key})
            row = result.first()

            if row:
                return (
                    row[0] or DEFAULT_SYSTEM_PROMPT,
                    row[1] or DEFAULT_USER_PROMPT,
                    {
                        "temperature": row[2] or 0.3,
                        "max_tokens": row[3] or 2500,
                        "service": row[4] or "ollama",
                        "model": row[5] or "qwen2.5:latest"
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to load prompt override: {e}")

        # Return defaults
        return (
            DEFAULT_SYSTEM_PROMPT,
            DEFAULT_USER_PROMPT,
            {
                "temperature": 0.3,
                "max_tokens": 2500,
                "service": "ollama",
                "model": "qwen2.5:latest"
            }
        )

    @staticmethod
    def get_ollama_host(db: Session) -> str:
        """Get Ollama host from database configuration."""
        try:
            result = db.execute(text(
                "SELECT config_value FROM api_configs WHERE service = 'ollama' AND config_key = 'host'"
            )).fetchone()
            if result:
                return result[0]
        except Exception as e:
            logger.error(f"Failed to get Ollama host: {e}")
        return 'http://192.168.51.197:11434'

    @staticmethod
    def resolve_template_variables(template: str, variables: Dict[str, Any]) -> str:
        """Resolve {{variable}} placeholders in template."""
        result = template
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value) if value else "")
        return result

    @staticmethod
    async def call_llm(
        db: Session,
        system_prompt: str,
        user_prompt: str,
        settings: Dict[str, Any]
    ) -> str:
        """Call LLM API and return response text."""
        service = settings.get("service", "ollama")
        model = settings.get("model", "mistral:7b")
        temperature = settings.get("temperature", 0.2)
        max_tokens = settings.get("max_tokens", 2000)

        if service == "ollama":
            host = SegmentLLMExtractor.get_ollama_host(db)

            # Combine system and user prompts for Ollama
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{host}/api/generate",
                    json={
                        "model": model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    }
                )

                if response.status_code != 200:
                    raise Exception(f"Ollama returned status {response.status_code}: {response.text}")

                data = response.json()
                return data.get("response", "")

        else:
            raise Exception(f"Unsupported LLM service: {service}")

    @staticmethod
    def parse_extraction_response(response_text: str) -> Dict[str, Any]:
        """Parse JSON response from LLM, handling common formatting issues."""
        # Try to find JSON in the response
        text = response_text.strip()

        # Sometimes the model wraps JSON in code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()

        # Try to parse as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # Try to find a JSON object in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            raise Exception(f"Failed to parse LLM response as JSON: {e}")

    @staticmethod
    async def extract_segment_llm_data(
        db: Session,
        rundown_item_id: int,
        model: str = None,
        force: bool = False
    ) -> SegmentLLMData:
        """
        Extract LLM data from a segment's content.

        Args:
            db: Database session
            rundown_item_id: ID of the rundown item to extract from
            model: Optional model override
            force: Force re-extraction even if not stale

        Returns:
            SegmentLLMData record with extracted data
        """
        # Get the rundown item
        rundown_item = db.query(RundownItem).filter(RundownItem.id == rundown_item_id).first()
        if not rundown_item:
            raise Exception(f"Rundown item {rundown_item_id} not found")

        content = rundown_item.script_content or ""
        content_hash = SegmentLLMExtractor.compute_content_hash(content)

        # Check for existing LLM data
        existing = db.query(SegmentLLMData).filter(
            SegmentLLMData.rundown_item_id == rundown_item_id
        ).first()

        if existing and not force:
            # Check if stale
            if existing.source_content_hash == content_hash and existing.processing_status == "completed":
                logger.info(f"LLM data for item {rundown_item_id} is current, skipping extraction")
                return existing

        # Get prompts and settings
        system_prompt, user_template, settings = SegmentLLMExtractor.get_extraction_prompt(db)

        # Override model if specified
        if model:
            settings["model"] = model

        # Get episode number for template variables
        episode_number = ""
        if rundown_item.rundown and rundown_item.rundown.episode:
            episode_number = str(rundown_item.rundown.episode.episode_number or "")

        # Resolve template variables
        user_prompt = SegmentLLMExtractor.resolve_template_variables(user_template, {
            "segment_title": rundown_item.title or "Untitled",
            "episode_number": episode_number,
            "content": content
        })

        # Create or update the LLM data record
        if not existing:
            asset_id = AssetIDService.generate(entity_type="segment_llm")
            existing = SegmentLLMData(
                asset_id=asset_id,
                rundown_item_id=rundown_item_id,
                processing_status="pending"
            )
            db.add(existing)
            db.flush()

        # Update status to processing
        existing.processing_status = "processing"
        db.commit()

        try:
            # Call LLM
            logger.info(f"Extracting LLM data for rundown item {rundown_item_id}")
            response_text = await SegmentLLMExtractor.call_llm(
                db, system_prompt, user_prompt, settings
            )

            # Parse response
            extracted = SegmentLLMExtractor.parse_extraction_response(response_text)

            # Update the record with extracted data
            existing.llm_summary = extracted.get("llm_summary", "")
            existing.llm_description = extracted.get("llm_description", "")
            existing.extracted_people = extracted.get("extracted_people", [])
            existing.extracted_organizations = extracted.get("extracted_organizations", [])
            existing.extracted_institutions = extracted.get("extracted_institutions", [])
            existing.extracted_topics = extracted.get("extracted_topics", [])
            existing.key_quotes = extracted.get("key_quotes", [])

            existing.source_content_hash = content_hash
            existing.extraction_model = settings.get("model", "unknown")
            existing.extraction_timestamp = datetime.utcnow()
            existing.confidence_score = extracted.get("confidence", 0.8)
            existing.token_count = len(content.split())  # Approximate
            existing.processing_status = "completed"
            existing.processing_tier = 1
            existing.error_message = None

            # Update tier metadata
            existing.tier_metadata = {
                "tier_1": {
                    "model": settings.get("model"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "confidence": extracted.get("confidence", 0.8)
                }
            }

            db.commit()
            logger.info(f"Successfully extracted LLM data for rundown item {rundown_item_id}")
            return existing

        except Exception as e:
            logger.error(f"Failed to extract LLM data for item {rundown_item_id}: {e}")
            existing.processing_status = "failed"
            existing.error_message = str(e)[:500]
            db.commit()
            raise

    @staticmethod
    async def batch_extract(
        db: Session,
        rundown_item_ids: List[int],
        model: str = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Extract LLM data for multiple segments.

        Args:
            db: Database session
            rundown_item_ids: List of rundown item IDs to process
            model: Optional model override
            force: Force re-extraction

        Returns:
            Dict with results summary
        """
        results = {
            "total": len(rundown_item_ids),
            "completed": 0,
            "skipped": 0,
            "failed": 0,
            "errors": []
        }

        for item_id in rundown_item_ids:
            try:
                llm_data = await SegmentLLMExtractor.extract_segment_llm_data(
                    db, item_id, model=model, force=force
                )
                if llm_data.processing_status == "completed":
                    results["completed"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "rundown_item_id": item_id,
                    "error": str(e)[:200]
                })

        return results

    @staticmethod
    def check_stale(db: Session, rundown_item_id: int) -> Dict[str, Any]:
        """
        Check if a segment's LLM data is stale.

        Returns:
            Dict with stale status and details
        """
        # Get the rundown item
        rundown_item = db.query(RundownItem).filter(RundownItem.id == rundown_item_id).first()
        if not rundown_item:
            return {"stale": True, "reason": "rundown_item_not_found"}

        content = rundown_item.script_content or ""
        current_hash = SegmentLLMExtractor.compute_content_hash(content)

        # Get existing LLM data
        llm_data = db.query(SegmentLLMData).filter(
            SegmentLLMData.rundown_item_id == rundown_item_id
        ).first()

        if not llm_data:
            return {"stale": True, "reason": "no_llm_data"}

        if llm_data.processing_status == "failed":
            return {"stale": True, "reason": "previous_extraction_failed"}

        if llm_data.processing_status != "completed":
            return {"stale": True, "reason": f"status_is_{llm_data.processing_status}"}

        if llm_data.source_content_hash != current_hash:
            return {"stale": True, "reason": "content_changed"}

        return {
            "stale": False,
            "last_extraction": llm_data.extraction_timestamp.isoformat() if llm_data.extraction_timestamp else None,
            "model": llm_data.extraction_model
        }

    @staticmethod
    def get_stale_segments(db: Session, episode_number: Optional[str] = None) -> List[Dict]:
        """
        Get list of segments with stale or missing LLM data.

        Args:
            db: Database session
            episode_number: Optional filter by episode

        Returns:
            List of stale segment info dicts
        """
        # Build query for rundown items
        query = db.query(RundownItem)

        if episode_number:
            from models_v2 import Rundown, Episode
            query = query.join(Rundown).join(Episode).filter(
                Episode.episode_number == int(episode_number)
            )

        rundown_items = query.all()
        stale_items = []

        for item in rundown_items:
            stale_check = SegmentLLMExtractor.check_stale(db, item.id)
            if stale_check.get("stale"):
                stale_items.append({
                    "rundown_item_id": item.id,
                    "asset_id": item.asset_id,
                    "title": item.title,
                    "stale_reason": stale_check.get("reason")
                })

        return stale_items

    @staticmethod
    def get_episode_llm_context(db: Session, episode_number: str) -> Dict[str, Any]:
        """
        Get aggregated LLM context for an episode.

        Combines prechewed data from all segments for efficient downstream operations.

        Args:
            db: Database session
            episode_number: Episode number

        Returns:
            Dict with episode LLM context
        """
        from models_v2 import Rundown, Episode

        # Get episode rundown items
        rundown_items = db.query(RundownItem).join(Rundown).join(Episode).filter(
            Episode.episode_number == int(episode_number)
        ).order_by(RundownItem.order_in_rundown).all()

        segments_data = []
        all_people = []
        all_organizations = []
        all_institutions = []
        all_topics = set()
        all_quotes = []

        for item in rundown_items:
            llm_data = db.query(SegmentLLMData).filter(
                SegmentLLMData.rundown_item_id == item.id
            ).first()

            segment_info = {
                "rundown_item_id": item.id,
                "asset_id": item.asset_id,
                "title": item.title,
                "item_type": item.item_type,
                "duration": item.duration,
                "order": item.order_in_rundown
            }

            if llm_data and llm_data.processing_status == "completed":
                segment_info["llm_summary"] = llm_data.llm_summary
                segment_info["llm_description"] = llm_data.llm_description
                segment_info["processing_status"] = "completed"

                # Aggregate entities
                if llm_data.extracted_people:
                    all_people.extend(llm_data.extracted_people)
                if llm_data.extracted_organizations:
                    all_organizations.extend(llm_data.extracted_organizations)
                if llm_data.extracted_institutions:
                    all_institutions.extend(llm_data.extracted_institutions)
                if llm_data.extracted_topics:
                    all_topics.update(llm_data.extracted_topics)
                if llm_data.key_quotes:
                    all_quotes.extend(llm_data.key_quotes[:2])  # Limit quotes per segment
            else:
                stale_check = SegmentLLMExtractor.check_stale(db, item.id)
                segment_info["processing_status"] = "stale" if stale_check.get("stale") else "pending"
                segment_info["stale_reason"] = stale_check.get("reason")

            segments_data.append(segment_info)

        # Deduplicate entities
        def dedupe_entities(entities: List[Dict], key: str = "name") -> List[Dict]:
            seen = set()
            result = []
            for entity in entities:
                name = entity.get(key, "").lower()
                if name and name not in seen:
                    seen.add(name)
                    result.append(entity)
            return result

        return {
            "episode_number": episode_number,
            "segment_count": len(segments_data),
            "segments": segments_data,
            "aggregated": {
                "all_people": dedupe_entities(all_people),
                "all_organizations": dedupe_entities(all_organizations),
                "all_institutions": dedupe_entities(all_institutions),
                "all_topics": sorted(list(all_topics)),
                "all_quotes": all_quotes[:10]  # Limit total quotes
            },
            "template_variables": {
                "segment_summaries": "\n".join([
                    s.get("llm_summary", "") for s in segments_data
                    if s.get("llm_summary")
                ]),
                "guest_names": ", ".join([
                    p.get("name", "") for p in all_people
                    if "guest" in (p.get("role", "").lower())
                ]),
                "topics": ", ".join(sorted(list(all_topics))),
                "organizations": ", ".join([o.get("name", "") for o in dedupe_entities(all_organizations)])
            }
        }
