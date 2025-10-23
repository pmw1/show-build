# LLM Prompt Management System

**Version**: 1.0
**Status**: ✅ Production Ready
**File**: `/disaffected-ui/src/composables/useLLMPrompts.js`

---

## Overview

The LLM Prompt Management System provides **centralized storage and version control** for all LLM prompts used in Show-Build. This separates prompt engineering from application logic, making it easy to:

- **Fine-tune prompts** without touching component code
- **A/B test** different prompt variations
- **Version control** prompts with metadata
- **Reuse** common prompts across components
- **Document** prompt purpose and parameters

---

## Architecture

```
Component/Composable
    ↓
getLLMPrompt('prompt-id', params)
    ↓
useLLMPrompts.js (Prompt Registry)
    ↓
Rendered Prompt + Metadata
    ↓
useLLM.smartCall() or llmState.withLLM()
    ↓
LLM Service (Ollama/OpenAI/etc.)
```

---

## Usage

### Basic Usage

```javascript
import { getLLMPrompt } from '@/composables/useLLMPrompts'
import { useLLM } from '@/composables/useLLM'

const { smartCall } = useLLM()

// Get prompt with parameters
const promptConfig = getLLMPrompt('fsq-split-analysis', {
  quote: 'Long quote text here...',
  maxLines: 5,
  charsPerLine: 50,
  minSecondScreen: 80
})

// Use with LLM
const result = await smartCall(promptConfig.prompt, {
  temperature: promptConfig.temperature,
  max_tokens: promptConfig.maxTokens,
  systemPrompt: promptConfig.systemPrompt
})
```

### With Universal LLM Framework

```javascript
import { getLLMPrompt } from '@/composables/useLLMPrompts'
import { useLLMState } from '@/composables/useLLMState'

const llmState = useLLMState()

const result = await llmState.withLLM(
  'field',
  'quote-field',
  'analyzing',
  async () => {
    const promptConfig = getLLMPrompt('fsq-split-analysis', { quote, maxLines })
    return await smartCall(promptConfig.prompt, {
      temperature: promptConfig.temperature,
      systemPrompt: promptConfig.systemPrompt
    })
  },
  {
    notify: true,
    notificationTitle: 'Quote Analysis'
  }
)
```

---

## Available Prompts

### FSQ (Full-Screen Quote) Prompts

#### `fsq-split-analysis`
**Purpose**: Analyzes FSQ quotes and determines optimal split strategy
**Version**: 2.1
**Temperature**: 0.2 (precise, consistent)
**Parameters**:
- `quote` (required): Quote text to analyze
- `maxLines`: Max lines per screen (default: 5)
- `charsPerLine`: Characters per line (default: 50)
- `fontSize`: Font size (default: '19px')
- `minSecondScreen`: Minimum chars for second screen (default: 80)
- `splitStrategy`: Split strategy (default: 'smart')
- `balanceThresholdPercent`: Balance threshold % (default: 30)
- `preferSentenceBoundaries`: Prefer sentence endings (default: true)
- `allowMidSentenceSplit`: Allow mid-sentence splits (default: false)

**Example**:
```javascript
const config = getLLMPrompt('fsq-split-analysis', {
  quote: 'A very long quote that needs to be split...',
  maxLines: 5,
  charsPerLine: 50
})
```

#### `fsq-nested-quotes`
**Purpose**: Normalizes nested quotes within quote text
**Version**: 1.0
**Temperature**: 0.3
**Parameters**:
- `quoteText` (required): Quote text with nested quotes

---

### Content Generation Prompts

#### `wpm-script-generator`
**Purpose**: Generates natural broadcast scripts for WPM testing
**Version**: 1.0
**Temperature**: 0.7 (creative)
**Parameters**:
- `wordCount`: Target word count (default: 200)
- `topic`: Topic or theme (default: 'current events')

**Example**:
```javascript
const config = getLLMPrompt('wpm-script-generator', {
  wordCount: 250,
  topic: 'technology trends'
})
```

