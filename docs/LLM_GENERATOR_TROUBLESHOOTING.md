# LLM Test Segment Generator Troubleshooting Guide

**Feature**: ContentEditor keyboard shortcut `Ctrl+Alt+Shift+[1-9]` generates test podcast segments using LLM

**File**: `/disaffected-ui/src/components/ContentEditor.vue:4031` (function `generateTestSegment()`)

---

## Common Issues and Solutions

### Issue 1: "No LLM service is enabled" Error

**Symptoms:**
- Press keyboard shortcut
- Error notification: "No LLM service is enabled"
- Browser console shows "Failed to load API configs"

**Root Causes:**
1. **Not logged in** - JWT token is undefined
2. **Token expired** - Token exists but is > 48 hours old
3. **API configs endpoint failing** - Backend returning 500/401

**Solutions:**

```javascript
// Check token in browser console
console.log('Token:', localStorage.getItem('auth-token'))
console.log('Expiry:', localStorage.getItem('auth-token-expiry'))
```

- If `null/undefined`: **Log in** (username: `kevin`, password: `test123`)
- If expired: **Log in again** to get fresh token
- If valid but still failing: Check backend logs for auth errors

---

### Issue 2: 504 Gateway Timeout / Ollama Times Out

**Symptoms:**
- Request takes 60+ seconds
- Returns 504 Gateway Timeout
- Backend logs show: `ERROR:llm_proxy_router:Ollama request timed out`

**Root Causes:**
1. **Using slow model** - `llama2:13b-chat` is too slow (13B parameters)
2. **Timeout too short** - Default was 60s, insufficient for long prompts
3. **Prompt too long** - 1000+ character prompts need more time

**Solutions:**

**Check which model is being used:**
```bash
# Backend logs
docker logs show-build-server 2>&1 | grep "Proxying Ollama request" | tail -5
# Should show: "Model: llama3:latest" (NOT "llama2")
```

**Fix slow model defaults:**
```javascript
// File: disaffected-ui/src/composables/useLLM.js:293
ollamaModels: {
  contentExpansion: 'llama3:latest',  // ✅ Fast (8B params)
  // NOT: 'llama2:13b-chat'            // ❌ Slow (13B params)
}
```

**Increase timeout:**
```python
# File: app/llm_proxy_router.py:65
async with httpx.AsyncClient(timeout=180.0) as client:  # 3 minutes
```

**Fast models available on 192.168.51.197:11434:**
- `llama3:latest` - Best balance (8B, fast, quality)
- `mistral:7b` - Fastest for short tasks
- `Qwen2.5-Coder:7b` - Fast, good for structured output

---

### Issue 3: Mixed Content Blocking (HTTPS → HTTP)

**Symptoms:**
- Browser console: `Blocked loading mixed active content "http://192.168.51.197:11434/api/generate"`
- Network error on Ollama calls
- No error logs on backend

**Root Cause:**
- Frontend accessed via HTTPS (`https://192.168.51.210:8091`)
- Frontend tries to call Ollama directly via HTTP
- Browser blocks HTTPS → HTTP requests (security policy)

**Solution:**

✅ **Always use HTTPS URL**: `https://192.168.51.210:8091`

✅ **Backend proxy endpoint** (already implemented):
```javascript
// File: disaffected-ui/src/composables/useLLM.js:41
// Calls /api/llm/ollama/generate (HTTPS)
// Backend proxies to http://192.168.51.197:11434 (server-to-server, allowed)
const response = await axios.post('/api/llm/ollama/generate', { ... })
```

✅ **Auto-redirect to HTTPS**:
```html
<!-- File: disaffected-ui/public/index.html:9-14 -->
<script>
  if (window.location.protocol === 'http:' && window.location.hostname !== 'localhost') {
    window.location.href = 'https:' + window.location.href.substring(window.location.protocol.length);
  }
</script>
```

---

### Issue 4: Authentication Logout Loop

**Symptoms:**
- Log in successfully
- Any 401 error immediately logs you out
- Token gets deleted from localStorage
- Have to re-login constantly

**Root Cause:**
```javascript
// BROKEN: App.vue axios interceptor (OLD CODE)
if (error.response?.status === 401) {
  handleLogout()  // ❌ Deletes token on every 401!
  showLoginModal.value = true
}
```

**The Problem:**
1. You log in → token saved
2. Any API call returns 401 (slow timeout, expired token, etc.)
3. Interceptor calls `handleLogout()` → **deletes your valid token**
4. Next API call has no token → 401
5. Logout again → infinite loop

**Solution:**
```javascript
// FIXED: App.vue:366-370
if (error.response?.status === 401) {
  // Don't clear localStorage token - just show login modal
  // This prevents logout loops when token expires or API calls fail
  isAuthenticated.value = false
  showLoginModal.value = true
}
```

**Why This Works:**
- Token stays in localStorage even after 401
- If token is valid but single API call fails → user can retry
- If token truly expired → user logs in, new token overwrites old one
- No more deletion → no more loops

---

### Issue 5: LLM Generates Text But Doesn't Display in Editor

