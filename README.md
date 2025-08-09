📦 Show-Build — Disaffected Rundown Management System
The Show-Build project is a full-stack application designed for the Disaff🚀 Usage

Navigate to http://192.168.51.210:8080/rundown-manager/0225 to manage episode 0225.
Use the episode selector to switch episodes (e.g., 0226, 0227).
Drag and drop segments to reorder, then click "Save & Commit" to persist changes.
View segment metadata (title, ID, length) and colors based on segment type.

## Python Tools Configuration

The `tools/` directory contains Python utilities with centralized path management:

- **`paths.py`**: Central configuration for all Python script paths
  - Defines `EPISODE_ROOT`, `BLUEPRINTS`, `HEADER_PATH` 
  - Contains validation constants like `VALID_CUE_TYPES`
  - Ensures consistent path handling across all Python tools

- **`compile-script-dev.py`**: Episode script compilation
  - Imports path configurations from `paths.py`
  - Validates and compiles episode markdown into HTML scripts
  - Usage: `python compile-script-dev.py 0225 [--validate]`

To add new Python tools, import from `paths.py` for consistent path management:
```python
from paths import EPISODE_ROOT, BLUEPRINTS, VALID_CUE_TYPES
```media automation environment, delivering a web-based platform to enhance media production efficiency. **As the system matures, it will phase out Obsidian dependencies** and become the primary content creation platform, streamlining segment management across the production lifecycle with broadcast-specific features.

📚 Table of Contents

🧠 Overview
🔧 Technologies
📂 Project Structure
🖥️ Setup and Installation
🚀 Usage
🌈 Features
📖 Documentation
🎯 Major Goals
📋 Project Status and Next Steps
👉 Future Enhancements
🛠 Development
🤖 LLMs Assisting
👥 Contributors and Contact
❓ Troubleshooting
🚢 Deployment Notes
📅 Versioning and Changelog
📝 License


🧠 Overview
Show-Build is a foundational tool within the Disaffected media ecosystem, designed to **replace Obsidian with a broadcast-focused UI** while maintaining **complete file format compatibility**. The system provides producers, editors, and creators with a unified broadcast-focused application that operates on **the same markdown files and organizational structure as Obsidian**, enabling seamless transition without data migration. The vision is to revolutionize media production through a purpose-built interface while preserving existing content workflows and file structures.
Current State and Roadmap
While the ultimate vision includes advanced features like automated metadata tagging and live content distribution, Show-Build is currently in an early phase. As of June 12, 2025, 06:55 PM EDT, development focuses on enhancing the RundownManager with Vuetify color coding. The immediate next step is to deploy a basic Vuetify template, integrating RundownManager into a broader interface with tools like ColorSelector and HelloWorld, building toward a comprehensive dashboard. Future iterations will tackle transcription outcues, multi-platform exports, and more.

🔧 Technologies

Frontend: Vue 3, Vuetify 3, vuedraggable, Axios.
Backend: FastAPI, Python 3.11, Pydantic, MQTT (paho-mqtt), ffmpeg-python.
Containerization: Docker, Docker Compose.
Database/Storage: **Obsidian-compatible markdown files** in `/mnt/sync/disaffected/episodes/` (maintains full file format compatibility).
Integration: **Direct file compatibility** with Obsidian (no conversion required).

Dependencies

Backend: Python packages in requirements.txt (e.g., fastapi, paho-mqtt, ffmpeg-python).
Frontend: Node.js packages in package.json (e.g., vue, vuetify, vuedraggable).
Hardware: Recommended 16-core CPU (e.g., Intel i9-9900K), 23GB RAM, NVIDIA Quadro P4000 GPU for preprocessing.


