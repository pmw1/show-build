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


# Canonical asset subfolder per cue type. find-media searches preshow/ AND this
# assets/{episode}/{subdir} folder so "Attempt Fix" also matches media that's
# already landed in the episode's asset tree (per user direction, an assets/
# match is reprocessed the same as a preshow match).
ASSET_SUBDIR_BY_TYPE = {
    "SOT": "video", "VO": "video", "NAT": "video", "PKG": "video",
    "IMG": "images", "GFX": "images", "FSQ": "images",
    "BUMP": "audio", "STING": "audio", "MUS": "audio", "VOX": "audio",
}


# ---------------------------------------------------------------------------
# Preshow listing (RECURSIVE)
# ---------------------------------------------------------------------------
# Hosts drop source media anywhere under preshow/, including subfolders
# ("raw/", "from-josh/", etc). Every consumer — find-media candidates,
# list-media picker, and the extract-cue LLM file list — must see the whole
# tree, so this is the single scanner. Filenames are reported as paths
# RELATIVE to preshow/ ("raw/foo.mp4"); import-media resolves them back.

def _iter_preshow_files(episode: str, allowed_extensions: Optional[set] = None):
    """Yield (relative_name, Path) for every file under preshow/, recursive,
    sorted. relative_name uses forward slashes and is relative to preshow/."""
    preshow = path_manager.episodes_root / episode / "preshow"
    if not preshow.is_dir():
        return
    for p in sorted(preshow.rglob("*")):
        if not p.is_file():
            continue
        if allowed_extensions is not None and p.suffix.lower() not in allowed_extensions:
            continue
        yield p.relative_to(preshow).as_posix(), p


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


def _is_zero_trim(value: Optional[str]) -> bool:
    """True when a trim point is absent or effectively zero (00:00:00)."""
    if not value:
        return True
    return value.strip() in ("00:00:00", "00:00:00:00", "0", "0:00", "00:00")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class FindMediaRequest(BaseModel):
    episode: str = Field(..., description="Episode number (e.g. '0272')")
    slug: str = Field(..., description="Cue slug from the legacy token")
    cue_type: str = Field(..., description="Canonical cue type, e.g. 'SOT', 'IMG'")
    filename_hint: Optional[str] = Field(
        None,
        description=(
            "Optional source-file hint extracted from script context (e.g. a "
            "filename Josh noted near the cue block). Candidates are scored "
            "against BOTH the slug and this hint; the higher ratio wins."
        ),
    )
    trim_start: Optional[str] = Field(
        None,
        description=(
            "The cue's in-point (HH:MM:SS), when known. When either trim is "
            "non-zero the search is restricted to preshow/ — trims index into "
            "a source RECORDING, and files in assets/video are finished clips "
            "(matching one produced 'trim beyond end of video' failures live)."
        ),
    )
    trim_end: Optional[str] = Field(None, description="The cue's out-point (HH:MM:SS), same semantics as trim_start")


