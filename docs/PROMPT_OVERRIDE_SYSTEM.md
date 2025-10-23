# LLM Prompt Override System

## Overview

The Prompt Override System allows **administrators only** to customize LLM prompts used throughout Show-Build without modifying code. Overrides are stored in the database and can be managed through a web UI.

**⚠️ Admin Access Required**: All prompt management endpoints require admin privileges (`admin.*` permission in RBAC system).

## Architecture

### Database
- **Table**: `prompt_overrides`
- **Fields**:
  - `id` - UUID primary key
  - `category` - Prompt category (generate, analyze, extract, refactor, compose)
  - `operation_key` - Operation identifier (e.g., `generate-segment-script`)
  - `system_prompt` - Override for system prompt (optional)
  - `user_prompt_template` - Override for user prompt with `{{variable}}` placeholders (optional)
  - `is_enabled` - Enable/disable toggle
  - `notes` - Developer notes
  - `created_by` - User who created the override
  - `created_at`, `updated_at` - Timestamps
  - `metadata` - JSONB for additional data

### Backend API
**Base URL**: `/api/prompts`

**Endpoints**:
- `GET /overrides` - List all overrides (filterable by category, enabled status)
- `GET /overrides/{id}` - Get specific override
- `POST /overrides` - Create new override
- `PATCH /overrides/{id}` - Update override
- `DELETE /overrides/{id}` - Delete override
- `POST /overrides/{id}/toggle` - Toggle enabled status
- `GET /operations` - List available operations by category

### Frontend
**Component**: `PromptManager.vue`
**Location**: Settings → AI & LLM → LLM Prompts
**Navigation**: Main menu → Settings → AI & LLM → LLM Prompts

**Features**:
- Table view of all overrides
- Filter by category
- Toggle enable/disable with switch
- Create/edit dialog with form validation
- Delete confirmation
- Category color coding

### Composable Integration
**File**: `src/composables/useLLMPrompts.js`

The `getLLMPrompt()` function now:
1. Checks for database overrides (cached for 60 seconds)
2. Falls back to default prompts if no override exists
3. Returns metadata indicating if prompt was overridden

**Usage**:
```javascript
import { getLLMPrompt } from '@/composables/useLLMPrompts'

// Without override check (uses default)
const prompt = await getLLMPrompt('fsq-split-analysis', { quote, maxLines })

// With override check (checks database)
const prompt = await getLLMPrompt('fsq-split-analysis',
  { quote, maxLines },
  { category: 'generate' }
)

console.log(prompt.overridden) // true if database override was used
```

## Creating a Prompt Override

### Via Web UI (Recommended)

1. Navigate to **Main Menu → Settings → AI & LLM → LLM Prompts**
2. Click **"New Override"** button
3. Fill in the form:
   - **Category**: Select from dropdown (generate, analyze, extract, refactor, compose)
   - **Operation**: Select specific operation for that category
   - **System Prompt**: Optional override for system instructions
   - **User Prompt Template**: Optional override with `{{variable}}` placeholders
   - **Developer Notes**: Optional notes explaining the override
   - **LLM Route Override** (Optional):
     - **Suggested Service**: e.g., ollama, openai, anthropic, gemini, grok
     - **Suggested Model**: e.g., grok-2-latest, claude-3-5-sonnet-20241022
     - **Temperature**: 0.0 (deterministic) to 2.0 (creative)
     - **Max Tokens**: e.g., 4096, 8192
   - **Enable**: Check to activate immediately
4. Click **"Create"**

### Via API

```bash
curl -X POST http://localhost:8888/api/prompts/overrides \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "generate",
    "operation_key": "generate-segment-script",
    "system_prompt": "You are an expert podcast script writer...",
    "user_prompt_template": "Write a {{duration}} script about {{topic}}...",
    "is_enabled": true,
    "notes": "Custom prompt for better tone",
    "suggested_service": "grok",
    "suggested_model": "grok-2-latest",
    "temperature": 0.7,
    "max_tokens": 4096
  }'
```

### Via SQL (Not Recommended)

```sql
INSERT INTO prompt_overrides (
  category, operation_key, system_prompt, user_prompt_template,
  is_enabled, notes, created_by,
  suggested_service, suggested_model, temperature, max_tokens
) VALUES (
  'generate',
  'generate-segment-script',
  'You are an expert podcast script writer...',
  'Write a {{duration}} script about {{topic}}...',
  true,
  'Custom prompt for better tone',
  'admin',
  'grok',
  'grok-2-latest',
  0.7,
  4096
);
```

## Template Variables

User prompt templates support variable substitution using `{{variable}}` syntax.

**Example**:
```
Write a {{duration}} podcast script about {{topic}}.
The tone should be {{tone}} and target audience is {{audience}}.
Include {{numPoints}} main points.
```

