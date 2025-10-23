/**
 * LLM Prompt Management System
 *
 * Centralized repository for all LLM prompts used throughout Show-Build.
 * This allows for easy prompt engineering, A/B testing, and version control.
 *
 * Usage:
 * import { getLLMPrompt } from '@/composables/useLLMPrompts'
 * const prompt = getLLMPrompt('fsq-split-analysis', { quote, maxLines, ... })
 */

/**
 * Prompt registry - all prompts stored here with metadata
 */
const PROMPTS = {
  // ========================================
  // FSQ (Full-Screen Quote) Prompts
  // ========================================

  'fsq-split-analysis': {
    version: '2.1',
    description: 'Analyzes FSQ quotes and determines optimal split strategy',
    lastModified: '2025-10-09',
    temperature: 0.2,
    maxTokens: 1000,
    systemPrompt: 'You are a precise quote layout analyzer. Return only valid JSON arrays with no additional text.',

    template: (params) => {
      const {
        quote,
        maxLines = 5,
        charsPerLine = 50,
        fontSize = '19px',
        minSecondScreen = 80,
        splitStrategy = 'smart',
        balanceThresholdPercent = 30,
        preferSentenceBoundaries = true,
        allowMidSentenceSplit = false
      } = params

      const maxCharsScreen1 = maxLines * charsPerLine
      const balanceThreshold = maxCharsScreen1 + Math.round(minSecondScreen * (balanceThresholdPercent / 100))

      return `You are an FSQ (Full Screen Quote) layout analyzer with SMART SPLIT logic to prevent orphan text.

DISPLAY CONSTRAINTS:
- Screen: 1920x1080 full screen
- Max lines for Screen 1: ${maxLines}
- Characters per line: ~${charsPerLine}
- Max characters for Screen 1: ${maxCharsScreen1}
- MINIMUM characters for Screen 2: ${minSecondScreen} (prevents orphans)
- Balance threshold: ${balanceThreshold} chars
- Font size: ${fontSize}

QUOTE TO ANALYZE (${quote.length} characters):
"${quote}"

SMART SPLIT STRATEGY: "${splitStrategy}"

🔍 DECISION LOGIC:

**STEP 1: Length Analysis**
- Quote length: ${quote.length} chars
- Max Screen 1: ${maxCharsScreen1} chars
- Balance threshold: ${balanceThreshold} chars

**STEP 2: Determine Split Behavior**

A) If ${quote.length} ≤ ${maxCharsScreen1}:
   → SINGLE SCREEN - Quote fits comfortably
   → Return: ["original quote as-is"]

B) If ${quote.length} is ${maxCharsScreen1 + 1} to ${balanceThreshold}:
   → BALANCED SPLIT - In the "gray zone"
   → Splitting at ${maxCharsScreen1} would leave only ${quote.length - maxCharsScreen1} chars on Screen 2
   → This is LESS than minimum (${minSecondScreen}), creating orphan text!
   → SOLUTION: Split near the MIDDLE (~${Math.floor(quote.length / 2)} chars) for balanced screens

C) If ${quote.length} > ${balanceThreshold}:
   → STANDARD SPLIT - Quote is long enough
   → Split at ~${maxCharsScreen1} chars
   → Remainder will be ≥ ${minSecondScreen} chars (adequate for Screen 2)

**STEP 3: Find Split Point** ${preferSentenceBoundaries ? '(Prefer Sentence Boundaries)' : ''}

Priority order for finding split point:
1. ${preferSentenceBoundaries ? 'Sentence endings (. ! ?) within ±50 chars of target' : 'Target position'}
2. ${allowMidSentenceSplit ? 'Clause breaks (, ; -) within ±30 chars if no sentence boundary' : 'Skip mid-sentence'}
3. Word boundaries (spaces) within ±20 chars
4. Exact position (last resort)

**VALIDATION RULES:**
- ⚠️ **NO OVERLAPPING SEGMENTS** - Each word should appear in EXACTLY ONE segment
- ⚠️ **NO DUPLICATE TEXT** - Do not repeat any portion of the quote across segments
- ⚠️ **CLEAN CUTS** - Split the quote, don't copy it
- Each segment must be independently readable
- NO orphan text (Screen 2 must be ≥ ${minSecondScreen} chars)
- Preserve original meaning and tone
- Each segment should be substantial

**WRONG EXAMPLE (DO NOT DO THIS):**
❌ WRONG:
[
  "The fundamental problem with modern technology isn't that it's too complex...",
  "that we've created systems that prioritize convenience over understanding..."
]
This is WRONG because "that we've created systems..." appears in BOTH segments (overlapping).

**CORRECT EXAMPLE:**
✅ CORRECT:
[
  "The fundamental problem with modern technology isn't that it's too complex or too simple, but rather that we've created systems that prioritize convenience over understanding.",
  "We've built a world where people can accomplish incredible things without having the slightest idea how any of it works..."
]
This is CORRECT because each segment contains unique, non-overlapping text.

**OUTPUT FORMAT:**
Return ONLY a valid JSON array of strings, no explanation.

Examples:
- 220 chars (fits): ["The entire quote stays together."]
- 280 chars (gray zone): ["First half ~140 chars.", "Second half ~140 chars."] ← BALANCED, NO OVERLAP
- 400 chars (long): ["First screen ~${maxCharsScreen1} chars.", "Second screen ~${400 - maxCharsScreen1} chars."] ← STANDARD, NO OVERLAP

⚠️ CRITICAL:
1. If split would create orphan (Screen 2 < ${minSecondScreen} chars), BALANCE the split instead!
2. NEVER repeat or overlap text between segments - split the quote cleanly!

Return ONLY the JSON array. No markdown, no explanation, just the array.`
    }
  },

  'fsq-nested-quotes': {
    version: '1.0',
    description: 'Normalizes nested quotes within quote text',
    lastModified: '2025-10-09',
    temperature: 0.3,
    maxTokens: 500,
    systemPrompt: 'You are a quote formatting assistant. Return only the corrected quote text.',

    template: (params) => {
      const { quoteText } = params

      return `Fix the nested quote formatting in this text. Replace straight quotes with proper curly quotes where appropriate.

Rules:
- Outer quotes: Use straight quotes (") or leave as-is
- Inner quotes: Use curly quotes (" and ")
- Preserve all other punctuation and formatting
- Return ONLY the corrected text, no explanation

Quote to fix:
${quoteText}

Return the corrected quote:`
    }
  },

  // ========================================
  // Content Generation Prompts
  // ========================================

  'wpm-script-generator': {
    version: '1.0',
    description: 'Generates natural broadcast scripts for WPM testing',
    lastModified: '2025-10-09',
    temperature: 0.7,
    maxTokens: 500,
    systemPrompt: 'You are a broadcast script writer. Write naturally and conversationally.',

    template: (params) => {
      const { wordCount = 200, topic = 'current events' } = params

      return `Generate a natural, conversational broadcast script suitable for reading aloud.
The script should be between 150-250 words and cover a ${topic} topic or interesting story.
Write in a friendly, engaging tone as if speaking directly to viewers.
Do not include any stage directions, just the spoken text.

Target word count: ~${wordCount} words

Return the script:`
    }
  },

  'segment-title-generator': {
    version: '1.0',
    description: 'Generates compelling segment titles from content',
    lastModified: '2025-10-09',
    temperature: 0.6,
    maxTokens: 100,
    systemPrompt: 'You are a broadcast segment title writer. Create concise, compelling titles.',

    template: (params) => {
      const { content, maxLength = 60 } = params

      return `Generate a compelling title for this broadcast segment.

Requirements:
- Maximum ${maxLength} characters
- Engaging and descriptive
- Suitable for broadcast rundown
- No punctuation at the end

Segment content:
${content.substring(0, 500)}...

Return ONLY the title:`
    }
  },

  'slug-generator': {
    version: '1.0',
    description: 'Generates URL-safe slugs from titles or content',
    lastModified: '2025-10-09',
    temperature: 0.1,
    maxTokens: 50,
    systemPrompt: 'You are a slug generator. Create lowercase, hyphenated identifiers.',

    template: (params) => {
      const { text, maxLength = 50 } = params

      return `Generate a URL-safe slug from this text.

Rules:
- Lowercase only
- Hyphens for spaces
- No special characters
- Maximum ${maxLength} characters
- No leading/trailing hyphens

Text: "${text}"

Return ONLY the slug:`
    }
  },

  // ========================================
  // Analysis & Enhancement Prompts
  // ========================================

  'script-analyzer': {
    version: '1.0',
    description: 'Analyzes script content for readability and broadcast suitability',
    lastModified: '2025-10-09',
    temperature: 0.4,
    maxTokens: 800,
    systemPrompt: 'You are a broadcast script analyst. Provide actionable feedback.',

    template: (params) => {
      const { script, targetDuration, targetWPM = 150 } = params
      const targetWords = Math.floor((targetDuration / 60) * targetWPM)

      return `Analyze this broadcast script for readability and timing.

Script:
${script}

Target duration: ${targetDuration} seconds
Target words: ~${targetWords} (at ${targetWPM} WPM)

Provide analysis in JSON format:
{
  "wordCount": <number>,
  "estimatedDuration": <seconds>,
  "readabilityScore": <1-10>,
  "issues": [
    {"type": "timing|readability|style", "description": "...", "severity": "low|medium|high"}
  ],
  "suggestions": [
    "Actionable suggestion 1",
    "Actionable suggestion 2"
  ]
}

Return ONLY valid JSON:`
    }
  },

  'cue-description-generator': {
    version: '1.0',
    description: 'Generates descriptions for cue blocks',
    lastModified: '2025-10-09',
    temperature: 0.5,
    maxTokens: 150,
    systemPrompt: 'You are a broadcast cue descriptor. Be concise and technical.',

    template: (params) => {
      const { cueType, metadata } = params

      return `Generate a concise description for this ${cueType} cue.

Cue metadata:
${JSON.stringify(metadata, null, 2)}

Requirements:
- Maximum 100 characters
- Technical and descriptive
- Suitable for rundown display

Return ONLY the description:`
    }
  },

  // ========================================
  // Future Prompts (Placeholder)
  // ========================================

  'guest-bio-generator': {
    version: '0.1',
    description: 'Generates guest biography from basic info (not yet implemented)',
    lastModified: '2025-10-09',
    temperature: 0.6,
    maxTokens: 300,
    systemPrompt: 'You are a biography writer for broadcast introductions.',

    template: () => {
      return 'NOT YET IMPLEMENTED'
    }
  }
}

