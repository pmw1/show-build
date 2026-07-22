# main.py — FastAPI application entry point

import os
import sys
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine, Base

logger = logging.getLogger(__name__)

# Ensure app directory is on Python path
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# ── Router imports ──────────────────────────────────────────────────────────

try:
    # Extracted routers (Phase 1 modularization)
    from routers.health_router import router as health_router
    from routers.upload_router import router as upload_router
    from routers.legacy_router import router as legacy_router
    from routers.misc_router import router as misc_router
    from routers.comfyui_router import router as comfyui_router

    # Authentication & Authorization
    from auth.router import router as auth_router
    from rbac_router import router as rbac_router

    # Configuration & Settings
    from api_config_router import router as api_config_router
    from settings_router import router as settings_router
    from settings_colors_router import router as settings_colors_router
    from routers.user_prefs_router import router as user_prefs_router
    from routers.messages_router import router as messages_router
    from setup_router import router as setup_router

    # Episodes & Content
    from episodes_router import router as episodes_router
    from episode_scaffold_router import router as episode_scaffold_router
    from rundown_templates_router import router as rundown_templates_router
    from content_library_router import router as content_library_router
    from script_generation_router import router as script_generation_router
    from routers.recording_sessions_router import router as recording_sessions_router

    # Assets & Media
    from assets_router import router as assets_router
    from assetid_router import router as assetid_router
    from new_assetid_router import router as new_assetid_router
    from convert_assetid_router import router as convert_assetid_router
    from media_router import router as media_router
    from media_analysis_router import router as media_analysis_router
    from repo_router import router as repo_router

    # Graphics & Production Assets
    from fsq_asset_router import router as fsq_asset_router
    from gfx_asset_router import router as gfx_asset_router
    from sot_router import router as sot_router
    from vo_router import router as vo_router

    # Legacy Cue Convert module (find-media endpoint for the /modules/legacyCueConvert frontend)
    from routers.legacy_cue_convert_router import router as legacy_cue_convert_router

    # Public website-facing API (read-only, key-gated). See docs/WEBSITE_PUBLIC_API_PLAN.md
    from routers.public import router as public_router

    # Audio & Voice
    from speakers_router import router as speakers_router
    from voice_sample_router import router as voice_sample_router
    from wpm_audio_router import router as wpm_audio_router
    from voice_model_router import router as voice_model_router
    from xtts_router import router as xtts_router
    from duration_analysis_router import router as duration_router
    from duration_estimation_router import router as duration_estimation_router

    # Organization & Shows
    from organization_router import router as organization_router
    from show_router import router as show_router

    # Templates & Documentation
    from templates_router import router as templates_router
    from docs_router import router as docs_router
    from mp3_profiles_router import router as mp3_profiles_router
    from blueprint_config_router import router as blueprint_config_router

    # LLM & AI
    from llm_proxy_router import router as llm_proxy_router
    # llm_state_router removed 2026-06-04 — orphaned /api/llm/operations +
    # /api/llm/notifications endpoints whose llm_notifications table schema no
    # longer matched the model (every call 500'd). State is now in-memory +
    # localStorage; the live notification feed is /api/llm-notifications/*.
    from prompts_router import router as prompts_router
    from segment_llm_router import router as segment_llm_router

    # Tools & Monitoring
    from tools_router import router as tools_router
    from housekeeping_router import router as housekeeping_router
    from workers_router import router as workers_router
    from celery_jobs_router import router as celery_jobs_router

    # Collaboration & Communication
    from whiteboard_router import router as whiteboard_router
    from routers.whiteboard.captures_router import router as whiteboard_captures_router
    from todos_router import router as todos_router
    from announcements_router import router as announcements_router
    from voice_conference_router import router as voice_conference_router
    from segment_locks_router import router as segment_locks_router

    # External Integrations
    from google_drive_router import router as google_drive_router
    from twitter_oauth_router import router as twitter_oauth_router
    from vmix_router import router as vmix_router

    # File & Data Management
    from file_inventory_router import router as file_inventory_router
    from consolidation_router import router as consolidation_router
    from customer_router import router as customer_router
    from production_roles_router import router as production_roles_router

except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Current directory: {os.getcwd()}")
    raise

# ── App creation ────────────────────────────────────────────────────────────

app = FastAPI(title="Show-Build", version="dev-v2.01.00")

@app.on_event("startup")
def startup_event():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    logging.info("Show-Build server started with database and background processing")

# ── Middleware ──────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static file mounts ─────────────────────────────────────────────────────

app.mount("/episodes", StaticFiles(directory="/home/episodes"), name="episodes")

