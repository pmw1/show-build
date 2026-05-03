"""
Legacy Cue Convert — backend endpoints.

Single endpoint today:
  POST /api/legacy-cue-convert/find-media
    Locate the best matching media file in episodes/{episode}/preshow/
    for a given (slug, cue_type). Hybrid resolver: deterministic
    fuzzy match first; LLM tiebreaker on ambiguity / low confidence.

The LLM prompt and model both live in api_configs and are reachable
through Settings → LLM Routing (model) and Settings → Interface →
Content Editor → Legacy Cue Convert (prompt).
"""
import logging
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth.utils import get_current_user_or_key
from core.paths import paths as path_manager
from database import get_db
from services.auto_description_service import (
    call_ollama,
    get_ollama_host,
    get_ollama_model,
    render_template,
)
from services.cue_media_import import (
    start_sot_processing_from_path,
    start_vo_processing_from_path,
    save_image_from_path,
    save_audio_from_path,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/legacy-cue-convert", tags=["Legacy Cue Convert"])


# ---------------------------------------------------------------------------
# Extension filtering per cue type
# ---------------------------------------------------------------------------
# Used by find-media to narrow the candidate list. Types not listed here
# (DIR/RIF/NOTE) skip the media lookup entirely.
EXTENSIONS_BY_TYPE = {
    # Video
    "SOT": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    "VO":  {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    "NAT": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    "PKG": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    # Image
    "IMG": {".png", ".jpg", ".jpeg", ".webp", ".gif"},
    "GFX": {".png", ".jpg", ".jpeg", ".webp", ".gif"},
    "FSQ": {".png", ".jpg", ".jpeg", ".webp", ".gif"},
    # Audio
    "BUMP":  {".mp3", ".wav", ".m4a", ".ogg", ".flac"},
    "STING": {".mp3", ".wav", ".m4a", ".ogg", ".flac"},
    "MUS":   {".mp3", ".wav", ".m4a", ".ogg", ".flac"},
    "VOX":   {".mp3", ".wav", ".m4a", ".ogg", ".flac"},
    # LIVE: typically a placeholder cue with no media file in preshow/.
    "LIVE":  set(),
}


# ---------------------------------------------------------------------------
# Slug normalization (mirrors the frontend's sanitizeSlug)
# ---------------------------------------------------------------------------

def _normalize_slug(s: str) -> str:
    """Mirror of disaffected-ui sanitizeSlug:
    lowercase → strip non-[a-z0-9 -] → spaces→hyphens → collapse → trim."""
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class FindMediaRequest(BaseModel):
    episode: str = Field(..., description="Episode number (e.g. '0272')")
    slug: str = Field(..., description="Cue slug from the legacy token")
    cue_type: str = Field(..., description="Canonical cue type, e.g. 'SOT', 'IMG'")


class FindMediaResponse(BaseModel):
    matched_filename: Optional[str] = None
    confidence: float = 0.0
    method: str = "none"  # "deterministic" | "llm" | "none"
    candidates_considered: int = 0


# ---------------------------------------------------------------------------
# Endpoint: POST /api/legacy-cue-convert/find-media
# ---------------------------------------------------------------------------

@router.post("/find-media", response_model=FindMediaResponse)
async def find_media(
    request: FindMediaRequest,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db),
) -> FindMediaResponse:
    """
    Resolve a legacy-cue slug to a media file in the episode's preshow/
    folder. Returns null when no candidate clears the threshold.

    Algorithm:
      1. List preshow/ files filtered by extension (per cue_type).
      2. Score each candidate's stem against the slug with
         difflib.SequenceMatcher.ratio (case-insensitive, normalized).
      3. If exactly one candidate scores ≥ 0.85 AND beats second-best
         by ≥ 0.05, return it as method='deterministic'.
      4. Otherwise, if any candidates exist, ask Ollama to pick from
         the top-N candidates. Use the prompt + model from api_configs.
      5. If LLM returns 'none' or fails, return method='none'.
    """
    cue_type = request.cue_type.upper()

    # Types we don't look up media for (LIVE/RIF/NOTE/DIR/CUE)
    allowed_extensions = EXTENSIONS_BY_TYPE.get(cue_type)
    if not allowed_extensions:
        return FindMediaResponse(
            matched_filename=None,
            confidence=0.0,
            method="none",
            candidates_considered=0,
        )

    # Resolve the preshow folder
    preshow_dir = path_manager.episodes_root / request.episode / "preshow"
    if not preshow_dir.is_dir():
        logger.info(f"[find-media] preshow dir does not exist: {preshow_dir}")
        return FindMediaResponse(method="none")

    # Collect candidates
    candidates = [
        p for p in preshow_dir.iterdir()
        if p.is_file() and p.suffix.lower() in allowed_extensions
    ]
    if not candidates:
        return FindMediaResponse(method="none")

    # Score
    target = _normalize_slug(request.slug)
    scored = []
    for path in candidates:
        stem = _normalize_slug(path.stem)
        ratio = SequenceMatcher(None, target, stem).ratio()
        scored.append((ratio, path))
    scored.sort(key=lambda x: x[0], reverse=True)

    best_ratio, best_path = scored[0]
    second_ratio = scored[1][0] if len(scored) > 1 else 0.0

    # Deterministic resolution: clear winner above threshold
    if best_ratio >= 0.85 and (best_ratio - second_ratio) >= 0.05:
        logger.info(
            f"[find-media] deterministic match {best_path.name} "
            f"(score={best_ratio:.3f}, gap={best_ratio - second_ratio:.3f})"
        )
        return FindMediaResponse(
            matched_filename=best_path.name,
            confidence=round(best_ratio, 3),
            method="deterministic",
            candidates_considered=len(scored),
        )

    # LLM tiebreaker: only consider top candidates with reasonable scores
    top_candidates = [path for ratio, path in scored if ratio >= 0.5][:8]
    if not top_candidates:
        return FindMediaResponse(
            method="none",
            candidates_considered=len(scored),
        )

    try:
        host = get_ollama_host(db)
        model = get_ollama_model(db, purpose='legacy_cue_match')

        # Load editable prompt template from api_configs
        prompt_row = db.execute(text(
            "SELECT config_value FROM api_configs "
            "WHERE workflow = 'generation' AND category = 'llm' "
            "AND service = 'legacy_cue_convert' AND config_key = 'media_match_prompt' "
            "AND is_enabled = true LIMIT 1"
        )).fetchone()
        prompt_template = (prompt_row[0] if prompt_row else _DEFAULT_PROMPT) or _DEFAULT_PROMPT

        file_list_str = "\n".join(p.name for p in top_candidates)
        rendered = render_template(prompt_template, {
            "type": cue_type,
            "slug": request.slug,
            "file_list": file_list_str,
        })

        response_text = call_ollama(
            host=host,
            model=model,
            prompt=rendered,
            temperature=0.0,
            max_tokens=80,
            timeout=15,
        ).strip()

        # Parse: must be exact match against the candidate list, or 'none'
        candidate_names = {p.name: p for p in top_candidates}
        if response_text.lower() == "none":
            return FindMediaResponse(
                method="none",
                candidates_considered=len(scored),
            )
        if response_text in candidate_names:
            chosen = candidate_names[response_text]
            score_for_chosen = next((r for r, p in scored if p == chosen), 0.0)
            return FindMediaResponse(
                matched_filename=chosen.name,
                confidence=round(score_for_chosen, 3),
                method="llm",
                candidates_considered=len(scored),
            )
        logger.warning(
            f"[find-media] LLM returned '{response_text}' which is not in "
            f"the candidate list — treating as no-match"
        )
    except Exception as exc:
        logger.error(f"[find-media] LLM tiebreaker failed: {exc}")

    return FindMediaResponse(
        method="none",
        candidates_considered=len(scored),
    )


# Fallback prompt if the api_configs row was deleted somehow. Also used
# by the reset-to-default endpoint below.
_DEFAULT_PROMPT = (
    "You are matching a script cue slug to a media filename in a TV-show "
    "production folder.\n\n"
    "Cue type: {{type}}\n"
    "Cue slug: {{slug}}\n"
    "Available filenames in the preshow folder:\n{{file_list}}\n\n"
    "Pick the filename whose stem most likely refers to the same media as "
    "the cue slug.\n"
    'Respond with ONLY the exact filename, or the single word "none" if no '
    "candidate is a likely match.\n"
    "Do not include extensions in the response unless they are part of the "
    "filename. Do not explain.\n"
)


# ---------------------------------------------------------------------------
# Prompt CRUD — read/update/reset the editable LLM prompt template.
# Used by Settings → Interface → Content Editor → Legacy Cue Convert.
# ---------------------------------------------------------------------------

class PromptResponse(BaseModel):
    prompt: str
    is_default: bool = False


class PromptUpdate(BaseModel):
    prompt: str = Field(..., description="New prompt template body")


def _read_prompt(db: Session) -> Optional[str]:
    row = db.execute(text(
        "SELECT config_value FROM api_configs "
        "WHERE workflow = 'generation' AND category = 'llm' "
        "AND service = 'legacy_cue_convert' AND config_key = 'media_match_prompt' "
        "LIMIT 1"
    )).fetchone()
    return row[0] if row and row[0] else None


@router.get("/media-match-prompt", response_model=PromptResponse)
async def get_media_match_prompt(
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db),
) -> PromptResponse:
    """Return the editable LLM prompt template for media matching."""
    stored = _read_prompt(db)
    if stored:
        return PromptResponse(prompt=stored, is_default=(stored == _DEFAULT_PROMPT))
    return PromptResponse(prompt=_DEFAULT_PROMPT, is_default=True)


