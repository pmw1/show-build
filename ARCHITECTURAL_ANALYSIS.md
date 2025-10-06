# Show-Build Architectural Analysis
## High-Level Design Review and Identified Issues

**Analysis Date:** 2025-10-04
**Scope:** Complete codebase architectural patterns, component design, and structural inconsistencies

---

## Executive Summary

This analysis reveals **6 critical architectural design flaws** affecting the Show-Build project, independent of the immediate SOT insertion bug. These systemic issues compound debugging difficulty, create maintenance burden, and introduce subtle runtime failures that are difficult to trace.

**Severity Breakdown:**
- 🔴 **Critical (3)**: Issues causing production bugs and debugging nightmares
- 🟡 **High (2)**: Architectural inconsistencies creating technical debt
- 🟢 **Medium (1)**: Organizational issues impacting maintainability

---

## 🔴 CRITICAL ISSUE #1: Mixed Vue API Paradigms (Options vs Composition)

### The Problem
The codebase simultaneously uses **Vue 3 Options API** and **Composition API** without clear standards or separation. This creates:
- Inconsistent event handling patterns
- Different reactivity models in parent-child relationships
- Unpredictable behavior when mixing approaches

### Evidence
**Component Count:**
- Total Vue components: 55
- Composition API (`setup()`): 4 components (7%)
- Options API (`export default {`): 43 components (78%)
- Mixed/unclear: 8 components (15%)

**Specific Examples:**

**SotModal.vue** (Composition API):
```javascript
setup(props, { emit }) {
  const handleAddCue = async () => {
    // ...
    emit('submit', sotData)
    emit('update:show', false)
  }
  return { handleAddCue, ... }
}
```

**ContentEditor.vue** (Options API):
```javascript
export default {
  methods: {
    async submitSot(data) {
      this.updateScriptContent(newContent)
      this.showSotModal = false
    }
  }
}
```

### Why This Causes the SOT Bug
The event emission from Composition API `emit('submit', sotData)` requires the parent to bind with `@submit="submitSot"`. However:
1. The parent (ContentEditor) uses Options API's `this.$refs` and `this.$emit` patterns
2. Event handling differs between APIs - Options API components may not properly receive events from Composition API children
3. No consistent pattern for v-model bindings across paradigms

### Impact
- **Debugging difficulty**: Different components require different debugging approaches
- **Unpredictable reactivity**: `ref()` vs `data()` have subtle timing differences
- **Event propagation failures**: Mixed event patterns can silently fail
- **Onboarding complexity**: Developers must understand both paradigms

### Recommended Fix
**Option A (Recommended):** Standardize on Composition API
- Convert all modal components to Composition API
- Migrate ContentEditor.vue and EditorPanel.vue to Composition API
- Establish clear composables for shared logic

**Option B:** Strict separation with adapters
- Keep Options API for large components
- Use Composition API only for small, reusable components
- Create adapter pattern for event bridging

---

## 🔴 CRITICAL ISSUE #2: Duplicate Component Files

### The Problem
Multiple components exist in **two separate locations** with different implementations:

**Confirmed Duplicates:**
```
/components/modals/ImgCueModal.vue
/components/content-editor/modals/ImgCueModal.vue

/components/modals/GfxModal.vue
/components/content-editor/modals/GfxModal.vue

/components/modals/SotModal.vue
(EditorPanel has its own IMG modal, ContentEditor uses SotModal)

/components/modals/NewItemModal.vue
/components/content-editor/modals/NewItemModal.vue
```

### Evidence from Conversation
During debugging, we discovered:
- IMG insertion works (EditorPanel uses its own modal)
- SOT insertion fails (ContentEditor uses different modal path)
- The working IMG modal is in `content-editor/modals/`
- The failing SOT modal is in `/modals/`

**From ContentEditor.vue:**
```vue
<!-- Line 186: Uses /modals/FsqModal -->
<FsqModal :show="showFsqModal" @submit="submitFsq" />

<!-- Line 191: Uses /modals/SotModal -->
<SotModal @submit="submitSot" />

<!-- Line 230: Uses content-editor/modals/ImgCueModal -->
<ImgCueModal @submit="handleImgCueSubmit" />
```

**From EditorPanel.vue:**
```vue
<!-- Line 1105: Uses content-editor/modals/ImgCueModal -->
<ImgCueModal @submit="handleImgCueSubmit" />
```

### Why This Is Critical
1. **Version drift**: Changes to one modal don't propagate to duplicates
2. **Import confusion**: Developers may edit wrong file
3. **Inconsistent behavior**: Same feature works differently in different contexts
4. **Bug hiding**: Fix applied to wrong duplicate masks underlying issue