class FindMediaResponse(BaseModel):
    matched_filename: Optional[str] = None
    confidence: float = 0.0
    method: str = "none"  # "deterministic" | "llm" | "none"
    candidates_considered: int = 0
    # Where the match was found, relative to the episode dir: "preshow" or
    # "assets/{subdir}". import-media uses this to locate the source file.
    source_dir: Optional[str] = None


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

    # Collect candidates from preshow/ AND the appropriate assets/{subdir}.
    # Each candidate is tagged with the source_dir it came from so import-media
    # can find it again. (Per user direction, an assets/ match is reprocessed
    # the same way a preshow match is.)
    episode_dir = path_manager.episodes_root / request.episode

    # preshow/ is scanned RECURSIVELY (rel_name may contain subdirs);
    # assets/{subdir} stays flat. rel_name is what we return as
    # matched_filename and what import-media joins onto source_dir.
    candidates = []  # list of (path, source_dir, rel_name)
    for rel_name, p in _iter_preshow_files(request.episode, allowed_extensions):
        candidates.append((p, "preshow", rel_name))
    # Trimmed cues cut from a source RECORDING — a finished clip in
    # assets/{subdir} can never be that source (matching one caused the
    # 'Trim start beyond end of video' failures on ep 0283). Only search
    # assets/ when no trims are in play.
    has_trims = not (
        _is_zero_trim(request.trim_start) and _is_zero_trim(request.trim_end)
    )
    asset_subdir = ASSET_SUBDIR_BY_TYPE.get(cue_type)
    if asset_subdir and not has_trims:
        d = episode_dir / "assets" / asset_subdir
        if d.is_dir():
            for p in d.iterdir():
                if p.is_file() and p.suffix.lower() in allowed_extensions:
                    candidates.append((p, f"assets/{asset_subdir}", p.name))
    if not candidates:
        return FindMediaResponse(method="none")

    # Score. When the caller supplied a filename_hint (source file noted in
    # the script near the cue), score against both the slug and the hint's
    # stem and keep the better ratio — a hint like "keysha-interview-raw.mp4"
    # should beat pure slug similarity.
    target = _normalize_slug(request.slug)
    hint = _normalize_slug(Path(request.filename_hint).stem) if request.filename_hint else None
    scored = []  # list of (ratio, path, source_dir, rel_name)
    for path, source_dir, rel_name in candidates:
        stem = _normalize_slug(path.stem)
        ratio = SequenceMatcher(None, target, stem).ratio()
        if hint:
            ratio = max(ratio, SequenceMatcher(None, hint, stem).ratio())
        scored.append((ratio, path, source_dir, rel_name))
    scored.sort(key=lambda x: x[0], reverse=True)

    best_ratio, best_path, best_source_dir, best_rel = scored[0]
    second_ratio = scored[1][0] if len(scored) > 1 else 0.0

    # Deterministic resolution: clear winner above threshold
    if best_ratio >= 0.85 and (best_ratio - second_ratio) >= 0.05:
        logger.info(
            f"[find-media] deterministic match {best_rel} in {best_source_dir} "
            f"(score={best_ratio:.3f}, gap={best_ratio - second_ratio:.3f})"
        )
        return FindMediaResponse(
            matched_filename=best_rel,
            confidence=round(best_ratio, 3),
            method="deterministic",
            candidates_considered=len(scored),
            source_dir=best_source_dir,
        )

    # LLM tiebreaker: only consider top candidates with reasonable scores
    top_candidates = [(rel, path) for ratio, path, _sd, rel in scored if ratio >= 0.5][:8]
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

        file_list_str = "\n".join(rel for rel, _p in top_candidates)
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
            # 80 tokens is instantly consumed by a reasoning model's thinking
            # phase → empty response → silent no-match. Same fix as
            # extract-cue.
            think=False,
        ).strip()

        # Parse: must be exact match against the candidate list (relative
        # name, with bare-basename fallback for subdir files), or 'none'
        candidate_names = {rel: (rel, p) for rel, p in top_candidates}
        for rel, p in top_candidates:
            candidate_names.setdefault(p.name, (rel, p))
        if response_text.lower() == "none":
            return FindMediaResponse(
                method="none",
                candidates_considered=len(scored),
            )
        if response_text in candidate_names:
            chosen_rel, chosen = candidate_names[response_text]
            score_for_chosen = next((r for r, p, _sd, _rel in scored if p == chosen), 0.0)
            source_for_chosen = next((sd for r, p, sd, _rel in scored if p == chosen), None)
            return FindMediaResponse(
                matched_filename=chosen_rel,
                confidence=round(score_for_chosen, 3),
                method="llm",
                candidates_considered=len(scored),
                source_dir=source_for_chosen,
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
# Endpoint: GET /api/legacy-cue-convert/list-media
# ---------------------------------------------------------------------------
# Candidate media files for the manual source-picker: when find-media can't
# determine a source video during Attempt Fix, the frontend pops a modal
# listing these so the user can choose one. Same search dirs + extension
# filter as find-media (preshow/ first, then assets/{subdir}).

class ListMediaFile(BaseModel):
    filename: str
    source_dir: str  # "preshow" or "assets/{subdir}" — feed back to import-media
    size_bytes: int = 0
    modified: Optional[str] = None  # ISO timestamp


class ListMediaResponse(BaseModel):
    files: list[ListMediaFile] = []


@router.get("/list-media", response_model=ListMediaResponse)
async def list_media(
    episode: str,
    cue_type: str = "SOT",
    current_user=Depends(get_current_user_or_key),
) -> ListMediaResponse:
    """List candidate media files (by cue-type extension) in the episode's
    preshow/ and assets/{subdir} folders, preshow first, each alphabetical."""
    from datetime import datetime, timezone

    ct = cue_type.upper()
    allowed_extensions = EXTENSIONS_BY_TYPE.get(ct)
    if not allowed_extensions:
        return ListMediaResponse(files=[])

    episode_dir = path_manager.episodes_root / episode

    def _entry(rel_name: str, p: Path, source_dir: str) -> ListMediaFile:
        try:
            st = p.stat()
            return ListMediaFile(
                filename=rel_name,
                source_dir=source_dir,
                size_bytes=st.st_size,
                modified=datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            )
        except OSError:
            return ListMediaFile(filename=rel_name, source_dir=source_dir)

    files: list[ListMediaFile] = []
    # preshow/ is recursive; filenames are relative paths ("raw/foo.mp4").
    group = [
        _entry(rel_name, p, "preshow")
        for rel_name, p in _iter_preshow_files(episode, allowed_extensions)
    ]
    files.extend(sorted(group, key=lambda f: f.filename.lower()))

    asset_subdir = ASSET_SUBDIR_BY_TYPE.get(ct)
    if asset_subdir:
        d = episode_dir / "assets" / asset_subdir
        if d.is_dir():
            group = [
                _entry(p.name, p, f"assets/{asset_subdir}")
                for p in d.iterdir()
                if p.is_file() and p.suffix.lower() in allowed_extensions
            ]
            files.extend(sorted(group, key=lambda f: f.filename.lower()))

    return ListMediaResponse(files=files)


# ---------------------------------------------------------------------------
# Endpoint: POST /api/legacy-cue-convert/extract-cue
# ---------------------------------------------------------------------------
# LLM extraction of video-cue data from a host-pasted script block. Hosts
# paste multi-line blocks like:
#
#   (SOT/keysha eight)
#   IN-02:54:58 "do you think"
#   to
#   OUT-02:57:31 "too tripped up in his lies"
#
# with random whitespace, loose token variants, or the info buried in prose.
# The frontend gathers the flagged paragraph + its continuation lines
# (block_text) plus surrounding script context (context_text — Josh often
# notes the source file near the block) and this endpoint asks the local
# Ollama to return structured cue data. Video types only (SOT/VO/NAT).

_DEFAULT_EXTRACT_PROMPT = (
    "You extract broadcast cue data from a TV-show script excerpt.\n\n"
    "The BLOCK below describes one or more video cues a host pasted into the "
    "script. Cue types: SOT (sound on tape — a clip played with its own "
    "audio), VO (voice-over b-roll), NAT (natural sound). Blocks usually "
    "start with a token like (SOT/some slug) or (VO/slug), may span several "
    "lines with random whitespace, and often carry an in-point and out-point "
    "as IN-HH:MM:SS / OUT-HH:MM:SS (the separator after IN/OUT may be '-', "
    "':', or just a space) with short quoted phrases (the in-cue and "
    "out-cue — the first and last words spoken in the clip).\n\n"
    "BLOCK:\n{{block_text}}\n\n"
    "SURROUNDING SCRIPT CONTEXT (may name the source video file or URL, "
    "often in a note):\n{{context_text}}\n\n"
    "AVAILABLE FILES — every file in this episode's preshow folder, "
    "including subfolders (paths are relative to preshow/):\n"
    "{{file_list}}\n\n"
    "SOURCE VIDEO — for EACH cue you emit, determine which AVAILABLE FILE "
    "is its source video:\n"
    "- The block or context sometimes carries a technical production note "
    "naming the source video — e.g. \"FULL VIDEO IS TITLED "
    "'33LaKeyshaKeysha'\" — or other phrasings to the same effect. Such "
    "lines read as instructions, not as part of the surrounding narrative; "
    "use that to deduce that they name the source video.\n"
    "- A \"FROM\" line — \"FROM: <title>\", \"FROM '<title>'\", bare "
    "\"FROM <title>\" (the colon is optional), or an all-caps note like "
    "\"FROM FULL SURVEILLANCE VIDEO\" — states which video the cue is cut "
    "FROM. Treat it as naming the source video for the cue it "
    "accompanies. The title is a FUZZY reference: it will usually lack "
    "the file extension and its casing/wording may differ from the "
    "filename.\n"
    "- Match that title (or, failing that, the cue's slug/description) "
    "against the AVAILABLE FILES list. Titles rarely match filenames "
    "exactly — match loosely on the meaningful words.\n"
    "- source_file MUST be one of the AVAILABLE FILES, copied EXACTLY as "
    "listed (including any subfolder path). Never invent a filename.\n"
    "- If you cannot confidently identify the source video for a cue, set "
    'source_file to null and source_file_error to "unable to find the '
    'video". Do not guess.\n\n'
    "SCOPE — this is critical:\n"
    "- Emit cues ONLY for what the BLOCK describes. Never emit a cue for "
    "something that appears only in the context.\n"
    "- The context is used ONLY to identify source_file / source_url. "
    "Never take timecodes, quotes, or slugs from the context; the BLOCK's "
    "own IN/OUT values always win.\n\n"
    "Return ONLY a JSON object, no commentary, in exactly this shape:\n"
    '{"cues": [{"type": "SOT|VO|NAT", "slug": "short-kebab-or-word slug", '
    '"in_point": "HH:MM:SS or null", "out_point": "HH:MM:SS or null", '
    '"in_cue": "first words spoken, or null", "out_cue": "last words spoken, '
    'or null", "source_url": "http… URL if one appears, else null", '
    '"source_file": "a path from AVAILABLE FILES, else null", '
    '"source_file_error": "unable to find the video (only when source_file '
    'is null), else null"}]}\n\n'
    "Rules:\n"
    "- Only emit cues you are confident about; an empty list is valid.\n"
    "- type must be SOT, VO, or NAT (treat VOT as SOT).\n"
    "- slug: prefer the token's slug text; otherwise derive 2-4 words from "
    "the description.\n"
    "- Timecodes: normalize to HH:MM:SS. If only MM:SS is given, use "
    "00:MM:SS.\n"
    "- Do not invent timecodes, URLs, or filenames that are not present.\n"
)

# Appended to a stored/custom extract prompt that predates the
# {{file_list}} placeholder, so the LLM always sees the episode's real
# files even if the admin-edited template in api_configs is older.
_FILE_LIST_ADDENDUM = (
    "\n\nAVAILABLE FILES — every file in this episode's preshow folder, "
    "including subfolders (paths are relative to preshow/):\n"
    "{{file_list}}\n\n"
    "For EACH cue, set source_file to the AVAILABLE FILE that is its source "
    "video, copied EXACTLY as listed. Technical notes in the script like "
    "\"FULL VIDEO IS TITLED '...'\" and FROM lines (\"FROM: <title>\", "
    "\"FROM '<title>'\") name the source video the cue is cut from — they "
    "read as instructions, not narrative, and the title is a fuzzy "
    "reference that usually lacks the file extension. Match loosely on "
    "meaningful words; if you cannot confidently identify the source video "
    "for a cue, set source_file to null and add "
    '"source_file_error": "unable to find the video" to that cue. '
    "Never invent a filename.\n"
)


class ExtractCueRequest(BaseModel):
    episode: str = Field(..., description="Episode number (context only)")
    block_text: str = Field(..., description="The flagged paragraph plus its continuation lines, joined with newlines")
    context_text: Optional[str] = Field("", description="Surrounding script paragraphs / notes for source-file hints")


class ExtractedCue(BaseModel):
    type: str
    slug: str
    in_point: Optional[str] = None
    out_point: Optional[str] = None
    in_cue: Optional[str] = None
    out_cue: Optional[str] = None
    source_url: Optional[str] = None
    source_file: Optional[str] = None
    # True when source_file was verified against the episode's actual
    # preshow tree (exact relative path, after normalization below). The
    # frontend skips fuzzy find-media and imports the file directly.
    source_file_verified: bool = False
    # LLM's per-cue failure signal ("unable to find the video") when it
    # could not confidently pick a source from the available files.
    source_file_error: Optional[str] = None


class ExtractCueResponse(BaseModel):
    cues: list[ExtractedCue] = []
    method: str = "llm"  # "llm" | "none"


_TIMECODE_RE = re.compile(r"^(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?$")


def _normalize_timecode(value: Optional[str]) -> Optional[str]:
    """Normalize '2:54:58' / '02:54' → 'HH:MM:SS'. Returns None if unparseable."""
    if not value:
        return None
    m = _TIMECODE_RE.match(value.strip())
    if not m:
        return None
    a, b, c = m.group(1), m.group(2), m.group(3)
    if c is None:
        h, mnt, s = 0, int(a), int(b)      # MM:SS
    else:
        h, mnt, s = int(a), int(b), int(c)  # HH:MM:SS
    if mnt > 59 or s > 59:
        return None
    return f"{h:02d}:{mnt:02d}:{s:02d}"


def _verify_preshow_file(name: str, listing: list[str]) -> Optional[str]:
    """Resolve an LLM-returned source_file against the real preshow listing.
    Accepts an exact relative path (case-insensitive) or a unique basename
    match. Returns the canonical relative path, or None if unverifiable."""
    name = name.strip().lstrip("/").replace("\\", "/")
    if not name:
        return None
    by_exact = {rel.lower(): rel for rel in listing}
    hit = by_exact.get(name.lower())
    if hit:
        return hit
    base = name.rsplit("/", 1)[-1].lower()
    basename_hits = [rel for rel in listing if rel.rsplit("/", 1)[-1].lower() == base]
    if len(basename_hits) == 1:
        return basename_hits[0]
    return None


def _parse_llm_json(raw: str) -> Optional[dict]:
    """Tolerant JSON extraction: strip <think> blocks and code fences, then
    parse the outermost {...} span. Returns None on failure."""
    import json as _json
    text_out = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    text_out = re.sub(r"```(?:json)?", "", text_out).strip()
    start = text_out.find("{")
    end = text_out.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return _json.loads(text_out[start:end + 1])
    except Exception:
        return None


@router.post("/extract-cue", response_model=ExtractCueResponse)
async def extract_cue(
    request: ExtractCueRequest,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db),
) -> ExtractCueResponse:
    """LLM-extract structured video-cue data (SOT/VO/NAT) from a pasted
    script block. Returns an empty cue list (method='none') on any LLM
    failure so the frontend can fall back to the regex conversion path."""
    if not request.block_text.strip():
        return ExtractCueResponse(cues=[], method="none")

    try:
        host = get_ollama_host(db)
        model = get_ollama_model(db, purpose='legacy_cue_match')

        prompt_row = db.execute(text(
            "SELECT config_value FROM api_configs "
            "WHERE workflow = 'generation' AND category = 'llm' "
            "AND service = 'legacy_cue_convert' AND config_key = 'extract_cue_prompt' "
            "AND is_enabled = true LIMIT 1"
        )).fetchone()
        prompt_template = (prompt_row[0] if prompt_row else _DEFAULT_EXTRACT_PROMPT) or _DEFAULT_EXTRACT_PROMPT

        # RECURSIVE preshow file list for this episode — the LLM picks each
        # cue's source_file from this list (or fails with source_file_error).
        # Stored custom templates may predate the placeholder; append the
        # addendum so the list is always present.
        all_preshow_files = [rel for rel, _p in _iter_preshow_files(request.episode)]
        prompt_files = all_preshow_files
        if len(prompt_files) > 300:
            logger.warning(
                f"[extract-cue] preshow listing truncated to 300 of "
                f"{len(prompt_files)} files for ep {request.episode}"
            )
            prompt_files = prompt_files[:300]
        file_list_str = "\n".join(prompt_files) if prompt_files else "(no files found)"
        if "{{file_list}}" not in prompt_template:
            prompt_template = prompt_template + _FILE_LIST_ADDENDUM

        rendered = render_template(prompt_template, {
            "block_text": request.block_text[:4000],
            "context_text": (request.context_text or "")[:6000],
            "file_list": file_list_str,
        })

        # Retry once on unparseable/empty output (temp 0 → 0.15): tokenless
        # blocks have no regex fallback, so one bad sample would surface as
        # a user-visible failure. think=False is CRITICAL — reasoning models
        # (qwen3) otherwise burn the whole num_predict budget on the thinking
        # phase with real-sized prompts and return an EMPTY response (the
        # "AI could not extract" failures seen live on ep 0283).
        parsed = None
        for attempt, temp in enumerate((0.0, 0.15)):
            raw = call_ollama(
                host=host,
                model=model,
                prompt=rendered,
                temperature=temp,
                max_tokens=3000,
                timeout=120,
                think=False,
            )
            parsed = _parse_llm_json(raw)
            if parsed and isinstance(parsed.get("cues"), list):
                break
            logger.warning(
                f"[extract-cue] unparseable LLM response "
                f"(attempt {attempt + 1}): {raw[:300]!r}"
            )
            parsed = None
    except Exception as exc:
        logger.error(f"[extract-cue] LLM call failed: {exc}")
        return ExtractCueResponse(cues=[], method="none")

    if not parsed:
        return ExtractCueResponse(cues=[], method="none")

    valid_types = {"SOT": "SOT", "VOT": "SOT", "VO": "VO", "NAT": "NAT"}
    cues: list[ExtractedCue] = []
    for entry in parsed["cues"]:
        if not isinstance(entry, dict):
            continue
        ctype = valid_types.get(str(entry.get("type", "")).strip().upper())
        slug = str(entry.get("slug") or "").strip()
        if not ctype or not slug:
            continue

        def _clean(key):
            v = entry.get(key)
            v = str(v).strip() if v is not None else ""
            return v if v and v.lower() not in ("null", "none") else None

        # Verify the LLM's source pick against the episode's real preshow
        # tree. Verified → frontend imports it directly (no fuzzy match).
        # Unverified non-null → kept as a fuzzy hint for find-media.
        # Null → the LLM's own "unable to find the video" failure stands.
        source_file = _clean("source_file")
        source_file_error = _clean("source_file_error")
        source_file_verified = False
        if source_file:
            resolved = _verify_preshow_file(source_file, all_preshow_files)
            if resolved:
                source_file = resolved
                source_file_verified = True
                source_file_error = None
            else:
                logger.info(
                    f"[extract-cue] LLM source_file '{source_file}' not in "
                    f"preshow listing — passing through as a hint only"
                )
        elif not source_file_error:
            source_file_error = "unable to find the video"

        cues.append(ExtractedCue(
            type=ctype,
            slug=slug,
            in_point=_normalize_timecode(_clean("in_point")),
            out_point=_normalize_timecode(_clean("out_point")),
            in_cue=_clean("in_cue"),
            out_cue=_clean("out_cue"),
            source_url=_clean("source_url"),
            source_file=source_file,
            source_file_verified=source_file_verified,
            source_file_error=source_file_error,
        ))

    # ------------------------------------------------------------------
    # Deterministic post-validation. The prompt's SCOPE rule alone does
    # not stop qwen3-class models from (a) emitting cues gleaned from the
    # CONTEXT (e.g. a neighboring flagged block's token) or (b) letting
    # context text override the block's own IN/OUT — both observed live
    # on ep 0283. Two guards:
    #
    # 1. Slug-anchored filter: every real cue's slug comes from the block
    #    (token slug or block wording), so at least one significant slug
    #    word must appear in block_text. Cues failing this were read out
    #    of the context — drop them. Never filter to zero: if nothing
    #    passes, keep the original list rather than fabricate a hard fail.
    # 2. Block-authoritative trims: when exactly one cue remains and the
    #    block itself carries uppercase IN/OUT timecode markers, those
    #    values ALWAYS win over whatever the model returned.
    # ------------------------------------------------------------------
    block_lower = request.block_text.lower()

    def _slug_anchored(c: ExtractedCue) -> bool:
        words = [w for w in re.split(r"[^a-z0-9]+", c.slug.lower()) if len(w) >= 3]
        return not words or any(w in block_lower for w in words)

    anchored = [c for c in cues if _slug_anchored(c)]
    if anchored and len(anchored) < len(cues):
        dropped = [c.slug for c in cues if c not in anchored]
        logger.info(f"[extract-cue] dropped context-bleed cue(s): {dropped}")
        cues = anchored

    if len(cues) == 1:
        # Separator after IN/OUT is optional — hosts write IN-02:54:58,
        # OUT: 2:05, and bare IN 29:14 interchangeably.
        m_in = re.search(r"\bIN\s*[-–—:]*\s*(\d{1,2}:\d{2}(?::\d{2})?)", request.block_text)
        m_out = re.search(r"\bOUT\s*[-–—:]*\s*(\d{1,2}:\d{2}(?::\d{2})?)", request.block_text)
        if m_in:
            cues[0].in_point = _normalize_timecode(m_in.group(1)) or cues[0].in_point
        if m_out:
            cues[0].out_point = _normalize_timecode(m_out.group(1)) or cues[0].out_point

    return ExtractCueResponse(cues=cues, method="llm" if cues else "none")