for mount_path, mount_dir, mount_name in [
    ("/repo", "/home/repo", "repo"),
    ("/media_assets", "/home/media_assets", "media_assets"),
    # Unbound media pool (episodes/, ads/, repo/, whiteboard/). Whiteboard media
    # and cue-released media are served from here; was /repo/whiteboard.
    ("/pool", "/home/pool", "pool"),
    ("/api/profile-pictures", "/home/profile_pictures", "profile_pictures"),
]:
    try:
        Path(mount_dir).mkdir(parents=True, exist_ok=True)
        app.mount(mount_path, StaticFiles(directory=mount_dir), name=mount_name)
    except (PermissionError, OSError) as e:
        logger.warning(f"Could not mount {mount_path} static files: {e}")

# ── Router registration ────────────────────────────────────────────────────

# Extracted routers (from Phase 1 modularization)
app.include_router(health_router)
app.include_router(upload_router)
app.include_router(legacy_router)
app.include_router(misc_router)
app.include_router(comfyui_router)

# Authentication & Authorization
app.include_router(auth_router, prefix="/api")
app.include_router(rbac_router, prefix="/api")

# Configuration & Settings
app.include_router(api_config_router)
app.include_router(settings_router, prefix="/api")
app.include_router(settings_colors_router)
app.include_router(user_prefs_router)
app.include_router(messages_router)
app.include_router(setup_router, prefix="/api")

# Episodes & Content
app.include_router(episodes_router, prefix="/api")
app.include_router(episode_scaffold_router, prefix="/api")
app.include_router(recording_sessions_router, prefix="/api", tags=["recording-sessions"])
app.include_router(rundown_templates_router, prefix="/api/rundown-templates", tags=["rundown-templates"])
app.include_router(content_library_router)
app.include_router(script_generation_router, prefix="/api")

# Assets & Media
app.include_router(assets_router, prefix="/api", tags=["assets"])
app.include_router(assetid_router)
app.include_router(new_assetid_router)
app.include_router(convert_assetid_router, prefix="/api")
app.include_router(media_router, prefix="/api")
app.include_router(media_analysis_router)
app.include_router(repo_router)

# Graphics & Production Assets
app.include_router(fsq_asset_router, prefix="/api/fsq", tags=["fsq"])
app.include_router(gfx_asset_router, prefix="/api/gfx", tags=["gfx"])
app.include_router(sot_router)
app.include_router(vo_router)

# Legacy Cue Convert (find-media endpoint for the /modules/legacyCueConvert frontend)
app.include_router(legacy_cue_convert_router)

# Audio & Voice
app.include_router(speakers_router)
app.include_router(voice_sample_router)
app.include_router(wpm_audio_router)
app.include_router(voice_model_router)
app.include_router(xtts_router)
app.include_router(duration_router)
app.include_router(duration_estimation_router, prefix="/api")

# Organization & Shows
app.include_router(organization_router, prefix="/api")
app.include_router(show_router, prefix="/api")

# Templates & Documentation
app.include_router(templates_router, prefix="/api", tags=["templates"])
app.include_router(docs_router)
app.include_router(mp3_profiles_router, prefix="/api/settings/mp3-profiles", tags=["mp3-profiles"])
app.include_router(blueprint_config_router, prefix="/api/settings/blueprint-nodes", tags=["blueprint-config"])

# LLM & AI
app.include_router(llm_proxy_router)
app.include_router(prompts_router)
app.include_router(segment_llm_router)

# Tools & Monitoring
app.include_router(tools_router)
app.include_router(housekeeping_router, prefix="/api")
app.include_router(workers_router)
app.include_router(celery_jobs_router, prefix="/api/celery-jobs", tags=["celery-jobs"])

# Collaboration & Communication
app.include_router(whiteboard_router)
app.include_router(whiteboard_captures_router)  # capture inbox (capture-extension/), standalone mount
app.include_router(todos_router)
app.include_router(announcements_router)
app.include_router(voice_conference_router)
app.include_router(segment_locks_router)

# External Integrations
app.include_router(google_drive_router, prefix="/api", tags=["google-drive"])
app.include_router(twitter_oauth_router)
app.include_router(vmix_router, prefix="/api", tags=["vmix"])

# File & Data Management
app.include_router(file_inventory_router)
app.include_router(consolidation_router, prefix="/api", tags=["consolidation"])
app.include_router(customer_router)
app.include_router(production_roles_router, prefix="/api/production-roles", tags=["production-roles"])

# Public website-facing API (read-only). All sub-routers mounted at /public/v1.
app.include_router(public_router)