@router.put("/media-match-prompt", response_model=PromptResponse)
async def update_media_match_prompt(
    request: PromptUpdate,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db),
) -> PromptResponse:
    """Persist a new prompt template (upsert into api_configs)."""
    db.execute(text("""
        INSERT INTO api_configs (workflow, category, service, config_key, config_value, is_enabled)
        VALUES ('generation', 'llm', 'legacy_cue_convert', 'media_match_prompt', :v, true)
        ON CONFLICT (workflow, category, service, config_key)
        DO UPDATE SET config_value = EXCLUDED.config_value, is_enabled = true, updated_at = now()
    """), {"v": request.prompt})
    db.commit()
    return PromptResponse(prompt=request.prompt, is_default=(request.prompt == _DEFAULT_PROMPT))


@router.post("/media-match-prompt/reset", response_model=PromptResponse)
async def reset_media_match_prompt(
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db),
) -> PromptResponse:
    """Restore the seeded default prompt body."""
    db.execute(text("""
        INSERT INTO api_configs (workflow, category, service, config_key, config_value, is_enabled)
        VALUES ('generation', 'llm', 'legacy_cue_convert', 'media_match_prompt', :v, true)
        ON CONFLICT (workflow, category, service, config_key)
        DO UPDATE SET config_value = EXCLUDED.config_value, is_enabled = true, updated_at = now()
    """), {"v": _DEFAULT_PROMPT})
    db.commit()
    return PromptResponse(prompt=_DEFAULT_PROMPT, is_default=True)


