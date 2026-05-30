# Show-Build Project Status: Universal Functional Design Pattern Analysis

**Date**: September 30, 2025
**Analysis Type**: Current State Assessment via UFDP
**Project**: Show-Build - Broadcast Rundown Management System

---

## 1. FUNCTIONAL IDENTITY

### Core Purpose
Show-Build is a **database-driven broadcast rundown management system** designed for the Disaffected media ecosystem. It serves as a comprehensive production tool for creating, editing, and managing television episode rundowns with integrated asset management and script compilation capabilities.

### Primary Functions
- **Rundown Management**: Create, edit, and organize broadcast episode content
- **Content Editor**: Rich-text editing with YAML frontmatter integration
- **Asset Management**: Handle media files, graphics, and audio elements
- **Script Compilation**: Generate production-ready scripts from rundown data
- **Authentication**: JWT-based user management with RBAC system

---

## 2. SYSTEM ARCHITECTURE

### Technology Stack
- **Frontend**: Vue 3 + Vuetify 3 (Composition API)
- **Backend**: FastAPI + Python
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens + API key fallback
- **Background Processing**: Celery + Redis
- **File Storage**: Docker volume mounts
- **Development**: Docker Compose orchestration

### Data Flow Architecture
**🗄️ DATABASE-FIRST SYSTEM** *(Critical Discovery)*:
```
Frontend (Vue 3)
    ↓ HTTP/API calls
Episodes Router (/api/episodes/{episode}/rundown)
    ↓ SQLAlchemy ORM
PostgreSQL Database (rundown_items table)
    ↓ script_content field
Content Editor Components
    ↓ Media references
Filesystem Assets (/mnt/sync/disaffected/episodes/{episode}/assets/)
```

**Key Insight**: The system is **100% database-driven for content**. Markdown files in `rundown/` directories are reserved for future mirroring but not yet implemented. Media assets (images, video, audio) ARE actively stored in episode `assets/` directories.

---

## 3. CURRENT OPERATIONAL STATUS

### ✅ Working Components

#### Authentication System
- **JWT-based authentication**: Functional
- **RBAC (Role-Based Access Control)**: 11-table system implemented
- **API key fallback**: Available for service-to-service auth
- **User management**: Complete with 5 hierarchical roles

#### Database Layer
- **PostgreSQL**: Running in Docker container
- **Models**: Comprehensive v2 models (`models_v2.py`)
- **Migrations**: Alembic system functional
- **Test Data Management**: `is_test_data` flags implemented

#### Frontend Framework
- **Vue 3 + Vuetify**: Core framework operational
- **Content Editor**: Multi-panel interface working
- **Rundown Panel**: Drag-and-drop functionality
- **Asset Integration**: Upload and processing capabilities

#### API Endpoints
- **Episodes API**: Database-driven endpoints functional
- **Asset Management**: File processing and storage
- **Authentication**: Login/register/profile management
- **RBAC**: Permission management system

### 🚨 Critical Issues Identified

#### YAML Frontmatter Generation Bug
**Status**: ACTIVE BUG - Malformed frontmatter generation
**Root Cause**: Corrupted metadata processing in Vue components
**Symptoms**:
```yaml
---
id: 'SEGMG2BVX15C41J3P'
slug:  Karens in Nature    # Missing quotes, formatting issues
type: segment
order: 50
---
link:                      # Extra fields after closing
---                        # Multiple closing blocks
```

**Investigation**: Enhanced debugging added to `generateCurrentFrontmatter()` in EditorPanel.vue

#### Database Metadata Consistency Issues
**Status**: DATA INTEGRITY PROBLEM
**Scope**: Database-only (filesystem markdown not in use)
**Evidence**: Episode 0243 shows different data in database vs expected metadata
**Impact**: Content editor receives inconsistent metadata causing frontmatter corruption in `script_content` field
**Note**: This is a database corruption issue, not a file sync issue (files not actively used)

### ⚠️ Stability Concerns

#### Development Environment
- **Hot Module Reload**: Working but requires monitoring
- **SSL Certificates**: Self-signed causing browser warnings
- **Docker Compose**: Functional but complex networking setup

#### Data Consistency
- **Database vs Files**: Legacy file-based endpoints exist but unused
- **Migration State**: Some tables may have orphaned/test data
- **AssetID System**: Multiple AssetID generation systems present

---

## 4. TECHNICAL DEBT

### Code Quality Issues
- **Duplicate API Endpoints**: File-based endpoints in `main.py` superseded by database endpoints in `episodes_router.py`
- **Legacy Components**: Backup files and unused code present
- **Mixed Data Patterns**: Both file-first and database-first patterns coexist

### Architecture Inconsistencies
- **Asset ID Management**: Multiple systems (`assetid_router.py`, `new_assetid_router.py`, `convert_assetid_router.py`)
- **Model Versioning**: Both `models.py` (deleted) and `models_v2.py` patterns
- **Router Proliferation**: 15+ routers with overlapping functionality

### Documentation Gaps
- **API Documentation**: Present but may not reflect current endpoints
- **Database Schema**: Complex relationships not fully documented
- **Frontend Components**: Vue template ref conflicts documented but widespread

---

## 5. SECURITY STATUS

### ✅ Implemented Security
- **JWT Authentication**: Proper token management
- **RBAC System**: Granular permission control
- **API Key Management**: Secure service authentication
- **Input Validation**: Pydantic models for API validation

### ⚠️ Security Considerations
- **Development Mode**: Debug information exposed
- **Self-Signed Certificates**: Not production-ready
- **Test Data**: Mixed with production data (marked with `is_test_data` flags)

---

## 6. DEPLOYMENT STATUS