**Symptoms:**
- Backend logs show: `Ollama response received, length: 2600 chars`
- Success notification appears
- **No text appears in editor**

**Root Causes:**
1. **Vue reactivity not triggering** - `rawMarkdownContent` updated but computed properties don't recalculate
2. **Editor ref not available** - `this.$refs.editorPanel` is null/undefined
3. **Looking in wrong place** - Script mode is just a VIEW of the raw markdown, check Code mode to see actual raw content

**Understanding the Data Flow:**

The ContentEditor uses a **single-source-of-truth** architecture:

```
rawMarkdownContent (source of truth - stores YAML frontmatter + content)
         ↓
   parsedContent() computed (ContentEditor.vue:983)
         ↓ parses frontmatter and extracts script
   scriptContent() computed (ContentEditor.vue:1032)
         ↓ displayed in UI
   "Script" tab view (read-only view of scriptContent)
```

**CRITICAL**: "Script mode" is NOT a separate storage location - it's a **view** that displays the `scriptContent` computed property, which is derived from `rawMarkdownContent`. The LLM generator writes to `rawMarkdownContent` at line 1111:

```javascript
// ContentEditor.vue:1100-1114 - updateScriptContent()
updateScriptContent(newScriptContent) {
  const parsed = this.parsedContent;

  // Rebuild frontmatter YAML
  const frontmatterLines = Object.entries(parsed.frontmatter)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n');

  // Rebuild full markdown content (writes to raw markdown)
  if (frontmatterLines) {
    this.rawMarkdownContent = `---\n${frontmatterLines}\n---\n\n${newScriptContent}`;
  } else {
    this.rawMarkdownContent = newScriptContent;
  }
}
```

**Diagnostic Steps:**

```javascript
// Check console for these debug messages (ContentEditor.vue:4093-4106)
console.log('📝 Generated text length:', generatedText?.length, 'chars');
console.log('📝 Generated text preview:', generatedText?.substring(0, 100));
console.log('📝 New script length:', newScript.length, 'chars');
console.log('🔄 After nextTick, scriptContent:', this.scriptContent?.substring(0, 100));
```

**Solution 1: Check Raw Markdown Content**
- Switch to **"Code"** tab in EditorPanel to see actual `rawMarkdownContent`
- LLM text is inserted here as raw markdown (after YAML frontmatter)
- "Script" tab just displays the content portion without frontmatter

**Solution 2: Force Vue Reactivity**
```javascript
// File: ContentEditor.vue:4104-4111
this.updateScriptContent(newScript);

// Force Vue to re-render
this.$nextTick(() => {
  if (this.$refs.editorPanel && this.$refs.editorPanel.$forceUpdate) {
    this.$refs.editorPanel.$forceUpdate();
  }
});
```

**Solution 3: Check Editor Ref**
```javascript
// If logs show "❌ EditorPanel ref not available"
// Wait for component to mount
if (!this.$refs.editorPanel) {
  console.error('EditorPanel not mounted yet');
  return;
}
```

---

## Complete Diagnostic Checklist

Run this in browser console when generator fails:

```javascript
// === AUTHENTICATION ===
console.log('Token:', localStorage.getItem('auth-token'))
console.log('Token exists:', !!localStorage.getItem('auth-token'))
console.log('Expiry:', new Date(parseInt(localStorage.getItem('auth-token-expiry'))))
console.log('Is expired:', Date.now() > parseInt(localStorage.getItem('auth-token-expiry')))

// === PROTOCOL ===
console.log('Protocol:', window.location.protocol)
console.log('Using HTTPS:', window.location.protocol === 'https:')

// === AXIOS ===
console.log('Axios auth header:', axios.defaults.headers.common['Authorization'])

// === BACKEND CHECK ===
fetch('/api/settings/api-configs')
  .then(r => r.json())
  .then(d => console.log('API Configs:', d.data?.preproduction?.ai_services?.ollama))
  .catch(e => console.error('Config fetch failed:', e))
```

---

## Backend Diagnostic Commands

```bash
# Check Ollama connectivity
curl -s http://192.168.51.197:11434/api/tags | jq '.models[].name'

# Check backend logs for LLM requests
docker logs show-build-server 2>&1 | grep -A 5 "Proxying Ollama request" | tail -20

# Check for timeouts
docker logs show-build-server 2>&1 | grep "timeout\|504" | tail -10

# Check authentication errors
docker logs show-build-server 2>&1 | grep "401\|Authentication" | tail -10

# Verify Ollama model in database
docker exec show-build-postgres psql -U showbuild -d showbuild -c \
  "SELECT config_key, config_value FROM api_configs WHERE service = 'ollama';"
```

---

## Architecture Overview