/**
 * Cache for database prompt overrides
 * Refreshed every 60 seconds to avoid excessive API calls
 */
let promptOverridesCache = null
let promptOverridesCacheTime = 0
const CACHE_TTL = 60000 // 60 seconds

/**
 * Fetch prompt overrides from database (with caching)
 */
async function fetchPromptOverrides() {
  const now = Date.now()

  // Return cached overrides if still valid
  if (promptOverridesCache && (now - promptOverridesCacheTime) < CACHE_TTL) {
    return promptOverridesCache
  }

  try {
    const axios = (await import('axios')).default
    const response = await axios.get('/api/prompts/overrides', {
      params: { enabled_only: true }
    })

    if (response.data.success) {
      // Convert to lookup map: category.operation_key -> override
      const overridesMap = {}
      response.data.overrides.forEach(override => {
        const key = `${override.category}.${override.operation_key}`
        overridesMap[key] = override
      })

      promptOverridesCache = overridesMap
      promptOverridesCacheTime = now
      console.log(`✅ Loaded ${response.data.overrides.length} prompt overrides from database`)
      return overridesMap
    }
  } catch (error) {
    console.warn('⚠️ Failed to load prompt overrides, using defaults:', error.message)
  }

  return {}
}

/**
 * Clear prompt overrides cache (useful after creating/updating overrides)
 */
