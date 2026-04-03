"""
Settings router — backward-compatibility shim.
Actual implementation lives in routers/settings/ package.
"""
from routers.settings import router  # noqa: F401

# Re-export shared utilities that other modules may import
from routers.settings import (  # noqa: F401
    load_settings,
    save_settings,
    derive_paths,
    format_bytes,
    camel_to_snake,
    SETTINGS_FILE,
    MediaPathSettings,
    InterfaceSettings,
    RundownSettings,
    SystemSettings,
    GenerationSettings,
    AutosaveHistorySettings,
    SettingsUpdate,
)