Variables are automatically replaced with values passed to `getLLMPrompt()`:
```javascript
const prompt = await getLLMPrompt('my-operation', {
  duration: '3 minutes',
  topic: 'AI development',
  tone: 'casual',
  audience: 'developers',
  numPoints: 5
}, { category: 'generate' })
```

## LLM Route Override

**Purpose**: Different LLM models have different strengths and prompting styles. The route override feature allows you to specify which LLM service and model should handle a specific operation, along with custom temperature and token limits.

**How It Works**:
1. When creating/editing a prompt override, you can optionally specify:
   - **Suggested Service**: The LLM provider (ollama, openai, anthropic, gemini, grok)
   - **Suggested Model**: The specific model to use (e.g., grok-2-latest, claude-3-5-sonnet-20241022)
   - **Temperature**: Controls randomness (0.0 = deterministic, 2.0 = creative)
   - **Max Tokens**: Maximum response length

2. The Universal LLM Framework can read these settings and route requests accordingly

**Example Use Cases**:
- **Creative tasks** (generate-segment-script): Use Grok with temperature 0.9 for more creative outputs
- **Analytical tasks** (analyze-script-tone): Use Claude with temperature 0.3 for consistent analysis
- **Fast iterations** (extract-keywords): Use local Ollama models for speed
- **Long-form content** (generate-episode-description): Increase max_tokens to 8192

**Model Selection Guidelines**:
- **Claude**: Excellent instruction following, good for structured tasks
- **GPT-4**: Strong reasoning, good for analysis
- **Grok**: Creative outputs, conversational tone
- **Gemini**: Fast, good for quick tasks
- **Ollama**: Local models, privacy-focused, cost-free

**Available Models**:
- Check available models with: `docker exec -it ollama ollama list` (for Ollama)
- Service-specific models are configured in Settings → AI & LLM → API Access
- Grok models include: grok-2-latest, grok-2-1212, grok-beta, and many vision variants

## Available Operations

### Generate
- `generate-segment-script`
- `generate-ad-script`
- `generate-promo-script`
- `generate-cta-script`
- `generate-outro-script`
- `generate-coldopen-script`
- `generate-tease-script`
- `generate-episode-description`
- `generate-segment-title`
- `generate-social-media-post`

### Analyze
- `analyze-script-tone`
- `analyze-script-length`
- `analyze-script-sentiment`
- `analyze-episode-structure`
- `analyze-pacing`

### Extract
- `extract-keywords`
- `extract-episode-number`
- `extract-metadata`

### Inventory (File System Analysis)
- `inventory-match-file-to-expectation` - Match a file to canonical expectation
- `inventory-classify-stray-file` - Classify unrecognized file
- `inventory-identify-duplicate` - Determine if files are duplicates
- `inventory-validate-file-purpose` - Validate file serves expected purpose
- `extract-quotes`
- `extract-topics`
- `extract-metadata`
- `extract-timestamps`

### Refactor
- `refactor-shorten-script`
- `refactor-lengthen-script`
- `refactor-adjust-tone`
- `refactor-improve-clarity`
- `refactor-add-humor`

### Compose
- `compose-episode-summary`
- `compose-show-notes`
- `compose-newsletter`
- `compose-segment-transition`

## Caching

Prompt overrides are cached for **60 seconds** to avoid excessive database queries.

**Clear cache**:
```javascript
import { clearPromptOverridesCache } from '@/composables/useLLMPrompts'

// After creating/updating/deleting overrides
clearPromptOverridesCache()
```

The cache is automatically cleared when:
- Creating a new override (via UI)
- Updating an override (via UI)
- Deleting an override (via UI)

## Best Practices

1. **Test Overrides First**: Create with `is_enabled: false`, test thoroughly, then enable
2. **Document Changes**: Use the `notes` field to explain why the override was needed
3. **Keep Templates Flexible**: Use variables instead of hardcoding values
4. **Monitor Performance**: Check console logs for override usage
5. **Version Control**: Export critical overrides to SQL for backup

## Troubleshooting

### Override Not Working
- Check `is_enabled` is `true`
- Verify correct `category` is passed to `getLLMPrompt()`
- Check browser console for "Using database override" message
- Clear cache: `clearPromptOverridesCache()`

### Variables Not Substituting
- Ensure variable names in template match parameter names exactly
- Use `{{variable}}` syntax (double braces)
- Check console for errors

### UI Not Loading Overrides
- Check backend API is running: `curl http://localhost:8888/api/prompts/overrides`
- Check authentication (API key or JWT token)
- Check browser console for errors

## Future Enhancements

- [ ] Prompt versioning and rollback
- [ ] A/B testing framework
- [ ] Prompt performance metrics
- [ ] Export/import prompt sets
- [ ] Prompt template validation
- [ ] Variable autocomplete in UI