class ExtractPromptResponse(BaseModel):
    prompt: str
    is_default: bool = False


@router.get("/extract-cue-prompt", response_model=ExtractPromptResponse)
async def get_extract_cue_prompt(
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db),
) -> ExtractPromptResponse:
    """Return the editable LLM prompt for pasted-block cue extraction."""
    row = db.execute(text(
        "SELECT config_value FROM api_configs "
        "WHERE workflow = 'generation' AND category = 'llm' "
        "AND service = 'legacy_cue_convert' AND config_key = 'extract_cue_prompt' LIMIT 1"
    )).fetchone()
    stored = row[0] if row and row[0] else None
    if stored:
        return ExtractPromptResponse(prompt=stored, is_default=(stored == _DEFAULT_EXTRACT_PROMPT))
    return ExtractPromptResponse(prompt=_DEFAULT_EXTRACT_PROMPT, is_default=True)


@router.put("/extract-cue-prompt", response_model=ExtractPromptResponse)
async def update_extract_cue_prompt(
    request: PromptUpdate,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db),
) -> ExtractPromptResponse:
    """Persist a new extraction prompt (upsert into api_configs)."""
    db.execute(text("""
        INSERT INTO api_configs (workflow, category, service, config_key, config_value, is_enabled)
        VALUES ('generation', 'llm', 'legacy_cue_convert', 'extract_cue_prompt', :v, true)
        ON CONFLICT (workflow, category, service, config_key)
        DO UPDATE SET config_value = EXCLUDED.config_value, is_enabled = true, updated_at = now()
    """), {"v": request.prompt})
    db.commit()
    return ExtractPromptResponse(prompt=request.prompt, is_default=(request.prompt == _DEFAULT_EXTRACT_PROMPT))