export function clearPromptOverridesCache() {
  promptOverridesCache = null
  promptOverridesCacheTime = 0
  console.log('🔄 Prompt overrides cache cleared')
}

/**
 * Get an LLM prompt by ID with parameters
 * Now checks database for overrides before using defaults
 *
 * @param {string} promptId - Prompt identifier from PROMPTS registry
 * @param {object} params - Parameters to inject into template
 * @param {object} options - Additional options
 * @param {string} options.category - Category for database lookup (generate, analyze, etc.)
 * @returns {object} Prompt configuration with rendered template
 */
export async function getLLMPrompt(promptId, params = {}, options = {}) {
  const promptConfig = PROMPTS[promptId]

  if (!promptConfig) {
    console.error(`❌ Unknown prompt ID: ${promptId}`)
    throw new Error(`Prompt not found: ${promptId}`)
  }

  // Render template with parameters (default prompt)
  const renderedPrompt = promptConfig.template(params)

  // Build response object with defaults
  let result = {
    prompt: renderedPrompt,
    systemPrompt: promptConfig.systemPrompt,
    temperature: promptConfig.temperature,
    maxTokens: promptConfig.maxTokens,
    version: promptConfig.version,
    description: promptConfig.description,
    overridden: false
  }

  // Check for database override
  if (options.category) {
    const overrides = await fetchPromptOverrides()
    const overrideKey = `${options.category}.${promptId}`
    const override = overrides[overrideKey]

    if (override) {
      console.log(`🎯 Using database override for ${overrideKey}`)

      // Apply overrides (only if provided)
      if (override.system_prompt) {
        result.systemPrompt = override.system_prompt
      }

      if (override.user_prompt_template) {
        // Simple template variable substitution
        let customPrompt = override.user_prompt_template
        Object.keys(params).forEach(key => {
          const regex = new RegExp(`{{${key}}}`, 'g')
          customPrompt = customPrompt.replace(regex, params[key])
        })
        result.prompt = customPrompt
      }

      result.overridden = true
      result.overrideId = override.id
      result.overrideNotes = override.notes
    }
  }

  return result
}

