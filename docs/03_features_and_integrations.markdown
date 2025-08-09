# Features and Integrations

## Overview
The Disaffected Production Suite provides features for pre-production content creation and integrates with external services via APIs and MQTT. This document details implemented features, API integrations, and workflows.

## Implemented Features
- **Content Editor (`ContentEditor.vue`)**:
  - Split-view Markdown and metadata editing
  - Cue insertion toolbar with shortcuts (Alt+G, Alt+Q, etc.)
  - Auto-save (3s inactivity or item switch)
  - Collapsible rundown panel
  - Accessibility features (high-contrast text, keyboard navigation)
- **Rundown Management (`RundownManager.vue`)**:
  - Drag-and-drop reordering with visual feedback
  - Automatic order assignment (increments of 10)
  - Optional filename prefixing toggle for Obsidian compatibility
- **Add New Rundown Item**:
  - Form-based creation with validation
  - Auto-generates IDs (`{type}_YYYYMMDD_###`)
  - Integrates with `/rundown/{episode_number}/item` endpoint
- **Color Management (`ColorSelector.vue`)**:
  - UI for selecting Vuetify theme colors
  - Persists selections in `localStorage`
  - Supports rundown item types and UI elements (pending synchronization with `themeColorMap.js`)

## API Integrations
- **Local AI Services**: Ollama, Whisper (content generation, transcription)
- **Cloud AI Services**: OpenAI, Anthropic, Google Gemini, X (Grok)
- **Media Services**: YouTube API, Vimeo API, AWS S3
- **Communication**: Slack, Discord, Twilio, email services (SendGrid, Mailgun, AWS SES)
- **Storage/Productivity**: Google Drive, Google Calendar
- **Development**: GitHub/GitLab, Zapier, custom webhooks
- **Specialized AI**: Stability AI (image generation), ElevenLabs (voice synthesis)
- **Social Media**: Twitter/X, Facebook, Instagram, LinkedIn, TikTok, Rumble

## Workflows
- **Content Creation**: AI-assisted script writing, media processing, storage, publishing
- **Live Production**: Real-time communication, emergency alerts, rundown updates
- **Post-Production**: Transcription, voice-over, version control, multi-platform distribution

*Last Updated: July 8, 2025*