# ---------------------------------------------------------------------------
# Endpoint: POST /api/legacy-cue-convert/import-media
# ---------------------------------------------------------------------------
# Called by conversion.js right after find-media returns a hit. Routes the
# resolved preshow file through the same backend function each cue type's
# manual modal uses today (via app/services/cue_media_import.py), so a
# converted cue ends up with media in the canonical assets/ subdirectory
# and (for SOT/VO) the FFmpeg pipeline kicks off as it would for a manual
# insert.

class ImportMediaRequest(BaseModel):
    episode: str = Field(..., description="Episode number (e.g. '0272')")
    slug: str = Field(..., description="Sanitized cue slug")
    cue_type: str = Field(..., description="Canonical cue type, e.g. 'SOT'")
    source_filename: str = Field(..., description="Filename inside episodes/{episode}/preshow/ — must be the matched_filename returned by /find-media")
    asset_id: Optional[str] = Field(None, description="The cue's AssetID, used for SOT/VO Celery job context")


class ImportMediaResponse(BaseModel):
    media_url: Optional[str] = None
    target_path: Optional[str] = None
    method: str = "skip"  # "sot_pipeline" | "vo_pipeline" | "image_copy" | "audio_copy" | "preshow_link" | "skip_generator" | "skip"
    processing_job_id: Optional[str] = None  # SOT/VO temp_job_id when the Celery pipeline was dispatched


