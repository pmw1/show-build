"""
Enum types for Show-Build v2 models.
"""
import enum


class RundownItemType(str, enum.Enum):
    """Types of items that can appear in a rundown."""
    SEGMENT = "segment"
    OPEN = "open"
    COLDOPEN = "coldopen"
    TEASE = "tease"
    AD = "ad"  # Changed from "advertisement" to match frontend and be more concise
    PROMO = "promo"
    INTERVIEW = "interview"
    PACKAGE = "package"
    TRANSITION = "transition"
    STINGER = "stinger"
    REJOIN = "rejoin"
    READER = "reader"
    CLOSE = "close"
    BREAK = "break"


class ElementType(str, enum.Enum):
    """Types of media elements."""
    VIDEO = "video"
    AUDIO = "audio"
    GRAPHIC = "graphic"
    ANIMATION = "animation"
    LOWER_THIRD = "lower_third"
    QUOTE = "quote"


class CueType(str, enum.Enum):
    """Types of production cues."""
    MEDIA = "media"  # Play media element
    CAMERA = "camera"  # Camera switch
    AUDIO_MIC = "audio_mic"  # Microphone control
    LIGHTING = "lighting"  # Lighting change
    DIRECTOR = "director"  # Director note
    TALENT = "talent"  # Talent instruction
