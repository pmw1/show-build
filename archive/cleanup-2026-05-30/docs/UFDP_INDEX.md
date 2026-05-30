# Show-Build UFDP Documentation Index

> **📖 About This Index**
>
> This is the **master index** for all UFDP (Unified Feature Documentation Protocol) documents in the Show-Build project. Each document provides comprehensive technical documentation for a specific system, feature, or workflow.
>
> **UFDP Format**: All documents follow a standardized structure with:
> - Human-friendly introduction
> - Hierarchical section numbering (1.1, 1.2, 2.1, etc.)
> - Table of contents with anchor links
> - Detailed architecture diagrams
> - Step-by-step procedures
> - Troubleshooting guides
> - Code examples and API references

---

## 📚 Core Infrastructure Documentation

### [NFS_INFRASTRUCTURE_UFDP.md](NFS_INFRASTRUCTURE_UFDP.md)
**Network File System for Distributed Storage**

**Topics Covered:**
- NFS server setup on whisper (central storage server)
- NFS client configuration on workers (kairo, proxima)
- Docker integration for seamless volume mounting
- Security configuration and access control
- Performance tuning for video processing workloads
- Health monitoring and diagnostics
- Troubleshooting stale mounts, permission issues

**When to Read:**
- Setting up new worker machines
- Debugging "file not found" errors in distributed tasks
- Performance tuning for large file operations
- Understanding shared storage architecture

**Key Sections:**
- Section 2: Architecture diagrams showing NFS data flow
- Section 3: Installation commands (requires sudo access)
- Section 5: Docker volume mount configuration
- Section 7: Comprehensive troubleshooting guide

---

## 🎬 Media Processing Documentation

### [MEDIA_PROCESSING_WORKFLOW_UFDP.md](MEDIA_PROCESSING_WORKFLOW_UFDP.md)
**Complete Video/Audio Processing Workflow**

**Topics Covered:**
- End-to-end SOT (Sound on Tape) processing example
- Preprocessing steps (upload, validation, staging)
- Distributed task execution via Celery workers
- Postprocessing steps (result delivery, database updates)
- Development guide for adding new processing tasks
- Performance optimization (FFmpeg, NFS, Celery)
- Troubleshooting failed tasks and worker issues

**When to Read:**
- Understanding how video uploads are processed
- Adding new media processing capabilities
- Debugging stuck or failed processing tasks
- Optimizing processing performance

**Key Sections:**
- Section 2: Complete workflow with detailed step-by-step breakdown
- Section 3: Preprocessing (upload → shared storage)
- Section 4: Postprocessing (results → user notification)
- Section 5: Developer guide for creating new tasks
- Section 8: Performance tuning for FFmpeg and workers

---

## 🔄 Distributed Processing Documentation

### [SOT_DISTRIBUTED_PROCESSING_UFDP.md](SOT_DISTRIBUTED_PROCESSING_UFDP.md)
**Celery + Redis Task Queue System**

**Topics Covered:**
- Distributed architecture overview (whisper → farmhouse → kairo)
- Redis message broker setup on farmhouse
- Celery worker deployment to remote machines
- Task queuing and routing strategies
- Worker health monitoring
- UI deployment interface in Settings > System > Deployments
- Automated worker deployment via bash script
- API endpoints for worker management

**When to Read:**
- Deploying new Celery workers
- Understanding Redis/Celery architecture
- Adding new task queues (media, compilation, quotes)
- Monitoring worker health and performance
- Using deployment UI to manage workers

**Key Sections:**
- Section 2: Architecture with network diagrams
- Section 4: Deployment procedures (manual and automated)
- Section 6: API reference for worker management
- Section 9: Troubleshooting worker connectivity

---

## 🎨 UI and Frontend Documentation

### [SCRIPT_MODE_AS_VIEWER_ARCHITECTURE_UFDP.md](SCRIPT_MODE_AS_VIEWER_ARCHITECTURE_UFDP.md)
**ContentEditor.vue Script Mode Rendering**

**Topics Covered:**
- Script mode rendering architecture
- Paragraph height and text wrapping
- View-only mode design philosophy
- Text measurement and layout algorithms
- Performance considerations for large scripts

**When to Read:**
- Working on ContentEditor.vue script mode
- Debugging text rendering issues
- Understanding view-only design decisions

---

### [FSQ_NESTED_QUOTE_PROCESSING_UFDP.md](FSQ_NESTED_QUOTE_PROCESSING_UFDP.md)
**Full Screen Quote Processing System**

**Topics Covered:**
- FSQ asset generation workflow
- Nested quote extraction from markdown
- Image rendering and PDF generation
- Auto-asset generation triggers
- Database integration for FSQ items

**When to Read:**
- Working on FSQ modal or quote processing
- Understanding quote extraction logic
- Debugging FSQ asset generation

---