@router.post("/import-media", response_model=ImportMediaResponse)
async def import_media(
    request: ImportMediaRequest,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db),
) -> ImportMediaResponse:
    """
    Move/process a media file from preshow/ to its canonical home for a
    converted cue. Per-type behavior:

      SOT / VO       → kick off the same Celery pipeline a manual modal
                       triggers; cue's [MediaURL] points to the future
                       location in assets/video/ (the pipeline writes
                       there on completion).
      IMG            → synchronous copy/rename to assets/images/.
      BUMP/STING/MUS/VOX → synchronous copy/rename to assets/audio/.
      NAT / PKG      → no working backend pipeline — link MediaURL
                       directly to the preshow file. See ACTIVE_WORK_QUEUE.md.
      GFX / FSQ      → generators, not uploaders. Returns media_url=null;
                       the user finishes the cue via the modal's generation
                       flow.
      LIVE / NOTE / RIF / CUE → no media. Returns media_url=null.
    """
    cue_type = request.cue_type.upper()

    # Resolve and verify the source file
    source_path = (
        path_manager.episodes_root
        / request.episode
        / "preshow"
        / request.source_filename
    )
    if not source_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Source file not found: {source_path}"
        )

    # Type-dispatched import
    try:
        if cue_type == "SOT":
            result = start_sot_processing_from_path(
                db=db,
                source_path=source_path,
                episode=request.episode,
                slug=request.slug,
                asset_id=request.asset_id,
            )
            # Pipeline output destination — predictable from the slug.
            return ImportMediaResponse(
                media_url=f"episodes/{request.episode}/assets/video/{request.slug}.mp4",
                target_path=result["working_dir"],
                method="sot_pipeline",
                processing_job_id=result["temp_job_id"],
            )

        if cue_type == "VO":
            result = start_vo_processing_from_path(
                db=db,
                source_path=source_path,
                episode=request.episode,
                slug=request.slug,
                asset_id=request.asset_id,
            )
            return ImportMediaResponse(
                media_url=f"episodes/{request.episode}/assets/video/{request.slug}.mp4",
                target_path=result["working_dir"],
                method="vo_pipeline",
                processing_job_id=result["temp_job_id"],
            )

        if cue_type == "IMG":
            result = save_image_from_path(
                source_path=source_path,
                episode=request.episode,
                slug=request.slug,
            )
            return ImportMediaResponse(
                media_url=result["media_url"].lstrip("/"),  # cue MediaURL is relative
                target_path=result["target_path"],
                method="image_copy",
            )

        if cue_type in ("BUMP", "STING", "MUS", "VOX"):
            result = save_audio_from_path(
                source_path=source_path,
                episode=request.episode,
                slug=request.slug,
                asset_id=request.asset_id,
            )
            return ImportMediaResponse(
                media_url=result["media_url"].lstrip("/"),
                target_path=result["target_path"],
                method="audio_copy",
            )

        if cue_type in ("NAT", "PKG"):
            # No working backend pipeline (the manual modal POSTs to the
            # decommissioned whisperbox host). Link directly to preshow.
            return ImportMediaResponse(
                media_url=f"episodes/{request.episode}/preshow/{request.source_filename}",
                method="preshow_link",
            )

        if cue_type in ("GFX", "FSQ"):
            # These are generators, not uploaders. Conversion produces a
            # media-less cue; the user runs the modal's generation flow.
            return ImportMediaResponse(method="skip_generator")

        # LIVE / NOTE / RIF / CUE / unknown
        return ImportMediaResponse(method="skip")

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception(f"[import-media] failed for cue_type={cue_type}")
        raise HTTPException(status_code=500, detail=f"Import failed: {exc}")