@router.post("/extract-cue-prompt/reset", response_model=ExtractPromptResponse)
async def reset_extract_cue_prompt(
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db),
) -> ExtractPromptResponse:
    """Restore the seeded default extraction prompt."""
    db.execute(text("""
        INSERT INTO api_configs (workflow, category, service, config_key, config_value, is_enabled)
        VALUES ('generation', 'llm', 'legacy_cue_convert', 'extract_cue_prompt', :v, true)
        ON CONFLICT (workflow, category, service, config_key)
        DO UPDATE SET config_value = EXCLUDED.config_value, is_enabled = true, updated_at = now()
    """), {"v": _DEFAULT_EXTRACT_PROMPT})
    db.commit()
    return ExtractPromptResponse(prompt=_DEFAULT_EXTRACT_PROMPT, is_default=True)


# ---------------------------------------------------------------------------
# Endpoint: POST /api/legacy-cue-convert/persist-conversion
# ---------------------------------------------------------------------------
# Server-side persistence of a completed Attempt Fix conversion. The editor
# calls this right after splicing the converted cue block(s) into the
# document, so the conversion survives even when the browser session's save
# path is broken (seen live 2026-07-18: a frozen autosave orphaned every
# conversion — pipelines completed but their cue blocks only ever existed in
# browser memory, and the completion write-back found nothing to update).
#
# The rundown item is located BY CONTENT: the flagged block's paragraph
# texts must match exactly one item in the episode. The matched paragraph
# span is replaced with the converted segments (cue markdown verbatim,
# prose re-wrapped as <p class="{speaker}">). Idempotent: if every cue
# AssetID is already present in the item, it's a no-op success.

