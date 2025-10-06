# Show-Build Debugging Standards & Checklist

**Purpose**: Systematic debugging approach to catch common issues quickly and prevent recurring problems.

## 🔍 MANDATORY DEBUGGING CHECKLIST

Run this checklist **EVERY TIME** you encounter unexplained frontend issues:

### 1. Vue Template Ref Naming Conflicts ⚠️

**Issue**: Template `ref` names conflicting with reactive variables cause mysterious form resets and reactivity failures.

**Check Command:**
```bash
cd disaffected-ui/src
echo "🔍 Checking for template ref naming conflicts..."
grep -rn 'ref="[^"]*"' . | sed 's/.*ref="\([^"]*\)".*/\1/' | sort | uniq -d
```

**Expected Output**: Empty (no conflicts) or list of conflicting names to fix

**Quick Fix Pattern:**
```vue
<!-- ❌ BAD: Conflict -->
<v-form ref="episodeForm">
<script>
const episodeForm = ref({})
</script>

<!-- ✅ GOOD: No conflict -->
<v-form ref="episodeFormRef">
<script>
const episodeForm = ref({})
</script>
```

### 2. Vue Component Mounting Issues

**Issue**: Duplicate app instances or mounting conflicts cause old versions to flash

**Check Command:**
```bash
echo "🔍 Checking for duplicate Vue app mounting..."
grep -rn "createApp\|mount(" disaffected-ui/src/main.js
grep -rn "app\." disaffected-ui/src/main.js
```

**Browser Check**: 
- Open DevTools → Console
- Look for duplicate Vue app warnings
- Check for old component versions flashing

### 3. Vue Reactivity System Debug

**Issue**: Reactive variables not updating or losing reactivity

**Debug Pattern to Add:**
```javascript
// Add to component setup() function for debugging
watch(yourReactiveVariable, (newVal, oldVal) => {
  console.log('Reactivity check:', { newVal, oldVal });
}, { deep: true, immediate: true });
```

### 4. Vuetify Component State Issues

**Issue**: Vuetify components (v-select, v-dialog) not behaving as expected

**Check Commands:**
```bash
echo "🔍 Checking Vuetify version compatibility..."
cd disaffected-ui && npm list vuetify

echo "🔍 Checking for v-model binding issues..."
grep -rn "v-model=" src/ | grep -E "(template_id|episode|form)"
```

#### Vuetify Text Clipping (Faded/Cut-off Text)

**Symptom**: Text in v-textarea or v-text-field appears faded, clipped, or cut off at the top (50%+ of characters missing)

**Root Cause**: Vuetify applies CSS `mask`, `clip-path`, or `-webkit-mask` properties that clip content at container boundaries

**Solution** (`EditorPanel.vue:4926-4987`):
```css
.your-textarea :deep(.v-field),
.your-textarea :deep(.v-field__input),
.your-textarea :deep(textarea) {
  clip-path: none !important;
  mask: none !important;
  -webkit-mask: none !important;
  overflow: visible !important;
}
```

**Why This Works**:
- Disables all CSS clipping mechanisms at every nesting level
- `overflow: visible` ensures content can extend beyond container
- Must apply to `.v-field`, `.v-field__input`, AND `textarea` elements
- Use `:deep()` selector to penetrate Vuetify's component encapsulation

**Related Issues**:
- Vuetify GitHub #12671 - v-text-field text clipped with large font-size
- Vuetify GitHub #11990 - v-textarea line-height doesn't work properly
- Common when using custom padding or line-height with Vuetify components

### 5. API Endpoint Consistency

**Issue**: Frontend calling wrong endpoints or field name mismatches

**Check Commands:**
```bash
echo "🔍 Checking API endpoint calls..."
grep -rn "axios\." disaffected-ui/src/ | grep -E "(episodes|templates)"

echo "🔍 Checking field name consistency..."
grep -rn "template_id\|episode_number\|next_number" disaffected-ui/src/
```

### 6. Console Error Analysis

**Issue**: JavaScript errors being masked or ignored

**Browser Debug Steps:**
1. Open DevTools → Console
2. Enable "Preserve log" and "Verbose" levels
3. Clear console and reproduce issue
4. Look for:
   - Uncaught Promise rejections
   - Vue reactivity warnings
   - Network 404/500 errors
   - Component lifecycle errors

### 7. Network Request Validation

**Issue**: API calls failing silently or returning unexpected data

**Check Commands:**
```bash
echo "🔍 Testing API endpoints directly..."
curl -s http://localhost:8888/api/episodes/next-number | jq .
curl -s http://localhost:8888/api/episodes/templates | jq .
```