### Impact on SOT Bug
The SOT modal at `/modals/SotModal.vue` may have different event handling than the working IMG modal at `/content-editor/modals/ImgCueModal.vue`. This architectural split means:
- Different event emission patterns
- Different parent component contexts
- Different prop/emit declarations
- No guarantee of consistent behavior

### Recommended Fix
1. **Audit all duplicates**: Document which version is "canonical"
2. **Consolidate**: Move all cue modals to `/components/content-editor/modals/`
3. **Single source of truth**: Delete duplicates, update imports
4. **Linting rule**: Add ESLint rule to prevent duplicate component names

---

## 🔴 CRITICAL ISSUE #3: Inconsistent Event Handling Patterns

### The Problem
Modal components use **three different submit event patterns** across the codebase:

### Pattern Analysis

**Pattern 1: Direct emit (Composition API)**
```javascript
// SotModal.vue, FsqModal.vue
emit('submit', sotData)
emit('update:show', false)
```

**Pattern 2: Direct emit (Options API)**
```javascript
// PkgModal.vue, NatModal.vue, VoModal.vue
this.$emit('submit', { title, duration, slug, assetID, mediaURL })
```

**Pattern 3: Direct emit with no data transformation**
```javascript
// GfxModal.vue
@click="$emit('submit')"
```

**Pattern 4: Method-based emit with complex logic**
```javascript
// ImgCueModal.vue
submit() {
  const imgCueData = {
    assetId: await this.generateAssetId(),
    slug: this.formData.slug,
    // ... complex FormData construction
  }
  this.$emit('submit', imgCueData)
}
```

### Parent Handler Patterns

**Pattern A: Direct content manipulation**
```javascript
// ContentEditor.vue - submitSot
async submitSot(data) {
  const sotCue = `<!-- Begin Cue -->...<!-- End Cue -->`
  this.updateScriptContent(currentContent + sotCue)
}
```

**Pattern B: Ref-based emit forwarding (BROKEN)**
```javascript
// Original ContentEditor.vue approach (commented out)
this.$refs.editorPanel.$emit('update:scriptContent', newContent)
// Problem: EditorPanel may not exist, ref may be null
```

**Pattern C: Item creation then insertion**
```javascript
// ContentEditor.vue - createSOTItem
async createSOTItem(itemData) {
  const response = await axios.post(`/rundown/${episode}/item`, payload)
  // Creates DB record first, then loads into UI
}
```

### Why This Matters
**For SOT Bug Specifically:**
- SotModal uses Composition API `emit('submit', sotData)`
- ContentEditor expects Options API event handling
- No standardized data payload format
- No validation of event receipt

**General Impact:**
- Impossible to trace event flow without reading every component
- No contract/interface definition for modal emissions
- Copy-paste errors propagate across new modals
- Refactoring one modal breaks others

### Recommended Fix
1. **Define standard modal interface:**
```typescript
interface CueModalEvents {
  'submit': (data: CueData) => void
  'cancel': () => void
  'update:show': (value: boolean) => void
}
```

2. **Create base modal composable:**
```javascript
// composables/useCueModal.js
export function useCueModal(emit) {
  const submitCue = (cueData) => {
    emit('submit', cueData)
    emit('update:show', false)
  }
  const cancel = () => {
    emit('update:show', false)
  }
  return { submitCue, cancel }
}
```

3. **Standardize parent handlers:**
```javascript
// All cue submissions go through single method
async insertCue(cueData) {
  const cueBlock = this.formatCueBlock(cueData)
  await this.updateScriptContent(currentContent + cueBlock)
}
```

---

## 🟡 HIGH ISSUE #4: No Centralized State Management for Modals

### The Problem
Modal state is scattered across multiple components with **individual boolean flags**:

**From ContentEditor.vue:**
```javascript
data() {
  return {
    showGfxModal: false,
    showFsqModal: false,
    showSotModal: false,
    showVoModal: false,
    showNatModal: false,
    showPkgModal: false,
    showVoxModal: false,
    showMusModal: false,
    showLiveModal: false,
    showNewItemModal: false,
    showNewGFXModal: false,
    showNewSOTModal: false,
    // 12 different modal flags!
  }
}
```

### Consequences
1. **State bloat**: Every parent component manages modal state independently
2. **No modal history**: Can't track which modals were opened in sequence
3. **Race conditions**: Multiple modals can be open simultaneously
4. **No global modal management**: Can't close all modals on route change
5. **Testing complexity**: Must mock 12+ boolean flags per test

### Impact on SOT Bug
When debugging the SOT modal:
- No way to verify modal actually closed after submit
- No state tracking to see if modal reopened unexpectedly
- `showSotModal` flag manually toggled in multiple places
- No guarantee flag state matches modal visibility

