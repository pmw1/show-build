"""
Show-Build v2 Database Models - Segment-Centric Architecture
Episodes as flagship units, Segments as portable value units.
Every entity has an AssetID from central service.

Split into domain-focused modules:
  - enums.py: RundownItemType, ElementType, CueType
  - organization.py: Organization, Show, Season, Customer
  - episode.py: Episode, Break, Rundown, Region, RundownItem
  - content.py: Segment, Script, Element, Cue, ContentVersion, SegmentLock
  - production.py: Speaker, ProductionRole, AssetLink, AssetMessage
  - settings.py: Settings, PromptOverride, GfxXpostCue
  - jobs.py: CeleryJobLog, SOTProcessingJob
"""

# Enums
from models.enums import RundownItemType, ElementType, CueType

# Organization domain
from models.organization import Organization, Show, Season, Customer

# Episode domain
from models.episode import Episode, Break, Rundown, Region, RundownItem

# Content domain
from models.content import Segment, Script, Element, Cue, ContentVersion, SegmentLock

# Production domain
from models.production import Speaker, ProductionRole, AssetLink, AssetMessage

# Settings domain
from models.settings import Settings, PromptOverride, GfxXpostCue, WorkerDefinition

# Jobs domain
from models.jobs import CeleryJobLog, SOTProcessingJob

# Recording domain (showtime writeback)
from models.recording import (
    RecordingSession, RecordingTake, TakeMarker, TakeCueFire,
)

__all__ = [
    # Enums
    "RundownItemType", "ElementType", "CueType",
    # Organization
    "Organization", "Show", "Season", "Customer",
    # Episode
    "Episode", "Break", "Rundown", "Region", "RundownItem",
    # Content
    "Segment", "Script", "Element", "Cue", "ContentVersion", "SegmentLock",
    # Production
    "Speaker", "ProductionRole", "AssetLink", "AssetMessage",
    # Settings
    "Settings", "PromptOverride", "GfxXpostCue", "WorkerDefinition",
    # Jobs
    "CeleryJobLog", "SOTProcessingJob",
    # Recording (showtime writeback)
    "RecordingSession", "RecordingTake", "TakeMarker", "TakeCueFire",
]