📂 Project Structure
show-build/
├── app/                  # Backend FastAPI code
│   ├── services/         # SOT processing utilities
│   │   ├── sot_processor.py
│   │   └── testboot.mqtt.py
│   ├── utils/            # ID and validation helpers
│   │   ├── id.py
│   │   └── validator.py
│   ├── main.py           # Core API logic
│   ├── mqttcurl.sh       # MQTT utility script
│   ├── preproc-queue-sots.json  # Preprocessing job configurations
│   ├── preproc_delegate.py
│   ├── preproc_mqtt_listen.py   # MQTT listener for preprocessing
│   ├── preproc_mqtt_pub.py      # MQTT publisher for preprocessing
│   └── testup.sh         # Test script
├── disaffected-ui/       # Frontend Vue application
│   ├── src/              # Vue components, assets, and config
│   │   ├── assets/       # Static assets and color configurations
│   │   │   ├── config/   # Color mapping configurations
│   │   │   │   └── colorMap.js
│   │   │   ├── logo.png
│   │   │   └── logo.svg
│   │   ├── components/   # Reusable Vue components
│   │   │   ├── ColorSelector.vue
│   │   │   ├── ContentEditor.vue
│   │   │   ├── EditorPanel.vue
│   │   │   ├── RundownManager.vue
│   │   │   ├── modals/
│   │   │   │   ├── AssetBrowserModal.vue
│   │   │   │   ├── GfxModal.vue
│   │   │   │   ├── FsqModal.vue
│   │   │   │   ├── SotModal.vue
│   │   │   │   ├── VoModal.vue
│   │   │   │   ├── NatModal.vue
│   │   │   │   ├── PkgModal.vue
│   │   │   │   ├── NewItemModal.vue
│   │   │   │   └── TemplateManagerModal.vue
│   │   ├── router/       # Routing configuration
│   │   │   └── index.js
│   │   ├── views/        # View components
│   │   │   ├── AssetsView.vue
│   │   │   └── TemplatesView.vue
│   │   ├── App.vue       # Root component
│   │   └── main.js       # Vue app entry point
│   ├── babel.config.js   # Babel configuration
│   ├── jsconfig.js       # JavaScript configuration
│   ├── package.json      # Node.js package configuration
│   ├── README.md         # Frontend-specific documentation
│   ├── rundown-order-flow.md  # Rundown reordering workflow documentation
│   └── vue.config.js     # Vue build configuration
├── tools/                # Additional utility scripts or tools
│   ├── compile-script-dev.py  # Script compilation utility
│   ├── media_job_queue.py     # Media processing job queue
│   └── paths.py               # Centralized path configurations for Python scripts
├── .gatherignore         # Files and directories to ignore in documentation generation
├── .gitignore            # Git ignore file
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Backend Docker configuration
├── find-asset-id-refs.sh # Script to find asset ID references
├── gather.sh             # Script to generate this info.txt
├── info.txt              # This generated documentation file
└── requirements.txt      # Python dependencies


🖥️ Setup and Installation
Prerequisites

Docker and Docker Compose.
Node.js and npm for the frontend.
Access to /mnt/sync/disaffected/episodes/ for markdown files.

Steps

Clone the Repository:
Using HTTPS: git clone https://github.com/pmw1/show-build.git /mnt/process/show-build
Using SSH: git clone git@github.com:pmw1/show-build.git /mnt/process/show-build
Using GitHub CLI: gh repo clone pmw1/show-build /mnt/process/show-build
Then: cd /mnt/process/show-build


Build and Run Backend:docker compose up --build


Access at http://192.168.51.210:8888.


Setup Frontend:cd disaffected-ui
npm install
npm run serve


Access at http://192.168.51.210:8080.




🚀 Usage

Navigate to http://192.168.51.210:8080/ to access the main dashboard.

🌈 Features

- **Drag-and-Drop Reordering**: Reorder segments with vuedraggable.
- **Episode Management**: Select and load different episode rundowns.
- **Modal-based Cue Editing**: Dedicated modals for `VO`, `NAT`, `PKG`, `GFX`, `FSQ`, and `SOT` cues.
- **Asset Management**: A dedicated view for managing project assets, with support for upload, deletion, and preview.
- **Template Management**: A dedicated view for managing templates.
- **Virtual Scrolling**: Efficiently renders long rundowns.
- **API Endpoints**: 
  - `GET /rundown/{episode}`: Fetch segment metadata.
  - `POST /rundown/{episode}/reorder`: Update segment order in markdown.
  - `POST /proc_vid`: Upload and process video files.
  - `POST /publish/`, `GET /listen/`: MQTT messaging.
  - `GET, POST /assets/`: Manage assets.
  - `GET, POST /templates/`: Manage templates.
