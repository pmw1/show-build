/**
 * useLLM.js - Composable for LLM API integrations
 * Supports: Ollama, OpenAI, Anthropic, Google Gemini, xAI Grok
 */

import { ref } from 'vue'
import axios from 'axios'

export function useLLM() {
  const loading = ref(false)
  const error = ref(null)

  /**
   * Get API configurations from backend
   */
  async function getApiConfigs() {
    try {
      const response = await axios.get('/api/settings/api-configs', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
        }
      })

      if (response.data.success && response.data.data) {
        return response.data.data
      }
      return null
    } catch (err) {
      console.error('Failed to load API configs:', err)
      return null
    }
  }

  /**
   * Call Ollama (local LLM via llama.cpp)
   */
  async function callOllama(prompt, model = 'llama2', options = {}) {
    try {
      const configs = await getApiConfigs()
      const ollamaConfig = configs?.preproduction?.ai_services?.ollama

      if (!ollamaConfig?.enabled) {
        throw new Error('Ollama is not enabled in settings')
      }

      const host = ollamaConfig.host || 'http://localhost:11434'

      const response = await axios.post(`${host}/api/generate`, {
        model: model,
        prompt: prompt,
        stream: false,
        options: {
          temperature: options.temperature || 0.7,
          top_p: options.top_p || 0.9,
          max_tokens: options.max_tokens || 500
        }
      })

      return response.data.response
    } catch (err) {
      console.error('Ollama API error:', err)
      throw err
    }
  }

  /**
   * Call OpenAI API
   */
  async function callOpenAI(prompt, model = 'gpt-4', options = {}) {
    try {
      const configs = await getApiConfigs()
      const openaiConfig = configs?.preproduction?.ai_services?.openai

      if (!openaiConfig?.enabled) {
        throw new Error('OpenAI is not enabled in settings')
      }

      // Enhanced logging for debugging
      console.log('🔍 OpenAI API Request:', {
        model,
        apiKeyPresent: !!openaiConfig.apiKey,
        apiKeyLength: openaiConfig.apiKey?.length,
        apiKeyPrefix: openaiConfig.apiKey?.substring(0, 10) + '...',
        enabled: openaiConfig.enabled
      })

      const response = await axios.post('https://api.openai.com/v1/chat/completions', {
        model: model,
        messages: [
          { role: 'system', content: options.systemPrompt || 'You are a helpful assistant.' },
          { role: 'user', content: prompt }
        ],
        temperature: options.temperature || 0.7,
        max_tokens: options.max_tokens || 500
      }, {
        headers: {
          'Authorization': `Bearer ${openaiConfig.apiKey}`,
          'Content-Type': 'application/json'
        }
      })

      console.log('✅ OpenAI API Success')
      return response.data.choices[0].message.content
    } catch (err) {
      console.error('❌ OpenAI API error:', {
        message: err.message,
        responseData: err.response?.data,
        status: err.response?.status,
        statusText: err.response?.statusText,
        headers: err.response?.headers
      })
      throw err
    }
  }

  /**
   * Call Anthropic Claude API
   */
  async function callAnthropic(prompt, model = 'claude-3-5-sonnet-20241022', options = {}) {
    try {
      const configs = await getApiConfigs()
      const anthropicConfig = configs?.preproduction?.ai_services?.anthropic

      if (!anthropicConfig?.enabled) {
        throw new Error('Anthropic is not enabled in settings')
      }

      // Enhanced logging for debugging
      console.log('🔍 Anthropic API Request:', {
        model,
        apiKeyPresent: !!anthropicConfig.apiKey,
        apiKeyLength: anthropicConfig.apiKey?.length,
        apiKeyPrefix: anthropicConfig.apiKey?.substring(0, 10) + '...',
        enabled: anthropicConfig.enabled
      })

      const response = await axios.post('https://api.anthropic.com/v1/messages', {
        model: model,
        max_tokens: options.max_tokens || 1024,
        messages: [
          { role: 'user', content: prompt }
        ],
        system: options.systemPrompt || 'You are a helpful assistant.'
      }, {
        headers: {
          'x-api-key': anthropicConfig.apiKey,
          'anthropic-version': '2023-06-01',
          'Content-Type': 'application/json'
        }
      })

      console.log('✅ Anthropic API Success')
      return response.data.content[0].text
    } catch (err) {
      console.error('❌ Anthropic API error:', {
        message: err.message,
        responseData: err.response?.data,
        status: err.response?.status,
        statusText: err.response?.statusText,
        headers: err.response?.headers
      })
      throw err
    }
  }

  /**
   * Call Google Gemini API
   */
  async function callGemini(prompt, model = 'gemini-2.0-flash', options = {}) {
    try {
      const configs = await getApiConfigs()
      const geminiConfig = configs?.preproduction?.ai_services?.gemini

      if (!geminiConfig?.enabled) {
        throw new Error('Gemini is not enabled in settings')
      }

      // Enhanced logging for debugging
      console.log('🔍 Gemini API Request:', {
        model,
        apiKeyPresent: !!geminiConfig.apiKey,
        apiKeyLength: geminiConfig.apiKey?.length,
        apiKeyPrefix: geminiConfig.apiKey?.substring(0, 10) + '...',
        enabled: geminiConfig.enabled
      })

      const response = await axios.post(
        `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`,
        {
          contents: [{
            parts: [{
              text: prompt
            }]
          }],
          generationConfig: {
            temperature: options.temperature || 0.7,
            maxOutputTokens: options.max_tokens || 500
          }
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'X-goog-api-key': geminiConfig.apiKey
          }
        }
      )

      console.log('✅ Gemini API Success')
      return response.data.candidates[0].content.parts[0].text
    } catch (err) {
      console.error('❌ Gemini API error:', {
        message: err.message,
        responseData: err.response?.data,
        status: err.response?.status,
        statusText: err.response?.statusText,
        headers: err.response?.headers
      })
      throw err
    }
  }

  /**
   * Call xAI Grok API
   */
  async function callGrok(prompt, model = 'grok-4-latest', options = {}) {
    try {
      const configs = await getApiConfigs()
      const grokConfig = configs?.preproduction?.ai_services?.grok

      if (!grokConfig?.enabled) {
        throw new Error('Grok is not enabled in settings')
      }

      // Enhanced logging for debugging
      console.log('🔍 Grok API Request:', {
        model,
        apiKeyPresent: !!grokConfig.apiKey,
        apiKeyLength: grokConfig.apiKey?.length,
        apiKeyPrefix: grokConfig.apiKey?.substring(0, 10) + '...',
        enabled: grokConfig.enabled
      })

      // xAI uses OpenAI-compatible API
      const response = await axios.post('https://api.x.ai/v1/chat/completions', {
        model: model,
        messages: [
          { role: 'system', content: options.systemPrompt || 'You are Grok, a helpful assistant.' },
          { role: 'user', content: prompt }
        ],
        temperature: options.temperature || 0.7,
        max_tokens: options.max_tokens || 500,
        stream: false
      }, {
        headers: {
          'Authorization': `Bearer ${grokConfig.apiKey}`,
          'Content-Type': 'application/json'
        }
      })

      console.log('✅ Grok API Success')
      return response.data.choices[0].message.content
    } catch (err) {
      console.error('❌ Grok API error:', {
        message: err.message,
        responseData: err.response?.data,
        status: err.response?.status,
        statusText: err.response?.statusText,
        headers: err.response?.headers
      })
      throw err
    }
  }

  /**
   * Get routing preferences from localStorage
   */
  function getRoutingPreferences() {
    const saved = localStorage.getItem('llm-routing-settings')
    if (saved) {
      return JSON.parse(saved)
    }
    // Optimized defaults for Show-Build with Ollama models
    return {
      routing: {
        quoteSplitting: 'ollama',      // Qwen2.5-Coder:7b - Best at JSON output
        slugGeneration: 'ollama',       // mistral:7b - Fast text transforms
        scriptSummary: 'ollama',        // llama3:latest - Balanced quality
        titleGeneration: 'ollama',      // llama3:latest - Creative + fast
        contentExpansion: 'ollama',     // llama2:13b-chat - Creative depth
        factChecking: 'ollama',         // deepseek-r1:8b - Reasoning specialist
        entityExtraction: 'ollama',     // Qwen2.5-Coder:7b - JSON output for structured data
        enableFallback: true,
        fallbackOrder: ['ollama', 'openai', 'gemini', 'grok', 'anthropic']
      },
      ollamaModels: {
        quoteSplitting: 'Qwen2.5-Coder:7b',
        slugGeneration: 'mistral:7b',
        scriptSummary: 'llama3:latest',
        titleGeneration: 'llama3:latest',
        contentExpansion: 'llama2:13b-chat',
        factChecking: 'deepseek-r1:8b',
        entityExtraction: 'Qwen2.5-Coder:7b'
      }
    }
  }

  /**
   * Smart LLM call with task-specific routing
   * @param {string} prompt - The prompt to send
   * @param {object} options - Options including taskType for routing
   */
  async function smartCall(prompt, options = {}) {
    loading.value = true
    error.value = null

    try {
      const configs = await getApiConfigs()
      const routing = getRoutingPreferences().routing

      // Determine preferred service based on task type
      let preferredService = 'auto'
      if (options.taskType) {
        const taskMap = {
          'quote-splitting': routing.quoteSplitting,
          'slug-generation': routing.slugGeneration,
          'script-summary': routing.scriptSummary,
          'title-generation': routing.titleGeneration,
          'content-expansion': routing.contentExpansion,
          'fact-checking': routing.factChecking,
          'entity-extraction': routing.entityExtraction
        }
        preferredService = taskMap[options.taskType] || 'auto'
      }

      // If specific service requested, try it first
      if (preferredService !== 'auto') {
        try {
          console.log(`🎯 Using preferred service for ${options.taskType}: ${preferredService}`)
          const result = await callSpecificService(preferredService, prompt, options)
          if (result) return result
        } catch (err) {
          console.warn(`Preferred service ${preferredService} failed, falling back...`)
          if (!routing.enableFallback) throw err
        }
      }

      // Auto routing or fallback
      const fallbackOrder = routing.enableFallback ? routing.fallbackOrder : ['ollama', 'openai', 'anthropic', 'gemini', 'grok']

      for (const service of fallbackOrder) {
        if (configs?.preproduction?.ai_services?.[service]?.enabled) {
          try {
            const result = await callSpecificService(service, prompt, options)
            if (result) return result
          } catch (err) {
            console.warn(`Service ${service} failed:`, err.message)
            continue
          }
        }
      }

      throw new Error('No LLM service is enabled. Please configure at least one AI service in Settings.')
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Call a specific LLM service by name
   */
  async function callSpecificService(service, prompt, options) {
    switch (service) {
      case 'ollama': {
        // Use task-specific Ollama model if available
        const routing = getRoutingPreferences()
        let ollamaModel = options.model

        if (options.taskType && routing.ollamaModels && routing.ollamaModels[options.taskType]) {
          ollamaModel = routing.ollamaModels[options.taskType]
          console.log(`🤖 Using Ollama (${ollamaModel}) for ${options.taskType}`)
        } else {
          console.log('🤖 Using Ollama (local)')
        }

        return await callOllama(prompt, ollamaModel, options)
      }
      case 'openai':
        return await callOpenAI(prompt, options.model, options)
      case 'anthropic':
        return await callAnthropic(prompt, options.model, options)
      case 'gemini':
        return await callGemini(prompt, options.model, options)
      case 'grok':
        return await callGrok(prompt, options.model, options)
      default:
        throw new Error(`Unknown service: ${service}`)
    }
  }

  /**
   * Split a long quote intelligently for FSQ (Full Screen Quote) display using LLM
   * Uses visual layout rules to determine if splitting is needed
   * @param {string} quote - The quote text to analyze
   * @param {object} options - Display options from generation settings
   */
  async function intelligentQuoteSplit(quote, options = {}) {
    // Get display parameters from options or use defaults
    const maxLines = options.maxLines || 4
    const charsPerLine = options.charsPerLine || 70
    const fontSize = options.fontSize || '19px'
    const maxChars = maxLines * charsPerLine

    const prompt = `You are an FSQ (Full Screen Quote) layout analyzer. Analyze this quote and determine if it needs to be split for optimal visual display.

DISPLAY CONSTRAINTS:
- Screen: 1920x1080 full screen
- Max comfortable lines: ${maxLines}
- Characters per line: ~${charsPerLine}
- Max characters per slide: ${maxChars}
- Font size: ${fontSize}

QUOTE TO ANALYZE:
"${quote}"

⚠️ CRITICAL: Only split if absolutely necessary! Preserving the quote as a single unit is PREFERRED.

DECISION RULES (apply in order):

1. CHARACTER COUNT CHECK:
   - Count total characters in quote (including spaces and punctuation)
   - If ≤ ${maxChars} chars: STOP HERE - DO NOT SPLIT
     → Return single-element array: ["original quote as-is"]
   - If > ${maxChars} chars: Splitting is required (proceed to step 2)

   IMPORTANT: If the quote fits comfortably, DO NOT split it. Unnecessary splitting reduces impact.

2. NATURAL BREAK PRIORITY (when splitting needed):
   a) FIRST CHOICE: Period/sentence boundary
      - Split at sentence end closest to ${maxChars} chars
      - Each segment should be complete thought

   b) SECOND CHOICE: Paragraph break
      - If quote has paragraphs, split between them

   c) THIRD CHOICE: Comma or semicolon
      - Split at major clause break
      - Must preserve meaning

   d) LAST RESORT: Hard split at ~50 words
      - Only if no natural breaks exist
      - Add ellipsis (...) to indicate continuation

3. VALIDATION:
   - Each segment must be independently readable
   - Each segment should fit visual constraints (≤ ${maxChars} chars)
   - Preserve original meaning and tone
   - No orphaned words (segments should be substantial)

OUTPUT FORMAT:
Return ONLY a valid JSON array of strings, no explanation.

Examples:
- Quote fits (≤${maxChars} chars): ["The entire quote stays together."]
  ✅ Correct: Single element array preserving the whole quote
  ❌ Wrong: Splitting a quote that already fits

- Quote too long (>${maxChars} chars): ["First segment ending at period.", "Second segment with rest of quote."]
  ✅ Correct: Multiple elements only when necessary

DEFAULT BEHAVIOR: When in doubt, DO NOT SPLIT. Return the original quote as a single-element array.

CRITICAL: Return ONLY the JSON array. No markdown, no explanation, just the array.`

    try {
      const result = await smartCall(prompt, {
        taskType: 'quote-splitting',
        temperature: 0.2, // Very low temperature for consistent, logical decisions
        max_tokens: 1000,
        systemPrompt: 'You are a precise quote layout analyzer. Return only valid JSON arrays with no additional text.'
      })

      // Clean up response to extract JSON
      let jsonText = result.trim()

      // Remove markdown code blocks if present
      jsonText = jsonText.replace(/```json\n?/g, '').replace(/```\n?/g, '')

      // Extract JSON array
      const jsonMatch = jsonText.match(/\[[\s\S]*\]/)
      if (jsonMatch) {
        const segments = JSON.parse(jsonMatch[0])

        // Validate that we got an array of strings
        if (Array.isArray(segments) && segments.every(s => typeof s === 'string')) {
          console.log(`📊 Quote split analysis: ${segments.length} segment(s)`)
          return segments
        }
      }

      // Fallback: return original quote as single segment
      console.warn('LLM did not return valid JSON array, using fallback')
      return [quote]
    } catch (err) {
      console.error('Failed to split quote with LLM:', err)
      // Fallback: return original quote
      return [quote]
    }
  }

  /**
   * Generate a slug from quote text using LLM
   */
  async function generateSlug(quoteText) {
    const prompt = `Generate a short, SEO-friendly slug (5-8 words max) for this quote. Use lowercase, hyphens, no special characters.

Quote: "${quoteText}"

Return ONLY the slug, nothing else.`

    try {
      const result = await smartCall(prompt, {
        taskType: 'slug-generation',
        temperature: 0.5,
        max_tokens: 50
      })

      return result.trim().toLowerCase().replace(/[^a-z0-9-\s]/g, '').replace(/\s+/g, '-')
    } catch (err) {
      console.error('Failed to generate slug with LLM:', err)
      // Fallback: use simple slugification
      return quoteText
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .substring(0, 50)
    }
  }

  /**
   * Normalize nested quotes according to English language best practices
   * Properly nests single and double quotes following AP/Chicago style
   * @param {string} quoteText - The quote text with potentially inconsistent nesting
   * @returns {string} - Properly formatted quote text
   */
  async function normalizeNestedQuotes(quoteText) {
    const prompt = `You are a professional copy editor specializing in English language typography and quotation formatting.

TASK: Fix the quotation marks in this text to follow proper English language nesting rules.

TEXT TO ANALYZE:
"${quoteText}"

RULES FOR PROPER QUOTATION NESTING:
1. American English style (AP/Chicago):
   - Outer quotes: Use double quotes (")
   - Inner quotes (quotes within quotes): Use single quotes (')
   - Example: He said "She told me 'hello' yesterday."

2. British English style (alternative):
   - Outer quotes: Use single quotes (')
   - Inner quotes: Use double quotes (")
   - Example: He said 'She told me "hello" yesterday.'

3. Consistency:
   - Pick ONE style and apply it throughout
   - Don't mix American and British styles in the same text

4. Special cases:
   - Apostrophes (possession/contractions) always use single quote (')
   - Example: "It's John's book," she said.
   - Dialogue within dialogue needs proper nesting
   - Example: "Did he say 'I won't go' or 'I will go'?" she asked.

5. Preserve meaning:
   - Don't change the actual words
   - Only fix quotation mark types and nesting
   - Maintain all punctuation placement

DECISION PROCESS:
1. Analyze the text for quote nesting levels
2. Choose American English style (most common for media/broadcast)
3. Apply consistent quote mark types:
   - Level 1 (outermost): Double quotes (")
   - Level 2 (nested): Single quotes (')
   - Level 3 (rare): Double quotes (")
4. Preserve apostrophes as single quotes (')

OUTPUT FORMAT:
Return ONLY the corrected text with proper quotation marks. No explanation, no markdown, just the text.

CRITICAL: Return the exact same words with only quotation marks corrected. Do not add, remove, or modify any other content.`

    try {
      const result = await smartCall(prompt, {
        taskType: 'content-expansion',
        temperature: 0.2, // Low temperature for consistent formatting
        max_tokens: 500,
        systemPrompt: 'You are a precise copy editor. Return only the corrected text with no additional commentary.'
      })

      // Clean response - remove any markdown or quotes the LLM might add
      let normalized = result.trim()

      // Remove surrounding quotes if LLM added them
      if ((normalized.startsWith('"') && normalized.endsWith('"')) ||
          (normalized.startsWith("'") && normalized.endsWith("'"))) {
        // Only remove if they're wrapper quotes, not part of the actual text
        const withoutOuter = normalized.slice(1, -1)
        // Check if the inner text still has the same quote structure
        if (withoutOuter.includes('"') || withoutOuter.includes("'")) {
          normalized = withoutOuter
        }
      }

      console.log('📝 Normalized nested quotes:', { original: quoteText, normalized })
      return normalized

    } catch (err) {
      console.error('Quote normalization failed:', err)
      // Return original on failure
      return quoteText
    }
  }

  /**
   * Extract people and entities from script content
   * Returns structured JSON with people (names, roles, affiliations) and entities (organizations, locations, events, etc.)
   */
  async function extractEntities(scriptContent) {
    const prompt = `Extract all people and entities from the following script content. Return ONLY valid JSON with no explanation.

Script:
${scriptContent}

Return a JSON object with this exact structure:
{
  "people": [
    {
      "name": "Full Name",
      "role": "title/position (if mentioned)",
      "affiliation": "organization/company (if mentioned)",
      "description": "brief context about this person from the script"
    }
  ],
  "entities": {
    "organizations": ["Company Name", "Organization Name"],
    "locations": ["City", "State", "Country", "Specific Place"],
    "events": ["Event Name or Description"],
    "products": ["Product Name or Service"],
    "other": ["Any other significant entities"]
  }
}

Rules:
- Extract ALL named individuals mentioned
- Include their role/title if stated (e.g., "CEO", "Senator", "Dr.")
- Include affiliation if mentioned (e.g., "Microsoft", "Harvard")
- For entities, categorize organizations, locations, events, products, and other significant entities
- Return ONLY the JSON object, no markdown formatting, no explanation
- If a category has no items, use an empty array []`

    try {
      const result = await smartCall(prompt, {
        taskType: 'entity-extraction',
        temperature: 0.3,  // Lower temperature for more consistent extraction
        max_tokens: 2000,
        systemPrompt: 'You are a precise entity extraction system. Return only valid JSON with no additional text or markdown formatting.'
      })

      // Clean up the response to extract JSON
      let jsonText = result.trim()

      // Remove markdown code blocks if present
      jsonText = jsonText.replace(/```json\n?/g, '').replace(/```\n?/g, '')

      // Parse and validate
      const entities = JSON.parse(jsonText)

      // Validate structure
      if (!entities.people || !entities.entities) {
        throw new Error('Invalid entity extraction format')
      }

      return entities
    } catch (err) {
      console.error('Entity extraction failed:', err)
      // Return empty structure on failure
      return {
        people: [],
        entities: {
          organizations: [],
          locations: [],
          events: [],
          products: [],
          other: []
        }
      }
    }
  }

  return {
    loading,
    error,
    callOllama,
    callOpenAI,
    callAnthropic,
    callGemini,
    callGrok,
    smartCall,
    intelligentQuoteSplit,
    generateSlug,
    normalizeNestedQuotes,
    extractEntities
  }
}