#### `segment-title-generator`
**Purpose**: Generates compelling segment titles from content
**Version**: 1.0
**Temperature**: 0.6
**Parameters**:
- `content` (required): Segment content to analyze
- `maxLength`: Maximum title length (default: 60)

#### `slug-generator`
**Purpose**: Generates URL-safe slugs from titles or content
**Version**: 1.0
**Temperature**: 0.1 (very deterministic)
**Parameters**:
- `text` (required): Text to convert to slug
- `maxLength`: Maximum slug length (default: 50)

---

### Analysis & Enhancement Prompts

#### `script-analyzer`
**Purpose**: Analyzes script content for readability and broadcast suitability
**Version**: 1.0
**Temperature**: 0.4
**Parameters**:
- `script` (required): Script content to analyze
- `targetDuration`: Target duration in seconds
- `targetWPM`: Target words per minute (default: 150)

**Returns**: JSON with wordCount, estimatedDuration, readabilityScore, issues, suggestions

#### `cue-description-generator`
**Purpose**: Generates descriptions for cue blocks
**Version**: 1.0
**Temperature**: 0.5
**Parameters**:
- `cueType` (required): Type of cue (FSQ, SOT, etc.)
- `metadata` (required): Cue metadata object

---

## Prompt Registry Structure

Each prompt in the registry has:

```javascript
'prompt-id': {
  version: '1.0',                    // Semantic versioning
  description: 'What this prompt does',
  lastModified: '2025-10-09',        // Last update date
  temperature: 0.2,                  // Default LLM temperature
  maxTokens: 1000,                   // Maximum response tokens
  systemPrompt: 'System message',    // System/role prompt
  template: (params) => {            // Template function
    return `Rendered prompt using ${params.foo}`
  }
}
```

---

## Helper Functions

### `listLLMPrompts()`
Lists all available prompts with metadata.

```javascript
import { listLLMPrompts } from '@/composables/useLLMPrompts'

const prompts = listLLMPrompts()
// [
//   { id: 'fsq-split-analysis', version: '2.1', description: '...', lastModified: '2025-10-09' },
//   { id: 'wpm-script-generator', version: '1.0', description: '...', lastModified: '2025-10-09' }
// ]
```

### `getPromptMetadata(promptId)`
Gets prompt metadata without rendering template.

```javascript
import { getPromptMetadata } from '@/composables/useLLMPrompts'

const metadata = getPromptMetadata('fsq-split-analysis')
// {
//   id: 'fsq-split-analysis',
//   version: '2.1',
//   description: 'Analyzes FSQ quotes...',
//   lastModified: '2025-10-09',
//   temperature: 0.2,
//   maxTokens: 1000,
//   systemPrompt: '...'
// }
```

### `updatePromptTemplate(promptId, newTemplate)`
⚠️ **Development only** - Updates prompt template at runtime (not persisted).

```javascript
import { updatePromptTemplate } from '@/composables/useLLMPrompts'

updatePromptTemplate('fsq-split-analysis', (params) => {
  return `New experimental prompt: ${params.quote}`
})
```

---

## Adding New Prompts

1. **Open** `useLLMPrompts.js`
2. **Add** to `PROMPTS` registry:

```javascript
'my-new-prompt': {
  version: '1.0',
  description: 'What this prompt does',
  lastModified: '2025-10-09',
  temperature: 0.5,
  maxTokens: 500,
  systemPrompt: 'You are a helpful assistant.',

  template: (params) => {
    const { requiredParam, optionalParam = 'default' } = params

    return `Your prompt template here.

Required: ${requiredParam}
Optional: ${optionalParam}

Return your response:`
  }
}
```

3. **Document** in this file under appropriate section
4. **Use** in components via `getLLMPrompt('my-new-prompt', params)`

---

## Migrating Existing Prompts

### Before (Scattered in Components)