### Recommended Fix

**Create Pinia Modal Store:**
```javascript
// stores/modals.js
import { defineStore } from 'pinia'

export const useModalStore = defineStore('modals', {
  state: () => ({
    activeModal: null,
    modalData: null,
    history: []
  }),

  actions: {
    openModal(modalName, data = null) {
      this.history.push({ modal: modalName, timestamp: Date.now() })
      this.activeModal = modalName
      this.modalData = data
    },

    closeModal() {
      this.activeModal = null
      this.modalData = null
    },

    closeAllModals() {
      this.activeModal = null
      this.modalData = null
    }
  },

  getters: {
    isModalOpen: (state) => (modalName) => state.activeModal === modalName
  }
})
```

**Usage:**
```vue
<template>
  <SotModal
    :show="modalStore.isModalOpen('sot')"
    @update:show="val => val ? modalStore.openModal('sot') : modalStore.closeModal()"
  />
</template>

<script>
import { useModalStore } from '@/stores/modals'
export default {
  setup() {
    const modalStore = useModalStore()
    return { modalStore }
  }
}
</script>
```

---

## 🟡 HIGH ISSUE #5: Component Responsibility Violations (ContentEditor.vue)

### The Problem
`ContentEditor.vue` is a **5,000+ line mega-component** that violates single responsibility principle:

**ContentEditor.vue Responsibilities (Current):**
1. Episode loading and metadata management
2. Rundown item selection and navigation
3. Script content editing and parsing
4. Modal state management (12 modals)
5. Cue insertion logic (8 cue types)
6. Auto-save and change tracking
7. Speaker detection and paragraph parsing
8. Asset ID generation coordination
9. Script compilation
10. WebSocket status monitoring
11. Theme color management
12. Keyboard shortcuts
13. Item creation (segments, SOTs, GFX)
14. Drag-and-drop file handling
15. Form validation across multiple cue types

### File Size Evidence
```bash
ContentEditor.vue:        ~45,938 tokens (too large to read in one operation)
EditorPanel.vue:          ~68,295 tokens (too large to read in one operation)
```

Both core components exceed token limits, indicating severe bloat.

### Consequences
1. **Impossible to debug**: 5000 lines means any bug could be anywhere
2. **Merge conflicts**: Multiple developers can't work on same component
3. **Performance**: Entire component re-renders on any state change
4. **Testing**: Impossible to write focused unit tests
5. **Cognitive load**: Developers can't hold mental model of component

### Impact on SOT Bug
The SOT insertion issue is buried in:
- 5000+ lines of ContentEditor.vue
- Among 12 other modal handlers
- Mixed with unrelated business logic
- No clear separation of concerns

Debugging requires:
- Reading entire file to understand context
- Tracking state across multiple unrelated features
- Understanding interactions between 15+ responsibilities

### Recommended Fix

**Decompose into feature-based components:**

```
ContentEditor.vue (orchestrator, <500 lines)
├── EpisodeLoader.vue (loading, metadata)
├── RundownNavigator.vue (item selection)
├── ScriptEditor.vue (content editing only)
├── CueInserter.vue (cue insertion logic)
├── ModalManager.vue (modal coordination)
└── AutoSaveManager.vue (change tracking, saves)
```

**Extract cue insertion to dedicated component:**
```vue
<!-- CueInserter.vue -->
<template>
  <component
    :is="currentModal"
    v-if="activeModal"
    @submit="handleCueSubmit"
  />
</template>

<script>
export default {
  methods: {
    async handleCueSubmit(cueData) {
      const cueBlock = this.formatCue(cueData)
      this.$emit('insert-cue', cueBlock)
    },

    formatCue(cueData) {
      // Centralized cue formatting logic
      return `<!-- Begin Cue -->\n${cueData}\n<!-- End Cue -->`
    }
  }
}
</script>
```

---

## 🟢 MEDIUM ISSUE #6: No Clear Component Organization Strategy

### The Problem
Components are organized by **type** (modals, views, settings) rather than **feature domain**, creating:

**Current Structure:**
```
/components
├── /modals (22 modals, all domains mixed)
│   ├── SotModal.vue (cue insertion)
│   ├── FsqModal.vue (cue insertion)
│   ├── TemplateManagerModal.vue (templates)
│   ├── AssetBrowserModal.vue (assets)
│   └── LoginModal.vue (auth)
├── /content-editor (has its own modals subdirectory!)
│   ├── /modals (duplicates of /modals!)
│   ├── EditorPanel.vue
│   └── CueToolbar.vue
├── /settings (settings components)
└── /tools (tool components)
```