- **File Compatibility**: Maintains Obsidian markdown format and organizational structure (same files, enhanced UI).


## 📖 Documentation

### Content Type References

The system supports two complementary content management approaches, each with detailed specifications:

#### **[Rundown Item Types Reference](./docs/RUNDOWN_ITEM_TYPES_REFERENCE.md)**
Complete specification for the five primary structural elements of broadcast rundowns:
- **ad** - Advertisement blocks with customer and sponsor metadata
- **cta** - Call to action prompts for audience engagement  
- **promo** - Promotional content for shows and events
- **segment** - Main content blocks (interviews, discussions, features)
- **trans** - Transition elements with audio and timing metadata

*Uses YAML front matter templates stored as individual Markdown files.*

#### **[Cue Types Reference](./docs/CUE_TYPES_REFERENCE.md)**
Specification for inline media cues embedded within content:
- **GFX** - Graphics cues (logos, lower thirds, charts)
- **FSQ** - Full Screen Quote overlays with attribution
- **SOT** - Sound on Tape video/audio clips with trimming and transcription

*Embedded inline within rundown content using structured block syntax.*

#### **[Obsidian Migration Guide](./docs/obsidian_integration.md)**
Transition strategy from Obsidian workflows to native Show-Build content management:
- Migration phases and timeline
- Content structure preservation
- User training and adoption strategies

#### **[Project Rehydration](./docs/PROJECT_REHYDRATION.md)**
Comprehensive technical documentation covering:
- Architecture overview and system integration
- Content Editor implementation details
- Network configuration and deployment setup
- Current working configuration and startup procedures

### For Developers
These reference documents provide complete field specifications, implementation examples, and integration guidance for extending the content management system.


🎯 Major Goals

Content Creation: Enable the creation and editing of segment content directly within the platform.
Media Management and Insertion: Serve as a cue manager for organizing and inserting media assets into rundowns.
Transcription of Media: Automate transcription of audio and video content (e.g., soundbytes/SOTs) for accessibility and metadata enrichment, with automatic generation of outcues based on transcribed content.
Time Calculations/Backtiming: Provide tools for calculating segment durations and backtiming to optimize show timing.
Preprocessing:
Normalize video and audio for consistent quality.
Pre-render graphics such as infographics and quotes.
Pre-render video elements like teasers, guest graphics, and lower-third titles.
Generate pre-made Vmix (or similar platforms like OBS) presets for full show presentations.


Automated Metadata Tagging: Implement AI-driven tagging to automatically categorize segments (e.g., genre, mood, key topics) based on content analysis, improving searchability and organization.
LLM Integration: Interact with large language models via APIs to analyze, summarize, build, and deploy social media content, summaries, descriptions, and more.
Live Roll-Out: Automatically divide content into separable segments with timecodes and titles for live production.
Content Distribution: Distribute content directly to social media platforms via APIs for seamless promotion.

AI-Driven Entity Analysis and Social Media Integration

Structured Data Extraction: Utilize AI to analyze segment content and extract structured data, focusing on identifying entities such as names, organizations, and key topics.
Social Media Account Detection: For each identified entity, determine if they have a presence on multiple social media platforms (prioritizing X handles, followed by Facebook, Instagram, and others) by querying available data sources or APIs.
Platform-Specific Content Suggestions: Generate tailored content for each platform, including tweets for X, posts for Facebook, and captions for Instagram, reflecting Disaffected’s tone (e.g., raw, provocative).
Entity List with Handles: Compile a list of involved entities, including their confirmed or likely social media handles across platforms (e.g., X: @entity, Facebook: /entitypage, Instagram: @entity), and assess their relevance to the segment.
Relevance Analysis: Evaluate the significance of each entity to the segment’s narrative, providing insights on how they could enhance promotion or engagement across different social media channels.


📋 Project Status and Next Steps