### Current Environment
- **Development**: Docker Compose running locally
- **Database**: PostgreSQL in container with persistent volumes
- **Frontend**: Vue dev server with hot reload
- **Backend**: FastAPI with auto-reload
- **Services**: All services operational

### Production Readiness
- **Status**: NOT PRODUCTION READY
- **Blockers**:
  - SSL certificate configuration needed
  - Environment variable security required
  - Database migration strategy needed
  - Performance optimization required

---

## 7. IMMEDIATE PRIORITIES

### 🔥 Critical (Fix Immediately)
1. **YAML Frontmatter Bug**: Resolve malformed frontmatter generation
2. **Data Consistency**: Synchronize database content with expected data
3. **Database Cleanup**: Remove test/orphaned data from production tables

### 🚨 High Priority (This Week)
1. **Error Handling**: Improve frontend error handling and user feedback
2. **Performance**: Optimize database queries and frontend rendering
3. **Documentation**: Update API documentation to reflect current endpoints

### 📋 Medium Priority (This Month)
1. **Code Cleanup**: Remove duplicate/legacy code
2. **Testing**: Implement comprehensive test suite
3. **Security**: Production-ready authentication configuration

---

## 8. TECHNICAL RECOMMENDATIONS

### Immediate Actions
1. **Fix YAML Generation**: Complete the debugging of `generateCurrentFrontmatter()` function
2. **Database Audit**: Verify data integrity across all tables
3. **Router Consolidation**: Merge duplicate API functionality

### Architecture Improvements
1. **Single Source of Truth**: Ensure database-first pattern is consistently applied
2. **Asset Management**: Consolidate AssetID systems into single coherent approach
3. **Error Boundaries**: Implement comprehensive error handling

### Development Workflow
1. **Testing Strategy**: Unit tests for Vue components and API endpoints
2. **CI/CD Pipeline**: Automated testing and deployment
3. **Monitoring**: Application performance and error tracking

---

## 9. KNOWN WORKING FEATURES

### Content Management
- ✅ Episode creation and editing
- ✅ Rundown item management
- ✅ Drag-and-drop reordering
- ✅ Content editor with multiple panels
- ✅ Asset upload and processing

### System Administration
- ✅ User authentication and authorization
- ✅ RBAC permission management
- ✅ Organization and show management
- ✅ Settings configuration

### Integration
- ✅ MQTT messaging for background processing
- ✅ Celery task management
- ✅ WebSocket real-time updates
- ✅ API key authentication for services
- ✅ Ollama LLM integration (local AI services)

### AI Services Configuration

#### Ollama (Local LLM Server)
**Status**: ✅ Configured and operational (as of October 6, 2025)

**Critical Configuration Details**:
- **Correct Host**: `http://192.168.51.197:11434` ✅
- **Incorrect Host**: `http://192.168.51.223:11434` ❌ (returns connection refused)
- **Default Model**: `llama3.2`

**Available Models on 192.168.51.197**:
- `deepseek-r1:8b` - DeepSeek reasoning model
- `llama3:latest` - Meta's Llama 3
- `mistral:7b` - Mistral 7B base model
- `mistral-large:latest` - Mistral Large
- `wizardlm-uncensored:13b` - Uncensored WizardLM
- `Qwen2.5-Coder:7b` - Qwen 2.5 coding model (7B)
- `Qwen2.5-Coder:32b` - Qwen 2.5 coding model (32B)
- `codellama:34b` - Meta's CodeLlama 34B

**Database Storage**:
```sql
-- Ollama config stored in api_configs table
SELECT service, config_key, config_value, is_enabled
FROM api_configs
WHERE service = 'ollama';

-- Expected output:
-- service | config_key | config_value                  | is_enabled
-- ollama  | host       | http://192.168.51.197:11434  | t
-- ollama  | model      | llama3.2                     | t
-- ollama  | enabled    | true                         | t
```

**Health Check Integration**:
- Ollama status appears in `/health` endpoint
- Frontend status indicator shows connection state
- Queries database for configuration (not file-based)
- Tests connectivity via `/api/tags` endpoint

**Quick Verification**:
```bash
# Test Ollama server directly
curl -s http://192.168.51.197:11434/api/tags

# Check Show-Build health status
curl -s http://192.168.51.210:8888/health | jq '.services.ollama'
```

**UI Access**:
- Settings → API Access → Local AI Access
- Status Grid Overlay shows Ollama connection state

---

## 10. DEVELOPMENT NOTES

### Recent Changes
- **Enhanced YAML Validation**: Added comprehensive malformed frontmatter detection
- **Debugging Implementation**: Added extensive logging to identify corruption sources
- **Slug Formatting Fix**: Corrected quote formatting in frontmatter generation
- **Double Frontmatter Prevention**: Implemented safeguards against content duplication

### Active Investigation
- **Root Cause Analysis**: YAML frontmatter corruption source identification
- **Data Flow Mapping**: Complete understanding of database-driven architecture
- **Performance Monitoring**: Frontend compilation and hot reload optimization

---

## CONCLUSION

Show-Build is a **sophisticated, database-driven broadcast management system** that is functionally operational but requires critical bug fixes and data consistency improvements before production deployment. The core architecture is sound, but technical debt and data integrity issues need immediate attention.

**Current Status**: 🟡 **DEVELOPMENT ACTIVE - CRITICAL ISSUES IDENTIFIED**
**Production Readiness**: 🔴 **NOT READY - REQUIRES SIGNIFICANT FIXES**
**Next Steps**: Focus on YAML frontmatter bug resolution and database cleanup.

---

*This analysis follows the Universal Functional Design Pattern to provide comprehensive system understanding and actionable recommendations.*