/**
 * List all available prompts
 *
 * @returns {Array} Array of prompt metadata
 */
export function listLLMPrompts() {
  return Object.keys(PROMPTS).map(id => ({
    id,
    version: PROMPTS[id].version,
    description: PROMPTS[id].description,
    lastModified: PROMPTS[id].lastModified
  }))
}

/**
 * Get prompt metadata without rendering
 *
 * @param {string} promptId - Prompt identifier
 * @returns {object} Prompt metadata (version, description, etc.)
 */
export function getPromptMetadata(promptId) {
  const promptConfig = PROMPTS[promptId]

  if (!promptConfig) {
    return null
  }

  return {
    id: promptId,
    version: promptConfig.version,
    description: promptConfig.description,
    lastModified: promptConfig.lastModified,
    temperature: promptConfig.temperature,
    maxTokens: promptConfig.maxTokens,
    systemPrompt: promptConfig.systemPrompt
  }
}

/**
 * Update a prompt's template (for live prompt engineering)
 * WARNING: Changes are not persisted - only for testing/development
 *
 * @param {string} promptId - Prompt identifier
 * @param {function} newTemplate - New template function
 */
export function updatePromptTemplate(promptId, newTemplate) {
  if (!PROMPTS[promptId]) {
    throw new Error(`Prompt not found: ${promptId}`)
  }

  console.warn(`⚠️ Updating prompt template for: ${promptId} (not persisted)`)
  PROMPTS[promptId].template = newTemplate
}

export default {
  getLLMPrompt,
  listLLMPrompts,
  getPromptMetadata,
  updatePromptTemplate,
  clearPromptOverridesCache
}