### [IMG_CUE_INSERTION_WORKFLOW_UFDP.md](IMG_CUE_INSERTION_WORKFLOW_UFDP.md)
**Image Cue Insertion in Script Content**

**Topics Covered:**
- IMG cue syntax and parsing
- Insertion workflow in ContentEditor
- Asset linking and database storage
- Rendering in script view

**When to Read:**
- Adding image insertion features
- Understanding cue syntax
- Debugging image display in scripts

---

### [MEDIA_ASSET_VERSIONING_UFDP.md](MEDIA_ASSET_VERSIONING_UFDP.md)
**Asset Versioning and History Tracking**

**Topics Covered:**
- Asset version management
- History tracking for media files
- Rollback functionality
- Database schema for versions

**When to Read:**
- Implementing asset versioning
- Understanding version history
- Working on rollback features

---

## 🔧 System Configuration Documentation

### [SHOW_BUILD_STATUS_UFDP.md](SHOW_BUILD_STATUS_UFDP.md)
**System Health Status Indicators**

**Topics Covered:**
- Status grid overlay architecture
- Health check endpoints
- Service monitoring (database, Redis, Celery, Ollama, XTTS)
- Real-time status updates

**When to Read:**
- Adding new status indicators
- Understanding health check system
- Debugging service connectivity

---

### [XTTS_STATUS_MONITORING_UFDP.md](XTTS_STATUS_MONITORING_UFDP.md)
**XTTS Voice Synthesis Monitoring**

**Topics Covered:**
- XTTS service integration
- Status monitoring and quota tracking
- Health checks and error handling

**When to Read:**
- Working with XTTS voice synthesis
- Monitoring XTTS service health
- Debugging voice generation issues

---

## 📊 Data Management Documentation

### [RUNDOWN_AUTO_SCAFFOLD_BEHAVIOR.md](RUNDOWN_AUTO_SCAFFOLD_BEHAVIOR.md)
**Automatic Rundown Scaffolding**

**Topics Covered:**
- Auto-scaffold behavior on episode creation
- Rundown structure generation
- Database initialization

**When to Read:**
- Understanding episode initialization
- Modifying auto-scaffold behavior

---

### [SCRIPT_MODE_PARAGRAPH_RESIZE_UDFP.md](SCRIPT_MODE_PARAGRAPH_RESIZE_UDFP.md)
**Paragraph Height and Resizing Logic**

**Topics Covered:**
- Text measurement algorithms
- Dynamic height calculation
- Performance optimization

**When to Read:**
- Debugging text layout issues
- Optimizing script rendering

---

## 🗄️ Database and Backend Documentation

### [DATABASE_SETUP_INSTRUCTIONS.md](docs/DATABASE_SETUP_INSTRUCTIONS.md)
**PostgreSQL Database Setup**

**Topics Covered:**
- Database installation and configuration
- Schema creation and migrations
- User management and permissions

**When to Read:**
- Initial database setup
- Understanding database schema
- Running migrations

---

### [RBAC_AUTHENTICATION_GUIDE.md](docs/RBAC_AUTHENTICATION_GUIDE.md)
**Role-Based Access Control System**

**Topics Covered:**
- RBAC architecture and models
- Permission system design
- User roles and groups
- API key authentication
- Audit logging

**When to Read:**
- Implementing permission checks
- Adding new roles or permissions
- Understanding authentication flow

---

### [ASSETID_SYSTEM_GUIDE.md](docs/ASSETID_SYSTEM_GUIDE.md)
**Asset ID Generation and Tracking**

**Topics Covered:**
- Asset ID format and structure
- Generation algorithms
- Database registry
- Scanning and validation tools

**When to Read:**
- Working with asset tracking
- Understanding asset ID format
- Debugging asset links

---

### [API_ENDPOINTS.md](docs/API_ENDPOINTS.md)
**REST API Endpoint Reference**

**Topics Covered:**
- Complete API endpoint listing
- Request/response formats
- Authentication requirements
- Usage examples

**When to Read:**
- Integrating with Show-Build API
- Understanding endpoint behavior
- Building API clients

---

## 🔍 Debugging and Standards Documentation

### [DEBUG_FIRST.md](DEBUG_FIRST.md)
**Priority Debugging Checklist** ⚠️ **READ THIS FIRST FOR ANY ISSUE**

**Topics Covered:**
- Quick debug command (`./scripts/debug-frontend.sh`)
- Common issue patterns
- Template ref naming conflicts
- API connectivity checks
- Vue mounting problems

**When to Read:**
- **ANY unexplained frontend issue** (run debug script immediately)
- Form resets or reactivity breaks
- Component mounting failures
- Before deep debugging (saves 10+ minutes)

---

### [DEBUGGING_STANDARDS.md](docs/DEBUGGING_STANDARDS.md)
**Systematic Debugging Methodology**

