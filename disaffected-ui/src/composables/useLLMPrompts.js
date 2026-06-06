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
    version: '2.0',
    description: 'Generates a short broadcast slug (2-4 words) for a segment from its title + script body. If the current slug is 5+ words it is included so the model shortens it.',
    lastModified: '2026-06-06',
    temperature: 0.3,
    maxTokens: 500,
    systemPrompt: '',

    // Mirrors the backend default in app/services/slug_gen_service.py
    // (DEFAULT_SLUG_PROMPT). Keep them in sync. Variables: show_name,
    // segment_title, segment_content, has_long_slug (bool), long_slug.
    template: (params) => {
      const showName = params.show_name || 'Disaffected'
      const title = params.segment_title || ''
      const content = params.segment_content || ''
      const longBlock = params.has_long_slug
        ? `The current slug is too long for broadcast: "${params.long_slug || ''}"\nGenerate a SHORTER replacement.\n`
        : ''
      return `You are naming a broadcast segment with a short slug for a rundown.

Show: ${showName}
Segment title: ${title}
${longBlock}Segment content:
${content}

Write a slug that:
- is 2 to 4 words MAX (prefer 2 or 3 words),
- captures the core topic of the segment,
- is broadcast-friendly and easy to say,
- contains no punctuation other than spaces between words.

Output ONLY the slug words, nothing else. No quotes, no preamble, no explanation.
/no_think`
    }
  },

  // ========================================
  // Segment / Script Generation Prompts
  // ========================================
  // These power the Ctrl+Alt+Shift+[1-9] "generate N paragraphs into the
  // current segment" feature (ContentEditor.generateTestSegment). The keypress
  // number is the {paragraphs} param. Editable + overridable via the Prompt
  // Manager (category 'generate'); the templates below are the default fallback.
  // Variables: paragraphs, duration, segmentType, upcomingSegments.

  'generate-segment-script': {
    version: '1.0',
    description: 'Generates a standard podcast segment of N paragraphs for the current rundown item (Ctrl+Alt+Shift+N).',
    lastModified: '2026-06-06',
    temperature: 0.7,
    maxTokens: 2000,
    systemPrompt: 'You are a broadcast script writer. Write naturally and conversationally.',
    template: (params) => {
      const { paragraphs = 3, duration = '3', slug = '', title = '', currentScript = '', otherSegments = '' } = params
      const titleLine = title ? `\nSegment title: ${title}` : ''
      const slugLine = slug ? `\nSegment slug: ${slug}` : ''
      const currentBlock = currentScript
        ? `\n\nThis segment's current script (continue/expand it; do not repeat it verbatim):\n${currentScript}`
        : ''
      return `RUNDOWN ITEM TYPE DEFINITIONS:
- Cold Open: Opening hook before any intro/music. Grabs attention instantly. 30-90 seconds.
- Tease: Preview of upcoming segments. Builds curiosity. Brief and energetic.
- Segment: Main content blocks. In-depth discussion, analysis, storytelling. Conversational. 5-15 minutes.

YOU ARE WRITING: SEGMENT${titleLine}${slugLine}

Write a ${duration}-minute podcast segment for a true crime podcast that examines manipulation tactics and abuse dynamics common to Cluster B personality disorders (narcissistic, borderline, antisocial, histrionic).${currentBlock}${otherSegments}

Write ${paragraphs} paragraphs.

Style requirements:
- Speak directly to podcast listeners in a conversational, engaging tone
- Use real psychological concepts but fictional case examples
- Include specific manipulation tactics (gaslighting, love-bombing, triangulation, DARVO, hoovering)
- Reference clinical patterns while remaining accessible
- Maintain journalistic credibility and empathy for victims
- DO NOT use real names or identify real cases

CRITICAL FORMATTING:
- Separate each paragraph with TWO newlines (blank line between paragraphs)
- Plain paragraph text, ready to paste into script. No titles, no metadata.

DO NOT include any introductory text like "Here is the podcast segment" - start IMMEDIATELY with the first paragraph of actual content.

Generate the segment now:`
    }
  },

  'generate-tease-script': {
    version: '1.0',
    description: 'Generates a tease/preview of N paragraphs that previews upcoming segments (Ctrl+Alt+Shift+N on a tease).',
    lastModified: '2026-06-06',
    temperature: 0.7,
    maxTokens: 2000,
    systemPrompt: 'You are a broadcast script writer. Write naturally and conversationally.',
    template: (params) => {
      const { paragraphs = 3, duration = '1', upcomingSegments = '', otherSegments = '', title = '' } = params
      const titleLine = title ? ` (titled "${title}")` : ''
      // Prefer the tease-specific upcoming list; fall back to the full other-segments list.
      const context = upcomingSegments || otherSegments
      return `YOU ARE WRITING: TEASE${titleLine}

Write a ${duration}-minute podcast tease/preview for a true crime podcast that examines manipulation tactics and abuse dynamics common to Cluster B personality disorders (narcissistic, borderline, antisocial, histrionic).

This tease should hook listeners and preview what's coming up in the show.${context}

Write ${paragraphs} short, punchy paragraphs that build anticipation.

Style requirements:
- Create urgency and intrigue
- Tease topics without spoiling details
- Use vivid, compelling language
- Keep it brief and energetic

CRITICAL FORMATTING:
- Separate each paragraph with TWO newlines (blank line between paragraphs)
- Plain paragraph text, ready to paste into script. No titles, no metadata.

DO NOT include any introductory text like "Here is the tease" - start IMMEDIATELY with the first paragraph of actual content.

Generate the tease now:`
    }
  },

  'generate-coldopen-script': {
    version: '1.0',
    description: 'Generates a cold-open hook of N paragraphs for the current rundown item (Ctrl+Alt+Shift+N on a cold open).',
    lastModified: '2026-06-06',
    temperature: 0.8,
    maxTokens: 2000,
    systemPrompt: 'You are a broadcast script writer. Write naturally and conversationally.',
    template: (params) => {
      const { paragraphs = 2, duration = '1', otherSegments = '', title = '' } = params
      const titleLine = title ? ` (titled "${title}")` : ''
      return `YOU ARE WRITING: COLD OPEN${titleLine}

Write a ${duration}-minute cold open for a true crime podcast that examines manipulation tactics and abuse dynamics common to Cluster B personality disorders (narcissistic, borderline, antisocial, histrionic).

A cold open should immediately grab attention with a compelling hook - a powerful question, shocking statement, or intriguing scenario.${otherSegments}

Write ${paragraphs} paragraphs.

Style requirements:
- Start with maximum impact - hook listeners instantly
- Create immediate tension or curiosity
- Use vivid, cinematic language
- Set the tone for the episode
- Don't explain everything - leave them wanting more

CRITICAL FORMATTING:
- Separate each paragraph with TWO newlines (blank line between paragraphs)
- Plain paragraph text, ready to paste into script. No titles, no metadata.

DO NOT include any introductory text - start IMMEDIATELY with the hook.

Generate the cold open now:`
    }
  },

  // ========================================
  // Multi-select "Modify with AI" Prompt
  // ========================================
  // Powers the multi-select toolbar's Modify with AI. The whole script is sent
  // as context (line-numbered) but only the SELECTED lines are modified per the
  // user's instruction/quick-action; the model returns the FULL reworked script
  // which replaces the current one (one undo step). Editable/overridable via the
  // Prompt Manager (category 'modify'). Variables: fullSegment, selectedText,
  // selectedLineNumbers, instruction.
  'modify-blocks': {
    version: '1.0',
    description: 'Modify the selected lines of a script per an instruction, returning the whole reworked script. Powers multi-select Modify with AI.',
    lastModified: '2026-06-06',
    temperature: 0.5,
    maxTokens: 4000,
    systemPrompt: 'You are a careful broadcast script editor. You make ONLY the requested change to the specified lines and return the entire script otherwise unchanged.',
    template: (params) => {
      const { fullSegment = '', selectedText = '', selectedLineNumbers = '', instruction = '' } = params
      return `You are editing a broadcast script. Below is the FULL script with line numbers (for context), then the SELECTED lines to modify, then the instruction.

Modify ONLY the selected lines per the instruction. Leave every other line EXACTLY as written. Then return the ENTIRE script (all lines, in order) with only those changes applied.

INSTRUCTION: ${instruction}

FULL SCRIPT (line-numbered, for context only — do not output the numbers):
${fullSegment}

SELECTED LINES TO MODIFY (lines ${selectedLineNumbers}):
${selectedText}

Return the COMPLETE rewritten script as plain text, with paragraphs separated by a blank line. Do NOT include line numbers, do NOT add any preamble or commentary, and do NOT wrap the output in code fences.`
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

      // Propagate the override's model parameters so callers actually honor the
      // temperature / max_tokens / model the user set in the Prompt Manager.
      // (== null check: 0 is a valid temperature, so only skip null/undefined.)
      if (override.temperature != null) result.temperature = override.temperature
      if (override.max_tokens != null) result.maxTokens = override.max_tokens
      if (override.suggested_service) result.suggestedService = override.suggested_service
      if (override.suggested_model) result.suggestedModel = override.suggested_model

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
