# LLM Prompt Override Integration Guide

## Overview

The prompt override system allows you to customize LLM prompts without modifying code. This guide shows how to integrate overrides into your LLM operations.

## How Connection Works

### 1. **Override Identification**

Each override is uniquely identified by:
```
category.operation_key
```

Examples:
- `generate.generate-segment-script`
- `analyze.analyze-script-tone`
- `extract.extract-keywords`

### 2. **Creating an Override in UI**

**Steps:**
1. Go to **Settings → LLM Prompts tab**
2. Click **New Override**
3. Select **Category**: `generate`
4. Select **Operation**: `generate-segment-script`
5. Enter custom prompts:
   - **System Prompt**: "You are an expert podcast script writer specialized in {{duration}} segments..."
   - **User Prompt Template**: "Write a script for a segment titled '{{title}}' that will be exactly {{duration}} long. Topic: {{topic}}"
6. Enable the override
7. Click **Create**

### 3. **Using Overrides in Code**

#### Option A: Direct Integration (Recommended for New Code)

When making LLM calls, use the `getLLMPrompt()` function with the category parameter:

```javascript
import { getLLMPrompt } from '@/composables/useLLMPrompts'

// Example: Generate segment script
async function generateSegmentScript(title, topic, duration) {
  // Get prompt (checks for override automatically)
  const promptData = await getLLMPrompt(
    'generate-segment-script',  // operation_key
    { title, topic, duration }, // template variables
    { category: 'generate' }    // enables override checking
  )

  console.log('Using override:', promptData.overridden) // true if override exists

  // Make LLM API call with prompt
  const response = await axios.post('/api/llm/generate', {
    system: promptData.systemPrompt,
    user: promptData.prompt,
    temperature: promptData.temperature,
    max_tokens: promptData.maxTokens
  })

  return response.data
}
```

#### Option B: Backend Integration (For Universal LLM Framework)

For operations using the Universal LLM Framework, integrate at the backend level:

**Backend (`app/llm_operations.py`):**
```python
from prompts_router import get_prompt_override

async def execute_llm_operation(operation_type: str, operation_key: str, params: dict):
    """Execute LLM operation with prompt override support"""

    # Check for database override
    override = await get_prompt_override(operation_type, operation_key)

    if override and override.is_enabled:
        # Use custom prompt
        system_prompt = override.system_prompt or get_default_system_prompt(operation_key)
        user_prompt = render_template(override.user_prompt_template, params)
        print(f"🎯 Using override for {operation_type}.{operation_key}")
    else:
        # Use default prompt
        system_prompt = get_default_system_prompt(operation_key)
        user_prompt = get_default_user_prompt(operation_key, params)

    # Call LLM API
    result = await call_llm_api(system_prompt, user_prompt)
    return result
```

## Available Operations by Category

### Generate Operations
- `generate-segment-script` - Generate podcast segment scripts
- `generate-ad-script` - Generate advertisement copy
- `generate-promo-script` - Generate promotional content
- `generate-cta-script` - Generate call-to-action scripts
- `generate-outro-script` - Generate outro scripts
- `generate-coldopen-script` - Generate cold open scripts
- `generate-tease-script` - Generate tease/teaser scripts
- `generate-episode-description` - Generate episode descriptions
- `generate-segment-title` - Generate segment titles
- `generate-social-media-post` - Generate social media content

### Analyze Operations
- `analyze-script-tone` - Analyze script tone/sentiment
- `analyze-script-length` - Analyze if script matches target duration
- `analyze-script-sentiment` - Detailed sentiment analysis
- `analyze-episode-structure` - Analyze episode pacing and structure
- `analyze-pacing` - Analyze pacing issues

### Extract Operations
- `extract-keywords` - Extract keywords from content
- `extract-quotes` - Extract notable quotes
- `extract-topics` - Extract main topics/themes
- `extract-metadata` - Extract structured metadata
- `extract-timestamps` - Extract timestamp markers

### Refactor Operations
- `refactor-shorten-script` - Make script more concise
- `refactor-lengthen-script` - Expand script with more detail
- `refactor-adjust-tone` - Change tone (formal/casual/etc)
- `refactor-improve-clarity` - Improve readability
- `refactor-add-humor` - Add humorous elements