```javascript
// WPMMeasurementTool.vue
const prompt = `Generate a natural, conversational broadcast script suitable for reading aloud.
The script should be between 150-250 words and cover a current events topic or interesting story.
Write in a friendly, engaging tone as if speaking directly to viewers.
Do not include any stage directions, just the spoken text.`

const response = await smartCall(prompt, {
  preferredService: 'ollama',
  preferredModel: 'qwen2.5-coder:7b'
})
```

### After (Centralized)

```javascript
// WPMMeasurementTool.vue
import { getLLMPrompt } from '@/composables/useLLMPrompts'

const promptConfig = getLLMPrompt('wpm-script-generator', {
  wordCount: 200,
  topic: 'current events'
})

const response = await smartCall(promptConfig.prompt, {
  preferredService: 'ollama',
  preferredModel: 'qwen2.5-coder:7b',
  temperature: promptConfig.temperature
})
```

**Benefits**:
- Prompt can be updated without touching component
- Version control and documentation
- Reusable across multiple components
- Easier A/B testing

---

## Prompt Engineering Workflow

### 1. Test in UI
Use the component as normal and observe LLM behavior.

### 2. Iterate in Code
Edit the prompt template in `useLLMPrompts.js`:

```javascript
template: (params) => {
  return `Updated prompt with better instructions...`
}
```

### 3. Hot Reload
Save file → Frontend hot reloads → Test immediately

### 4. Version Bump
When satisfied, update version:

```javascript
version: '2.2', // Was 2.1
lastModified: '2025-10-09'
```

### 5. Document Changes
Add comments or update this doc with what changed and why.

---

## A/B Testing Prompts

Create variant prompts for testing:

```javascript
'fsq-split-analysis': { /* Original prompt */ },

'fsq-split-analysis-v2': {
  version: '2.2-experimental',
  description: 'Testing simplified instructions',
  // ... same config but different template
}
```

Use feature flags or random selection:

```javascript
const variant = Math.random() > 0.5 ? 'fsq-split-analysis' : 'fsq-split-analysis-v2'
const promptConfig = getLLMPrompt(variant, params)
```

Track results and promote winner to production.

---

## Best Practices

### 1. **Clear Parameter Documentation**
Document all parameters in prompt description and this file.

### 2. **Sensible Defaults**
Provide defaults for optional parameters:
```javascript
const { maxLength = 50, temperature = 0.5 } = params
```

### 3. **Version Incrementally**
- Patch (1.0.1): Minor wording changes
- Minor (1.1): New parameters or instructions
- Major (2.0): Complete prompt rewrite

### 4. **Include Examples**
When possible, include few-shot examples in prompts.

### 5. **Set Appropriate Temperature**
- 0.0-0.2: Deterministic (analysis, extraction)
- 0.3-0.5: Balanced (description, formatting)
- 0.6-0.8: Creative (content generation)
- 0.9-1.0: Very creative (brainstorming)

### 6. **Validate Output Format**
If expecting JSON, validate and provide fallback:
```javascript
try {
  return JSON.parse(result)
} catch (e) {
  console.error('Invalid JSON from LLM')
  return fallbackValue
}
```

---

## Future Enhancements

### Database-Backed Prompts
Store prompts in PostgreSQL for:
- Live editing via admin UI
- User-specific prompt customization
- Rollback to previous versions
- Analytics on prompt performance

### Prompt Performance Metrics
Track for each prompt:
- Average response time
- Success rate (valid output)
- User satisfaction (implicit/explicit)
- Token usage

### Multi-Language Support
Template prompts for different languages:
```javascript
getLLMPrompt('fsq-split-analysis', params, { language: 'es' })
```

### Prompt Marketplace
Share and discover community prompts for common tasks.

---

## Related Documentation

- **Universal LLM Framework**: `/UNIVERSAL_LLM_FRAMEWORK_UFDP.md`
- **LLM Routing**: `/docs/LLM_ROUTING_SYSTEM.md`
- **Composables Guide**: `/docs/COMPOSABLES.md`

---

**Created**: 2025-10-09
**Author**: Claude Code
**Status**: Production - Ready for Migration
