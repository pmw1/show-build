📦 Show-Build — Disaffected Rundown Management System
The Show-Build project is a full-stack application designed for the Disaffected media automation environment, delivering a web-based platform to enhance media production efficiency. It integrates with Obsidian and other markdown workflows, aiming to streamline segment management across the production lifecycle.

📚 Table of Contents

🧠 Overview
🔧 Technologies
📂 Project Structure
🖥️ Setup and Installation
🚀 Usage
🌈 Features
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
Show-Build is a foundational tool within the Disaffected media ecosystem, designed to empower producers, editors, and creators by centralizing episode rundown management. It leverages markdown integration for editorial flexibility and supports automated workflows to reduce manual effort, with a vision to revolutionize media production through scalability and collaboration.
Current State and Roadmap
While the ultimate vision includes advanced features like automated metadata tagging and live content distribution, Show-Build is currently in an early phase. As of June 12, 2025, 06:55 PM EDT, development focuses on enhancing the RundownManager with Vuetify color coding. The immediate next step is to deploy a basic Vuetify template, integrating RundownManager into a broader interface with tools like ColorSelector and HelloWorld, building toward a comprehensive dashboard. Future iterations will tackle transcription outcues, multi-platform exports, and more.

🔧 Technologies

Frontend: Vue 3, Vuetify 3, vuedraggable, Axios.
Backend: FastAPI, Python 3.11, Pydantic, MQTT (paho-mqtt), ffmpeg-python.
Containerization: Docker, Docker Compose.
Database/Storage: File-based (markdown in /mnt/sync/disaffected/episodes/).
Integration: Obsidian and other markdown-based systems for markdown management.

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
│   │   │   ├── HelloWorld.vue
│   │   │   ├── RundownManager.vue
│   │   │   └── RundownManagerBACKUP.vue
│   │   ├── router/       # Routing configuration
│   │   │   └── index.js
│   │   ├── views/        # View components (currently empty)
│   │   ├── App.vue       # Root component
│   │   └── main.js       # Vue app entry point
│   ├── babel.config.js   # Babel configuration
│   ├── jsconfig.js       # JavaScript configuration
│   ├── package.json      # Node.js package configuration
│   ├── README.md         # Frontend-specific documentation
│   ├── rundown-order-flow.md  # Rundown reordering workflow documentation
│   └── vue.config.js     # Vue build configuration
├── tools/                # Additional utility scripts or tools
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

Navigate to http://192.168.51.210:8080/rundown-manager/0225 to manage episode 0225.
Use the episode selector to switch episodes (e.g., 0226, 0227).
Drag and drop segments to reorder, then click “Save & Commit” to persist changes.
View segment metadata (title, ID, length) and colors based on segment type.


🌈 Features

Drag-and-Drop Reordering: Reorder segments with vuedraggable.
Episode Management: Select and load different episode rundowns.
API Endpoints: 
GET /rundown/{episode}: Fetch segment metadata.
POST /rundown/{episode}/reorder: Update segment order in markdown.
POST /proc_vid: Upload and process video files.
POST /publish/, GET /listen/: MQTT messaging.


Obsidian Integration: Markdown files updated with order: field.


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