_P_TAG_RE = re.compile(r"<p\b[^>]*>([\s\S]*?)</p>", re.IGNORECASE)


def _normalize_block_line(s: str) -> str:
    """Normalize a paragraph's text for matching: strip tags/entities, drop
    the '*** ' flag marker, collapse whitespace."""
    s = re.sub(r"<[^>]+>", "", s or "")
    s = (s.replace("&nbsp;", " ").replace("&amp;", "&")
         .replace("&lt;", "<").replace("&gt;", ">")
         .replace("&quot;", '"').replace("&#39;", "'"))
    s = re.sub(r"^\s*\*\*\*\s*", "", s.strip())
    return re.sub(r"\s+", " ", s)


class PersistSegment(BaseModel):
    type: str  # "cue" | "text"
    content: str


class PersistConversionRequest(BaseModel):
    episode: str = Field(..., description="Episode number (e.g. '0283')")
    speaker: str = Field("josh", description="Speaker class for re-wrapped prose paragraphs")
    block_lines: list[str] = Field(..., description="Plain-text lines of the replaced flagged block, in document order")
    segments: list[PersistSegment] = Field(..., description="Replacement segments: cue markdown verbatim, prose as text")


class PersistConversionResponse(BaseModel):
    persisted: bool
    reason: Optional[str] = None
    rundown_item_id: Optional[int] = None


