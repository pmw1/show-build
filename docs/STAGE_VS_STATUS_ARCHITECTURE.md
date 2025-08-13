# Stage vs Status Architecture

This document outlines an important architectural distinction that needs to be addressed in the Show-Build system.

## The Problem

The current codebase mixes two different concepts under the umbrella of "production status":

1. **Workflow Stages** - The phase of production workflow
2. **Production Status** - The completion state within any given stage

This mixing causes confusion in the UI, color coding system, and data management.

## Conceptual Distinction

### Workflow Stages (Sequential Production Phases)
These represent **where** in the overall production workflow an episode currently is:
- **Pre-Production**: Planning, scripting, guest booking, content development
- **Production**: Active recording, filming, live broadcast
- **Post-Production**: Editing, graphics, final assembly, publishing

### Production Status (Completion States)
These represent **how complete** the work is within any given stage:
- **Draft**: Initial work, not ready for review
- **Approved**: Work reviewed and approved, ready for next step
- **Production**: Active work in progress 
- **Completed**: Work finished and ready for next stage/delivery

## Current Implementation Issues

### Mixed Terminology in Code
The codebase currently has inconsistent usage:

**Old System** (found in composables):
- `'Pre-Production'`, `'In Production'`, `'Post-Production'` (stages)
- Used in `useContentEditor.js` and `useEditorUtils.js`

**New System** (used in ContentEditor):
- `'draft'`, `'approved'`, `'production'`, `'completed'` (statuses)
- Used in `ContentEditor.vue` and status coloring system

### Impact on User Interface
- Status dropdown shows mixed stage/status values
- Color coding system expects status values but sometimes receives stage values
- User confusion about what field controls what behavior

## Proper Architecture (Future State)

### Data Model
Each episode should have **both** fields:
```javascript
{
  productionStage: 'pre-production' | 'production' | 'post-production',
  productionStatus: 'draft' | 'approved' | 'production' | 'completed'
}
```

### UI Components
- **Stage Field**: Shows workflow phase (Pre-Production, Production, Post-Production)
- **Status Field**: Shows completion state (Draft, Approved, Production, Completed)
- **Status Bar Coloring**: Based on production status only

### Color Coding
Status colors should map to completion states:
- `draft` → Grey (work not started/incomplete)
- `approved` → Green (work reviewed and approved)  
- `production` → Blue (work actively in progress)
- `completed` → Yellow (work finished)

## Current Workaround

**Note: The user has not decided how to proceed with this architectural change and wants to think through the approach carefully to avoid further problems.**

For now, the system focuses only on production status (draft/approved/production/completed) for UI display and coloring, while the larger stage vs status separation remains unimplemented.

## Files Affected

### Need Architecture Changes (Future)
- `src/composables/useContentEditor.js` - Mixed stage/status references
- `src/composables/useEditorUtils.js` - Old stage-based status array
- API endpoints and database schema - Need both stage and status fields
- All episode data models

### Current Status System (Working)
- `src/components/ContentEditor.vue` - Uses proper status system
- `src/components/content-editor/ShowInfoHeader.vue` - Status display and coloring
- `src/utils/themeColorMap.js` - Status color definitions

## Recommendations

1. **Phase 1**: Document the issue (this document) and fix immediate coloring problems
2. **Phase 2**: Plan the full architecture change carefully
3. **Phase 3**: Implement dual stage/status system with proper data migration
4. **Phase 4**: Update all UI components to use both fields appropriately

## Status

- **Current**: Mixed system causing coloring issues
- **Immediate Fix**: Focus on production status only, ignore stage references
- **Long-term**: Full architectural separation (timeline TBD)

---
*Document created: 2025-01-13*
*Status: Architecture planning phase*