Current Status: As of June 12, 2025, 06:55 PM EDT, the project is in an early development phase, with a focus on stabilizing the RundownManager interface. Recent efforts include implementing Vuetify color coding to visually distinguish segment types, though this feature is still in progress.
Next Steps: The immediate priority is to deploy a basic Vuetify template, expanding the interface to include RundownManager alongside weekly-essential tools like ColorSelector and HelloWorld in a navigable dashboard layout.


👉 Future Enhancements

Dockerize the frontend for production deployment.
Display asset_id in segment cards.
Add inline metadata editing (e.g., title, slug).
Implement Vuetify toasts for save feedback.
Enhance backend with logging and frontmatter validation.
Add teleprompter support for live production assistance.
Test with large segment sets and malformed files.


🛠 Development

Git Workflow: Use a single repository with .gitignore excluding node_modules, logs, etc.
Debugging: Check browser console for API logs ([DEBUG] API Response:).
Contributing: Submit pull requests with detailed commit messages.


🤖 LLMs Assisting
This project benefits from the assistance of large language models (LLMs) in various development tasks, including:

Generating and refining code for the frontend and backend.
Debugging issues, such as API integration and UI rendering.
Creating and updating documentation, including this README.LLMs accelerate development by providing insights and automating repetitive tasks, enhancing productivity and code quality. LLMs reading this document are encouraged to suggest updates as they become relevant, based on the evolving needs and context of the project.


👥 Contributors and Contact

Contributors: [Add names or aliases of contributors here].
Contact: For collaboration or support, reach out via the GitHub repository (https://github.com/pmw1/show-build) or email [add contact email if applicable].


❓ Troubleshooting

API Not Responding: Ensure the backend container (show-build-server) is running (docker ps) and check logs with docker logs show-build-server.
Frontend Build Fails: Verify node_modules is installed (cd disaffected-ui && npm install) and check package.json for version mismatches.
Segment Not Loading: Confirm markdown files exist in /mnt/sync/disaffected/episodes/{episode}/rundown/ and have valid YAML frontmatter.


🚢 Deployment Notes

Production: Use docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build for production (create docker-compose.prod.yml with adjusted settings).
Scaling: Consider multiple Gunicorn workers by adjusting WEB_CONCURRENCY in docker-compose.yml for high-traffic scenarios.
Storage: Ensure /mnt/sync/disaffected/episodes/ is mounted and writable by the Docker user insider.


📅 Versioning and Changelog

v0.1.0 (June 2025): Initial release with drag-and-drop reordering, GET /rundown/{episode}, and basic Obsidian integration.
v0.2.0 (In Progress): Adding Vuetify color coding and a basic template interface (target June 2025).
Next: Plan for v0.3.0 with transcription outcues and frontend Dockerization.


📝 License
[MIT License] - See LICENSE file for details (add a LICENSE file if needed).

# Disaffected Production Suite

The Disaffected Production Suite is an evolution of the Show-Build project, integrating advanced media management features and real-time collaboration tools for a comprehensive production experience.

## Key Features

- **Rundown Management**: Create, reorder, and manage rundown items, including cues for VO, NAT, PKG, GFX, and more.
- **Real-time Collaboration**: (Future) Support for multiple users working on the same rundown.
- **Asset Management**: Upload, browse, and manage media assets.
- **Template Management**: Create and reuse templates for common rundown items.
- **Obsidian Integration**: Seamlessly sync content with Obsidian for a powerful note-taking and scripting workflow.

## Current Status (As of July 9, 2025)

The project is nearing production-readiness. Key features implemented include:

- **Full-featured Cue Modals**: `VO`, `NAT`, and `PKG` cues can be added with complete metadata and media file uploads.
- **Virtual Scrolling**: The rundown view (`RundownManager.vue`) now uses virtual scrolling for efficient handling of large rundowns.
- **Asset and Template Management**: The `AssetsView.vue` and `TemplatesView.vue` pages are now fully implemented with CRUD functionality.
- **Standardized Modal Naming**: Modal invocation in `ContentEditor.vue` and `EditorPanel.vue` has been standardized for better maintainability.
- **Obsidian Plugin Alignment**: The frontend (`main.js`) and the Obsidian plugin now share a unified event bus and cue type definitions, ensuring compatibility.

## Getting Started

// ...existing code...