@router.post("/persist-conversion", response_model=PersistConversionResponse)
async def persist_conversion(
    request: PersistConversionRequest,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db),
) -> PersistConversionResponse:
    wanted = [_normalize_block_line(l) for l in request.block_lines]
    wanted = [w for w in wanted if w]
    if not wanted or not request.segments:
        return PersistConversionResponse(persisted=False, reason="empty block or segments")

    cue_asset_ids = []
    for seg in request.segments:
        if seg.type == "cue":
            m = re.search(r"\[Asset\s*[Ii][Dd]:\s*([^\]\s][^\]]*)\]", seg.content)
            if m:
                cue_asset_ids.append(m.group(1).strip())

    rows = db.execute(text("""
        SELECT ri.id, ri.script_content
        FROM rundown_items ri
        JOIN rundowns r ON r.id = ri.rundown_id
        JOIN episodes e ON e.id = r.episode_id
        WHERE e.episode_number = CAST(:ep AS INTEGER)
          AND ri.script_content IS NOT NULL
    """), {"ep": int(request.episode)}).fetchall()

    matches = []  # (item_id, content, span_start, span_end)
    for item_id, content in rows:
        paras = [(m.start(), m.end(), _normalize_block_line(m.group(1)))
                 for m in _P_TAG_RE.finditer(content)]
        non_empty = [(s, e, t) for s, e, t in paras if t]
        for i in range(len(non_empty) - len(wanted) + 1):
            window = non_empty[i:i + len(wanted)]
            if [t for _s, _e, t in window] == wanted:
                matches.append((item_id, content, window[0][0], window[-1][1]))
                break

    if not matches:
        # Idempotency: the conversion may already be persisted (block gone,
        # cues in place) — treat that as success.
        if cue_asset_ids:
            for item_id, content in rows:
                if all(aid in content for aid in cue_asset_ids):
                    return PersistConversionResponse(
                        persisted=True, reason="already persisted", rundown_item_id=item_id)
        return PersistConversionResponse(persisted=False, reason="block not found in any rundown item")
    if len(matches) > 1:
        return PersistConversionResponse(
            persisted=False,
            reason=f"block matched {len(matches)} rundown items — ambiguous",
        )

    item_id, content, span_start, span_end = matches[0]
    chunks = []
    for seg in request.segments:
        body = (seg.content or "").strip()
        if not body:
            continue
        if seg.type == "cue":
            chunks.append(body)
        else:
            chunks.append(f'<p class="{request.speaker}">{body}</p>')
    replacement = "\n\n".join(chunks)
    new_content = content[:span_start] + replacement + content[span_end:]

    db.execute(text(
        "UPDATE rundown_items SET script_content = :c, updated_at = now() WHERE id = :i"
    ), {"c": new_content, "i": item_id})
    db.commit()
    logger.info(
        f"[persist-conversion] item {item_id}: replaced {len(wanted)} paragraph(s) "
        f"with {len(chunks)} segment(s), cues={cue_asset_ids}"
    )
    return PersistConversionResponse(persisted=True, rundown_item_id=item_id)


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
    source_filename: str = Field(..., description="Filename of the matched media — must be the matched_filename returned by /find-media")
    asset_id: Optional[str] = Field(None, description="The cue's AssetID, used for SOT/VO Celery job context")
    source_dir: Optional[str] = Field("preshow", description="Where the file lives relative to the episode dir: 'preshow' or 'assets/{subdir}' — the source_dir returned by /find-media. Defaults to 'preshow' for back-compat.")
    trim_start: Optional[str] = Field(None, description="Optional in-point (HH:MM:SS) from the host's script block — passed to the SOT/VO pipeline so the trim phase cuts to it")
    trim_end: Optional[str] = Field(None, description="Optional out-point (HH:MM:SS), same semantics as trim_start")


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

    # Resolve and verify the source file. source_dir is "preshow" or
    # "assets/{subdir}" (from find-media); fall back to preshow for back-compat.
    # Constrain to a known set so a crafted source_dir can't escape the episode.
    source_dir = (request.source_dir or "preshow").strip("/")
    allowed_source_dirs = {"preshow"} | {
        f"assets/{sub}" for sub in ("video", "images", "audio", "graphics")
    }
    if source_dir not in allowed_source_dirs:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source_dir '{source_dir}'"
        )
    # source_filename may be a RELATIVE path within source_dir (preshow is
    # scanned recursively, e.g. "raw/foo.mp4"). Reject anything that could
    # escape the directory.
    rel_filename = request.source_filename.replace("\\", "/").lstrip("/")
    if not rel_filename or ".." in rel_filename.split("/"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source_filename '{request.source_filename}'"
        )
    source_base = path_manager.episodes_root / request.episode / source_dir
    source_path = source_base / rel_filename
    try:
        source_path.resolve().relative_to(source_base.resolve())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source_filename '{request.source_filename}'"
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
                trim_start=request.trim_start or "00:00:00",
                trim_end=request.trim_end or "00:00:00",
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
                trim_start=request.trim_start or "00:00:00",
                trim_end=request.trim_end or "00:00:00",
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
                media_url=f"episodes/{request.episode}/preshow/{rel_filename}",
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