**Topics Covered:**
- Debugging checklist and workflow
- Log analysis techniques
- Common Vue.js pitfalls
- Network debugging tools

**When to Read:**
- Establishing debugging practices
- Training new developers
- Systematic issue investigation

---

### [VUE_TEMPLATE_REF_CONFLICTS.md](docs/VUE_TEMPLATE_REF_CONFLICTS.md)
**Template Ref Naming Conflicts** ⚠️ **CRITICAL - 80% of Vue Issues**

**Topics Covered:**
- Template ref vs reactive variable conflicts
- Naming conventions (use `Ref` suffix)
- Conflict detection commands
- Prevention strategies

**When to Read:**
- Form values mysteriously reset
- Reactivity breaks without obvious cause
- Data appears then disappears
- Before creating new Vue components (prevention)

---

### [DUPLICATE_COMPONENT_FILES.md](docs/DUPLICATE_COMPONENT_FILES.md)
**Duplicate Component Detection**

**Topics Covered:**
- Identifying duplicate components
- Resolution strategies
- Cleanup procedures

**When to Read:**
- Unexpected component behavior
- Build conflicts
- Code organization cleanup

---

## 🛠️ Tools and Scripts Documentation

### [TOOLS_DOCUMENTATION.md](docs/TOOLS_DOCUMENTATION.md)
**Command-Line Tool Reference**

**Topics Covered:**
- Episode management tools
- Asset ID generators and scanners
- Media processing utilities
- Database migration helpers

**When to Read:**
- Using Show-Build CLI tools
- Automating workflows
- Bulk operations on episodes

---

### [TEST_DATA_MANAGEMENT.md](docs/TEST_DATA_MANAGEMENT.md)
**Test Data Flagging and Cleanup**

**Topics Covered:**
- `is_test_data` flag usage
- Test episode numbering (900X)
- Bulk cleanup queries
- API filtering

**When to Read:**
- Creating test data
- Cleaning up after testing
- Separating test from production

---

## 📝 Episode Production Documentation

### [EPISODE_PRODUCTION_WORKFLOW.md](docs/EPISODE_PRODUCTION_WORKFLOW.md)
**Complete Episode Production Lifecycle**

**Topics Covered:**
- Episode creation and scaffolding
- Rundown building workflow
- Script compilation
- Asset management
- Final delivery

**When to Read:**
- Understanding production workflow
- Training new producers
- Workflow optimization

---

### [EPISODE_DELETION_STRATEGY.md](EPISODE_DELETION_STRATEGY.md)
**Safe Episode Deletion Procedures**

**Topics Covered:**
- Cascade deletion behavior
- Backup procedures
- Soft delete vs hard delete
- Recovery options

**When to Read:**
- Before deleting episodes
- Implementing deletion features
- Data retention policies

---

## 🏗️ Architecture and Planning Documentation

### [ARCHITECTURAL_ANALYSIS.md](ARCHITECTURAL_ANALYSIS.md)
**System Architecture Overview**

**Topics Covered:**
- High-level system design
- Component relationships
- Technology stack decisions
- Scalability considerations

**When to Read:**
- Onboarding new developers
- Planning major features
- Architecture refactoring

---

### [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md)
**Feature Implementation Notes**

**Topics Covered:**
- Implementation decisions and rationale
- Technical debt tracking
- Future enhancement ideas

**When to Read:**
- Understanding "why" behind implementations
- Planning refactoring
- Historical context

---

## 📋 Quick Reference

### By Use Case

**🚀 Getting Started:**
1. [DATABASE_SETUP_INSTRUCTIONS.md](docs/DATABASE_SETUP_INSTRUCTIONS.md) - Set up database
2. [NFS_INFRASTRUCTURE_UFDP.md](NFS_INFRASTRUCTURE_UFDP.md) - Set up shared storage
3. [SOT_DISTRIBUTED_PROCESSING_UFDP.md](SOT_DISTRIBUTED_PROCESSING_UFDP.md) - Deploy workers
4. [RBAC_AUTHENTICATION_GUIDE.md](docs/RBAC_AUTHENTICATION_GUIDE.md) - Configure authentication

**🐛 Debugging Issues:**
1. [DEBUG_FIRST.md](DEBUG_FIRST.md) - **START HERE** (run `./scripts/debug-frontend.sh`)
2. [VUE_TEMPLATE_REF_CONFLICTS.md](docs/VUE_TEMPLATE_REF_CONFLICTS.md) - If form resets/reactivity breaks
3. [DEBUGGING_STANDARDS.md](docs/DEBUGGING_STANDARDS.md) - Systematic approach
4. [NFS_INFRASTRUCTURE_UFDP.md](NFS_INFRASTRUCTURE_UFDP.md) Section 7 - File access issues
5. [MEDIA_PROCESSING_WORKFLOW_UFDP.md](MEDIA_PROCESSING_WORKFLOW_UFDP.md) Section 7 - Task failures