### Compose Operations
- `compose-episode-summary` - Create episode summaries
- `compose-show-notes` - Generate show notes
- `compose-newsletter` - Create newsletter content
- `compose-segment-transition` - Write transition text

## Template Variables

Prompts support template variables using `{{variable}}` syntax:

### Common Variables
- `{{title}}` - Segment/episode title
- `{{topic}}` - Main topic or subject
- `{{duration}}` - Target duration (e.g., "5:00", "3 minutes")
- `{{tone}}` - Desired tone (casual, formal, humorous)
- `{{audience}}` - Target audience description
- `{{context}}` - Additional context/background
- `{{keywords}}` - Comma-separated keywords
- `{{style}}` - Writing style preferences

### Example Prompt Template

```
Write a {{duration}} podcast script for a segment titled "{{title}}".

Topic: {{topic}}
Tone: {{tone}}
Target Audience: {{audience}}

Requirements:
- Keep it conversational and engaging
- Include {{numPoints}} main points
- End with a clear transition

Context: {{context}}
```

## Integration Checklist

To add prompt override support to an existing LLM operation:

- [ ] Identify the operation category (generate/analyze/extract/refactor/compose)
- [ ] Define a unique operation_key (e.g., `generate-my-feature`)
- [ ] List all template variables needed
- [ ] Update code to call `getLLMPrompt()` with category parameter
- [ ] Test with default prompt
- [ ] Create override in UI
- [ ] Test with override enabled
- [ ] Document variables in operation description

## Example: Adding Override Support to ContentEditor

**Current Code (without overrides):**
```javascript
async generateTestContent() {
  const prompt = `Write a test script about ${this.topic}`

  const response = await axios.post('/api/llm/generate', {
    system: 'You are a script writer',
    user: prompt
  })

  return response.data.script
}
```

**Updated Code (with override support):**
```javascript
async generateTestContent() {
  // Get prompt with override checking
  const promptData = await getLLMPrompt(
    'generate-test-script',
    {
      topic: this.topic,
      duration: this.targetDuration,
      tone: 'casual'
    },
    { category: 'generate' }
  )

  const response = await axios.post('/api/llm/generate', {
    system: promptData.systemPrompt,
    user: promptData.prompt,
    temperature: promptData.temperature
  })

  return response.data.script
}
```

**Create Override in UI:**
1. Settings → LLM Prompts
2. New Override
3. Category: `generate`
4. Operation: `generate-test-script`
5. User Prompt: `Create a {{tone}} test script about {{topic}} that runs for {{duration}}. Make it engaging and informative.`
6. Enable and Save

## Debugging

### Check if Override is Being Used

```javascript
const promptData = await getLLMPrompt('my-operation', params, { category: 'generate' })

if (promptData.overridden) {
  console.log('✅ Using custom prompt override')
  console.log('Override ID:', promptData.overrideId)
  console.log('Notes:', promptData.overrideNotes)
} else {
  console.log('⚠️ Using default prompt (no override found)')
}
```

### Common Issues

**Override not applying:**
- Verify `is_enabled` is `true` in database
- Check category is passed to `getLLMPrompt()`
- Check operation_key matches exactly (case-sensitive)
- Clear cache: `clearPromptOverridesCache()`

**Variables not substituting:**
- Ensure variable names match exactly: `{{topic}}` not `{{Topic}}`
- Check variables are passed in params object
- Variables are case-sensitive

## Backend Helper Function

If you need to add a backend helper to fetch overrides:

```python
# app/prompts_router.py (add this function)

async def get_prompt_override(category: str, operation_key: str, db: Session):
    """Helper function to get enabled prompt override"""
    query = text("""
        SELECT * FROM prompt_overrides
        WHERE category = :category
        AND operation_key = :operation_key
        AND is_enabled = TRUE
    """)

    result = db.execute(query, {
        "category": category,
        "operation_key": operation_key
    })

    return result.first()
```

## Next Steps

1. **Audit Existing LLM Calls**: Find where your app makes LLM API calls
2. **Add Override Support**: Update to use `getLLMPrompt()` with category
3. **Create Overrides**: Use UI to customize prompts for your workflow
4. **Test Thoroughly**: Verify overrides work as expected
5. **Document Variables**: Keep track of what variables each operation expects
