# Show-Build Development TODO

## Current Sprint: Segment-Centric Architecture

### ✅ Completed
- [x] Create Production Hierarchy Documentation
- [x] Design new database schema with segment-centric models
- [x] Build AssetID service for universal ID generation

### 🔄 In Progress
- [ ] Create segment management system with drag & drop
- [ ] Replace markdown cue blocks with database entities
- [ ] Build RESTful API endpoints for segment operations
- [ ] Update Vue 3 interface for segment-focused editing

### 🆕 Recently Added
- [ ] Add Requirements Extraction & Clean Implementation tool to frontend Tools section
- [ ] Implement Requirements Extraction function-by-function approach  
- [ ] Create accessible Tools location on frontend for Requirements Extraction

### 📋 Backlog
- [ ] Implement segment publishing workflows
- [ ] Create production marker system for auto-cutting
- [ ] Build role-specific script generation
- [ ] Implement timing and backtiming calculations
- [ ] Create WebSocket real-time updates for production

---

## Open Architectural Questions

### 1. Block Modeling
**Question**: Should blocks be separate database entities or metadata tags on segments?

**Considerations**:
- Separate entities allow for block-level timing and advertising metadata
- Tags are simpler but less flexible for complex block operations
- Blocks need to track commercial value and sponsor information

**Decision**: _Pending discussion_

### 2. Dynamic Advertiser Constraints
**Question**: How to implement dynamic rules for advertiser placement?

**Example**: "Advertiser X doesn't want to be adjacent to segments about topic Y"

**Options**:
- Rule engine with JSON-based constraint definitions
- Tag-based matching system
- Manual override capabilities

**Decision**: _Pending discussion_

### 3. Non-Media Cue Sequencing
**Question**: How should non-media cues (camera switches, mic control) integrate with media cues?

**Considerations**:
- All cues share timeline but have different execution requirements
- Some cues are dependent on others
- Live production needs real-time cue triggering

**Decision**: _Pending discussion_

### 4. Real-Time Dashboard Architecture
**Question**: What architecture for real-time production dashboard?

**Important**: Big conversation needed before implementation!

**Topics to discuss**:
- WebSocket vs Server-Sent Events vs polling
- What data needs real-time updates
- Performance implications
- Client state management
- Scalability concerns

**Decision**: _Hold for detailed discussion_

### 5. Multi-Role Script Templates
**Question**: How to generate role-specific scripts from same content?

**Roles**:
- Host (teleprompter content)
- Director (camera cues, timing)
- Technical (audio/video cues)
- Camera operators (shot lists)

**Options**:
- Template system with role-based filters
- Separate script entities per role
- Dynamic generation from segment data

**Decision**: _Pending discussion_

### 6. Segment Version Control
**Question**: Do segments need version control for re-editing/re-packaging?

**Use cases**:
- Re-cutting segment for different platform
- Updating segment after initial broadcast
- A/B testing different versions

**Complexity**: May be overkill for current needs

**Decision**: _Pending - probably not needed initially_

---

## Technical Debt & Improvements

### Backend
- [ ] Migrate from file-based to database-first storage
- [ ] Remove markdown parsing complexity
- [ ] Consolidate duplicate endpoints (legacy vs modern)
- [ ] Implement proper database migrations with Alembic
- [ ] Add comprehensive API documentation (OpenAPI/Swagger)

### Frontend
- [ ] Dockerize Vue frontend
- [ ] Implement segment drag & drop interface
- [ ] Create role-based script views
- [ ] Build timing dashboard (after architecture discussion)
- [ ] Add production marker UI

### Infrastructure
- [ ] Set up development vs production configurations
- [ ] Implement proper logging and monitoring
- [ ] Add automated testing suite
- [ ] Create backup and restore procedures
- [ ] Document deployment process

---

## Future Features (Post-MVP)

### Production Features
- [ ] Live production cue execution tracking
- [ ] Auto-cutting from production markers
- [ ] AI-based speech timing (words per minute)
- [ ] Multi-camera coordination system

### Content Distribution
- [ ] Social media auto-publishing
- [ ] YouTube clip generation
- [ ] Podcast feed generation
- [ ] Transcription integration

### Advanced Capabilities
- [ ] AI information gathering
- [ ] Media transcoding pipeline
- [ ] Intelligence gathering system
- [ ] Advanced analytics dashboard

---

## Notes

### Design Principles
1. **Segment-centric**: Segments are portable value units
2. **Episode as flagship**: Episodes organize broadcasts
3. **AssetID everything**: Universal identification system
4. **Database-first**: No markdown parsing in new system
5. **Role-based**: Different views for different production roles

### Current Status
- Working on `dev-fork` branch
- Keeping Vue 3 + Vuetify + TypeScript frontend
- Keeping FastAPI backend
- PostgreSQL for data storage
- Redis for queuing/real-time

### Important Reminders
- Frontend is NOT dockerized (runs on host)
- Backend services ARE dockerized
- Markdown/file system being phased out
- Focus on segment portability and publishing

---

*Last Updated: 2025-08-10*
*Active Branch: dev-fork*