```
User presses Ctrl+Alt+Shift+3
  ↓
ContentEditor.vue:2309 (keyboard handler)
  ↓
ContentEditor.vue:4031 generateTestSegment()
  ↓
useLLM.js:302 smartCall() with taskType: 'content-expansion'
  ↓
useLLM.js:293 routes to ollamaModels.contentExpansion (should be 'llama3:latest')
  ↓
useLLM.js:391 callSpecificService('ollama', prompt, options)
  ↓
useLLM.js:41 callOllama() → POST /api/llm/ollama/generate
  ↓
llm_proxy_router.py:48 ollama_generate_proxy()
  ↓
Checks authentication (get_current_user_or_key)
  ↓
Queries database for Ollama host (get_ollama_host_from_db)
  ↓
httpx.post(http://192.168.51.197:11434/api/generate)
  ↓
Returns response to frontend
  ↓
ContentEditor.vue:4102 updateScriptContent(generatedText)
  ↓
Updates rawMarkdownContent (line 1111)
  ↓ single source of truth
Computed property parsedContent() recalculates (line 983)
  ↓ parses YAML frontmatter + content
Computed property scriptContent() recalculates (line 1032)
  ↓ extracts content without frontmatter
EditorPanel displays in "Script" tab (view-only)
EditorPanel displays in "Code" tab (raw markdown with frontmatter)
```

**Data Flow Details:**

1. **rawMarkdownContent** (reactive string) - Source of truth
   ```
   ---
   id: 12345
   title: Episode Title
   ---

   [LLM-generated content inserted here]
   ```

2. **parsedContent()** (computed) - Parses into frontmatter + script
3. **scriptContent()** (computed) - Extracts content only
4. **"Script" tab** - Displays `scriptContent` (content without frontmatter)
5. **"Code" tab** - Displays `rawMarkdownContent` (full markdown with frontmatter)

---

## Key Files Reference

| File | Purpose | Key Functions/Lines |
|------|---------|-------------------|
| `ContentEditor.vue:2309` | Keyboard handler | Listens for Ctrl+Alt+Shift+[1-9] |
| `ContentEditor.vue:4031` | Generator function | `generateTestSegment()` |
| `ContentEditor.vue:1100` | Update script | `updateScriptContent()` |
| `ContentEditor.vue:983` | Parse markdown | `parsedContent()` computed |
| `ContentEditor.vue:1032` | Get script content | `scriptContent()` computed |
| `useLLM.js:38` | Ollama caller | `callOllama()` - uses proxy |
| `useLLM.js:293` | Model routing | `ollamaModels.contentExpansion` |
| `useLLM.js:302` | Smart router | `smartCall()` - task-based routing |
| `llm_proxy_router.py:48` | Backend proxy | `/api/llm/ollama/generate` endpoint |
| `llm_proxy_router.py:65` | Timeout config | `httpx.AsyncClient(timeout=180.0)` |
| `App.vue:366` | Auth interceptor | Handles 401 errors |
| `index.html:9` | HTTPS redirect | Forces HTTPS on non-localhost |

---

## Quick Fixes Reference

### "No LLM service enabled"
```bash
# Just log in
# Username: kevin
# Password: test123
```

### "504 Gateway Timeout"
```javascript
// Change model: disaffected-ui/src/composables/useLLM.js:293
contentExpansion: 'llama3:latest',  // NOT llama2:13b-chat
```

### "Mixed content blocked"
```bash
# Access via HTTPS only
https://192.168.51.210:8091
```

### "Text generated but not showing"
```javascript
// Switch to Script mode in editor
// Or force refresh: this.$refs.editorPanel.$forceUpdate()
```

### "Logout loop"
```javascript
// App.vue:367 - Don't call handleLogout(), just set isAuthenticated = false
```

---

## Testing the Generator

1. **Access via HTTPS**: `https://192.168.51.210:8091`
2. **Accept self-signed cert** (if prompted)
3. **Log in**: kevin / test123
4. **Open any episode** in ContentEditor
5. **Switch to Script mode** in EditorPanel
6. **Press**: `Ctrl+Alt+Shift+3` (or `Control+Option+Shift+3` on Mac)
7. **Wait**: 5-30 seconds for generation
8. **Check**: Text should appear in script editor

**Expected console output:**
```
🧪 Generating test segment with 3 paragraphs...
🎯 Calling smartCall with taskType: content-expansion
🤖 Using Ollama (llama3:latest) for content-expansion
📝 Generated text length: 2656 chars
📝 Generated text preview: This week, we're diving into...
📝 New script length: 2656 chars
🔄 After nextTick, scriptContent: This week, we're diving into...
✅ Test segment generated and inserted
```

---

## Future Improvements

- [ ] Add loading spinner during generation
- [ ] Allow model selection via UI
- [ ] Add "Regenerate" button
- [ ] Save LLM preferences per user
- [ ] Add more task types (fact-checking, title-generation, etc.)
- [ ] Implement streaming responses for real-time feedback
- [ ] Add token usage tracking
- [ ] Support other LLM providers (OpenAI, Anthropic, etc.)

---

**Last Updated**: 2025-10-07
**Maintained By**: Claude Code Session Continuation
**Related Docs**:
- `DEBUG_FIRST.md` - General frontend debugging
- `DEBUGGING_STANDARDS.md` - Systematic debugging checklist
- `VUE_TEMPLATE_REF_CONFLICTS.md` - Vue reactivity issues