**🎬 Adding Media Features:**
1. [MEDIA_PROCESSING_WORKFLOW_UFDP.md](MEDIA_PROCESSING_WORKFLOW_UFDP.md) Section 5 - Development guide
2. [SOT_DISTRIBUTED_PROCESSING_UFDP.md](SOT_DISTRIBUTED_PROCESSING_UFDP.md) Section 6 - API integration
3. [ASSETID_SYSTEM_GUIDE.md](docs/ASSETID_SYSTEM_GUIDE.md) - Asset tracking

**⚙️ System Administration:**
1. [NFS_INFRASTRUCTURE_UFDP.md](NFS_INFRASTRUCTURE_UFDP.md) - Storage management
2. [SOT_DISTRIBUTED_PROCESSING_UFDP.md](SOT_DISTRIBUTED_PROCESSING_UFDP.md) - Worker deployment
3. [SHOW_BUILD_STATUS_UFDP.md](SHOW_BUILD_STATUS_UFDP.md) - Health monitoring
4. [TEST_DATA_MANAGEMENT.md](docs/TEST_DATA_MANAGEMENT.md) - Data cleanup

**📚 Development Reference:**
1. [API_ENDPOINTS.md](docs/API_ENDPOINTS.md) - API reference
2. [TOOLS_DOCUMENTATION.md](docs/TOOLS_DOCUMENTATION.md) - CLI tools
3. [EPISODE_PRODUCTION_WORKFLOW.md](docs/EPISODE_PRODUCTION_WORKFLOW.md) - Workflow patterns

---

## 🔗 Cross-References

### Infrastructure Stack
- Storage: [NFS_INFRASTRUCTURE_UFDP.md](NFS_INFRASTRUCTURE_UFDP.md)
- Task Queue: [SOT_DISTRIBUTED_PROCESSING_UFDP.md](SOT_DISTRIBUTED_PROCESSING_UFDP.md)
- Database: [DATABASE_SETUP_INSTRUCTIONS.md](docs/DATABASE_SETUP_INSTRUCTIONS.md)
- Auth: [RBAC_AUTHENTICATION_GUIDE.md](docs/RBAC_AUTHENTICATION_GUIDE.md)

### Media Pipeline
- Upload → [MEDIA_PROCESSING_WORKFLOW_UFDP.md](MEDIA_PROCESSING_WORKFLOW_UFDP.md) Section 3
- Processing → [MEDIA_PROCESSING_WORKFLOW_UFDP.md](MEDIA_PROCESSING_WORKFLOW_UFDP.md) Section 2
- Delivery → [MEDIA_PROCESSING_WORKFLOW_UFDP.md](MEDIA_PROCESSING_WORKFLOW_UFDP.md) Section 4
- Asset Tracking → [ASSETID_SYSTEM_GUIDE.md](docs/ASSETID_SYSTEM_GUIDE.md)

### Frontend Development
- Debugging → [DEBUG_FIRST.md](DEBUG_FIRST.md) + [VUE_TEMPLATE_REF_CONFLICTS.md](docs/VUE_TEMPLATE_REF_CONFLICTS.md)
- Component Standards → [DEBUGGING_STANDARDS.md](docs/DEBUGGING_STANDARDS.md)
- Script Editor → [SCRIPT_MODE_AS_VIEWER_ARCHITECTURE_UFDP.md](SCRIPT_MODE_AS_VIEWER_ARCHITECTURE_UFDP.md)

---

## 📖 Documentation Standards

All UFDP documents follow these conventions:

1. **Human-Friendly Introduction** - Clear explanation of what the document covers
2. **Table of Contents** - With anchor links to all major sections
3. **Hierarchical Numbering** - 1.1, 1.2, 2.1, etc. for easy reference
4. **Code Examples** - Actual working code, not pseudocode
5. **Diagrams** - ASCII art for architecture and data flow
6. **Troubleshooting** - Dedicated section with common issues
7. **Cross-References** - Links to related documents

---

## 🆕 Contributing New Documentation

When creating new UFDP documents:

1. **Copy the structure** from existing UFDP docs (see [NFS_INFRASTRUCTURE_UFDP.md](NFS_INFRASTRUCTURE_UFDP.md))
2. **Add human-friendly intro** at the top with quick navigation
3. **Create table of contents** with anchor links
4. **Use hierarchical numbering** (1.1, 1.2, 2.1, 2.2, etc.)
5. **Include diagrams** for architecture and workflows
6. **Add to this index** under appropriate category
7. **Cross-reference** related documents

---

**Last Updated:** 2025-01-06
**Total UFDP Documents:** 20+
**Quick Access:** All documents in `/mnt/process/show-build/*.md` and `/mnt/process/show-build/docs/*.md`