**Browser Network Tab**: Check for failed requests, wrong response formats

---

## 🛠️ DEBUGGING WORKFLOW

When encountering any frontend issue, follow this exact sequence:

### Phase 1: Quick Scans (2 minutes)
```bash
#!/bin/bash
echo "=== SHOW-BUILD DEBUGGING QUICK SCAN ==="
cd /mnt/process/show-build/disaffected-ui/src

echo "1. Template ref conflicts:"
grep -rn 'ref="[^"]*"' . | sed 's/.*ref="\([^"]*\)".*/\1/' | sort | uniq -d

echo "2. Vue mounting issues:"
grep -rn "createApp\|mount(" ../main.js

echo "3. Recent console errors (check browser DevTools manually)"
echo "4. API endpoint accessibility:"
cd .. && curl -s http://localhost:8888/health | jq . 2>/dev/null || echo "Backend not accessible"
```

### Phase 2: Deep Analysis (5 minutes)
- Add reactive debugging to suspect components
- Check browser DevTools Console + Network tabs
- Verify API responses with direct curl tests
- Check component lifecycle with Vue DevTools

### Phase 3: Component-Specific Debug
- Add extensive console.log statements to track data flow
- Use Vue DevTools to inspect reactive state
- Isolate the failing component/function

---

## 📋 NAMING CONVENTIONS (Enforced Standards)

### Template Refs
**ALWAYS** use descriptive names ending in `Ref`:
- `episodeFormRef` (not `episodeForm`)
- `createDialogRef` (not `dialog`)  
- `dataTableRef` (not `table`)
- `fileInputRef` (not `fileInput`)

### Reactive Variables  
**ALWAYS** use descriptive, different names:
- `episodeFormData` (not `episodeForm`)
- `dialogVisible` (not `dialog`)
- `tableItems` (not `table`)
- `selectedFiles` (not `fileInput`)

### API Response Handling
**ALWAYS** validate response structure:
```javascript
// ❌ BAD: Assumes response structure
const episodeNumber = response.data.next_episode_number;

// ✅ GOOD: Validates and handles variations
const episodeNumber = response.data.next_number || response.data.next_episode_number;
if (!episodeNumber) {
  console.error('Unexpected API response structure:', response.data);
}
```

---

## 🔧 AUTOMATIC VALIDATION COMMANDS

Add these to your development workflow:

### Pre-commit Hook (Recommended)
```bash
#!/bin/bash
# Save as .git/hooks/pre-commit
cd disaffected-ui/src
CONFLICTS=$(grep -rn 'ref="[^"]*"' . | sed 's/.*ref="\([^"]*\)".*/\1/' | sort | uniq -d)
if [ ! -z "$CONFLICTS" ]; then
    echo "❌ Template ref naming conflicts found:"
    echo "$CONFLICTS"
    echo "Fix conflicts before committing!"
    exit 1
fi
echo "✅ No template ref conflicts found"
```

### Development Alias
Add to your shell profile:
```bash
alias debug-showbuild='cd /mnt/process/show-build && echo "=== DEBUGGING SCAN ===" && cd disaffected-ui/src && echo "Template ref conflicts:" && grep -rn "ref=\"[^\"]*\"" . | sed "s/.*ref=\"\([^\"]*\)\".*/\1/" | sort | uniq -d && echo "Done. Check browser DevTools for runtime issues."'
```

---

## 📚 ISSUE RESOLUTION PATTERNS

### Pattern 1: Form Not Populating
**Symptoms**: Form fields remain empty despite data loading
**Common Causes**: 
1. Template ref naming conflicts ✅ 
2. Async data race conditions
3. v-model binding issues

**Debug Steps**: Run checklist items 1, 3, 4

### Pattern 2: Data Loads Then Disappears  
**Symptoms**: Data briefly appears then resets
**Common Causes**:
1. Template ref conflicts ✅
2. Unexpected function calls resetting state
3. Component lifecycle issues

**Debug Steps**: Add stack trace logging to reset functions

### Pattern 3: API Calls Failing Silently
**Symptoms**: No error messages, data doesn't load
**Common Causes**:
1. Wrong endpoint URLs
2. Field name mismatches  
3. Authentication issues

**Debug Steps**: Run checklist items 5, 7

---

## 🎯 SUCCESS METRICS

After implementing debugging standards, track:
- **Time to identify root cause**: Should decrease significantly
- **Recurring issue frequency**: Should approach zero for documented patterns
- **Debug confidence**: Team should feel systematic about troubleshooting

**Goal**: Any debugging session should start with this checklist and resolve 80% of issues within the documented patterns.