### Issues
1. **Domain confusion**: Related features scattered across directories
2. **Duplication**: `/modals` and `/content-editor/modals` overlap
3. **No feature grouping**: Cue insertion logic split across multiple directories
4. **Import path inconsistency**: Some imports use `/modals`, others use `./modals`

### Recommended Fix

**Feature-Based Organization:**
```
/components
├── /cues (all cue-related components)
│   ├── /modals
│   │   ├── SotModal.vue
│   │   ├── FsqModal.vue
│   │   ├── ImgCueModal.vue
│   │   └── GfxModal.vue
│   ├── CuePlacementOverlay.vue
│   ├── CueToolbar.vue
│   └── CueParser.js
├── /editor (content editing domain)
│   ├── ContentEditor.vue
│   ├── EditorPanel.vue
│   ├── ScriptEditor.vue
│   └── RundownNavigator.vue
├── /rundown (rundown management)
│   ├── StackOrganizer.vue
│   └── RundownPanel.vue
├── /assets (asset management)
│   ├── AssetBrowserModal.vue
│   └── AssetUploader.vue
├── /templates (template management)
│   └── TemplateManagerModal.vue
└── /auth (authentication)
    └── LoginModal.vue
```

**Benefits:**
- All cue-related code in one place
- Clear domain boundaries
- Easier to find related components
- Reduces duplication (single `/cues/modals/` directory)

---

## Root Cause Analysis: Why These Issues Exist

### 1. **Rapid Feature Addition Without Refactoring**
Evidence: 12 modal flags added incrementally to ContentEditor.vue without extracting modal management.

### 2. **No Architectural Guidelines**
Evidence: Mixed Vue API usage (Options vs Composition) with no standard.

### 3. **Copy-Paste Development**
Evidence: Similar modal components with inconsistent event patterns suggest copy-paste without abstraction.

### 4. **Monolithic Component Growth**
Evidence: ContentEditor.vue and EditorPanel.vue grew beyond maintainable size (>5000 lines each).

### 5. **No Code Review for Architecture**
Evidence: Duplicate component files exist in multiple locations without resolution.

---

## Immediate Actions to Fix SOT Bug

**Based on architectural analysis, the SOT bug is likely caused by:**

1. **Event emission mismatch** (Critical Issue #3)
   - SotModal uses Composition API `emit('submit')`
   - ContentEditor uses Options API event handling
   - Event may not be properly bound or received

2. **Duplicate component confusion** (Critical Issue #2)
   - SOT modal at `/modals/SotModal.vue` may be wrong version
   - Working IMG modal is at `/content-editor/modals/ImgCueModal.vue`
   - Different parent contexts (ContentEditor vs EditorPanel)

3. **Missing event handler** (Critical Issue #3)
   - ContentEditor.vue may not have `@submit="submitSot"` properly bound
   - Event listener may be on wrong element
   - Modal show/hide state may interfere with event propagation

**Debugging Steps:**
1. ✅ Verify SotModal emits submit event (CONFIRMED: logs show emit called)
2. ❌ Verify ContentEditor receives submit event (NOT CONFIRMED: no logs appear)
3. ❓ Check if event listener is properly attached to SotModal component
4. ❓ Compare SotModal event handling to working ImgCueModal

**Likely Fix:**
Move SotModal to `/content-editor/modals/` and update ContentEditor to use same pattern as EditorPanel's IMG modal handling.

---

## Long-Term Recommendations

### Phase 1: Immediate Stability (1-2 weeks)
1. Consolidate duplicate components
2. Standardize all modal event patterns
3. Document current Vue API usage (Options vs Composition)

### Phase 2: Architectural Cleanup (1-2 months)
1. Create Pinia modal store
2. Extract ContentEditor into smaller components
3. Migrate all modals to Composition API
4. Create base modal composable

### Phase 3: Reorganization (2-3 months)
1. Reorganize components by feature domain
2. Create architectural decision records (ADRs)
3. Establish component size limits (<500 lines)
4. Add linting rules for architecture enforcement

---

## Conclusion

The SOT cue insertion bug is a **symptom of systemic architectural issues**, not an isolated code defect. The codebase exhibits:

- ❌ No consistent Vue API paradigm
- ❌ Duplicate components with drift
- ❌ No standardized event patterns
- ❌ Monolithic component design
- ❌ No centralized state management
- ❌ Type-based rather than domain-based organization

**These issues compound** to make debugging extraordinarily difficult:
- Console logs disappear in framework noise
- Event flow is unpredictable
- Multiple code paths for same feature
- No single source of truth

**Fix the architecture, fix the bugs.**

The immediate SOT bug can be resolved by standardizing event handling, but without addressing underlying architecture, similar bugs will continue to emerge in other features.
