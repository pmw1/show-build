/**
 * useLLM.js - Composable for LLM API integrations
 * Supports: Ollama, OpenAI, Anthropic, Google Gemini, xAI Grok
 *
 * Provider implementations: ./llm/providers.js
 * Quote splitting utilities: ./llm/quoteSplitting.js
 */

import { ref } from 'vue'
import axios from 'axios'
import { notifyUserStandard, NOTIFICATION_COLORS } from '@/composables/useStandardNotification'
import {
  callOllama as _callOllama,
  callOpenAI as _callOpenAI,
  callAnthropic as _callAnthropic,
  callGemini as _callGemini,
  callGrok as _callGrok
} from './llm/providers'
import {
  validateAndFixSegments,
  deterministicSplit
} from './llm/quoteSplitting'

export function useLLM() {
  const loading = ref(false)
  const error = ref(null)
  const lastUsedModel = ref(null)

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

  // Wrap provider calls to fetch configs automatically (backward compat)
  async function callOllama(prompt, model, options = {}) {
    return _callOllama(prompt, model, options)
  }

  async function callOpenAI(prompt, model, options = {}) {
    const configs = await getApiConfigs()
    const openaiConfig = configs?.preproduction?.ai_services?.openai
    if (!openaiConfig?.enabled) throw new Error('OpenAI is not enabled in settings')
    return _callOpenAI(prompt, model, options, openaiConfig.apiKey)
  }

  async function callAnthropic(prompt, model, options = {}) {
    const configs = await getApiConfigs()
    const anthropicConfig = configs?.preproduction?.ai_services?.anthropic
    if (!anthropicConfig?.enabled) throw new Error('Anthropic is not enabled in settings')
    return _callAnthropic(prompt, model, options, anthropicConfig.apiKey)
  }

  async function callGemini(prompt, model, options = {}) {
    const configs = await getApiConfigs()
    const geminiConfig = configs?.preproduction?.ai_services?.gemini
    if (!geminiConfig?.enabled) throw new Error('Gemini is not enabled in settings')
    return _callGemini(prompt, model, options, geminiConfig.apiKey)
  }

  async function callGrok(prompt, model, options = {}) {
    const configs = await getApiConfigs()
    const grokConfig = configs?.preproduction?.ai_services?.grok
    if (!grokConfig?.enabled) throw new Error('Grok is not enabled in settings')
    return _callGrok(prompt, model, options, grokConfig.apiKey)
  }

  /**
   * Get routing preferences from localStorage
   */
  function getRoutingPreferences() {
    const saved = localStorage.getItem('llm-routing-settings')
    if (saved) {
      return JSON.parse(saved)
    }
    return {
      routing: {
        quoteSplitting: 'ollama',
        slugGeneration: 'ollama',
        scriptSummary: 'ollama',
        titleGeneration: 'ollama',
        contentExpansion: 'ollama',
        factChecking: 'ollama',
        entityExtraction: 'ollama',
        enableFallback: true,
        fallbackOrder: ['ollama', 'openai', 'gemini', 'grok', 'anthropic']
      },
      ollamaModels: {
        quoteSplitting: 'Qwen2.5-Coder:7b',
        slugGeneration: 'mistral:7b',
        scriptSummary: 'llama3:latest',
        titleGeneration: 'llama3:latest',
        contentExpansion: 'llama3:latest',
        factChecking: 'deepseek-r1:8b',
        entityExtraction: 'Qwen2.5-Coder:7b'
      }
    }
  }

  /**
   * Smart LLM call with task-specific routing
   */
  async function smartCall(prompt, options = {}) {
    loading.value = true
    error.value = null

    try {
      const configs = await getApiConfigs()
      const routing = getRoutingPreferences().routing

      if (!configs) {
        console.warn('⚠️ Failed to load API configs, attempting direct Ollama fallback')
        try {
          return await callOllama(prompt, options.model || 'deepseek-r1:32b-qwen-distill-q4_K_M', options)
        } catch (err) {
          throw new Error('Failed to load API configuration. Please ensure you are logged in.')
        }
      }

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

      if (preferredService !== 'auto') {
        try {
          console.log(`🎯 Using preferred service for ${options.taskType}: ${preferredService}`)
          const result = await callSpecificService(preferredService, prompt, options, configs)
          if (result) return result
        } catch (err) {
          console.warn(`Preferred service ${preferredService} failed, falling back...`)
          if (!routing.enableFallback) throw err
        }
      }

      const fallbackOrder = routing.enableFallback ? routing.fallbackOrder : ['ollama', 'openai', 'anthropic', 'gemini', 'grok']

      for (const service of fallbackOrder) {
        const isEnabled = configs?.preproduction?.ai_services?.[service]?.enabled
        if (isEnabled) {
          try {
            const result = await callSpecificService(service, prompt, options, configs)
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
  async function callSpecificService(service, prompt, options, configs = null) {
    let serviceName = service
    let modelOverride = null

    if (service.includes(':')) {
      const parts = service.split(':')
      serviceName = parts[0]
      modelOverride = parts.slice(1).join(':')
    }

    // Notify when using cloud-based (paid) services
    const cloudServices = ['openai', 'anthropic', 'gemini', 'grok']
    const isCloudService = cloudServices.includes(serviceName)

    // NOTE: the old POST /api/llm/notifications here was removed (dead endpoint —
    // llm_state_router retired 2026-06-04). The user-facing "Cloud AI API Call"
    // notice is already shown per-provider via notifyUserStandard() below, so this
    // duplicate backend notification served no purpose.
    void isCloudService

    const routing = getRoutingPreferences()
    const serviceConfig = configs?.preproduction?.ai_services?.[serviceName]
    const apiKey = serviceConfig?.apiKey

    switch (serviceName) {
      case 'ollama': {
        let ollamaModel = modelOverride || options.model
        if (!ollamaModel && options.taskType && routing.ollamaModels?.[options.taskType]) {
          ollamaModel = routing.ollamaModels[options.taskType]
        } else if (!ollamaModel && serviceConfig?.model) {
          ollamaModel = serviceConfig.model
        }

        lastUsedModel.value = { service: 'ollama', model: ollamaModel || 'default', timestamp: new Date().toISOString() }

        const taskName = options.taskType ? ` for ${options.taskType.replace(/-/g, ' ')}` : ''
        const displayModel = ollamaModel || serviceConfig?.model || 'deepseek-r1:32b-qwen-distill-q4_K_M'
        notifyUserStandard(
          `🤖 Local AI Processing<small>Model: ${displayModel}${taskName}</small>`,
          NOTIFICATION_COLORS.INFO,
          2500
        )
        return await _callOllama(prompt, ollamaModel, options)
      }
      case 'openai': {
        const model = modelOverride || options.model || 'gpt-4'
        lastUsedModel.value = { service: 'openai', model, timestamp: new Date().toISOString() }
        const taskName = options.taskType ? ` • Task: ${options.taskType.replace(/-/g, ' ')}` : ''
        notifyUserStandard(`💰 Cloud AI API Call<small>Provider: OpenAI • Model: ${model}${taskName}</small>`, NOTIFICATION_COLORS.WARNING, 5000)
        return await _callOpenAI(prompt, model, options, apiKey)
      }
      case 'anthropic': {
        const model = modelOverride || options.model || 'claude-3-5-sonnet-20241022'
        lastUsedModel.value = { service: 'anthropic', model, timestamp: new Date().toISOString() }
        const taskName = options.taskType ? ` • Task: ${options.taskType.replace(/-/g, ' ')}` : ''
        notifyUserStandard(`💰 Cloud AI API Call<small>Provider: Anthropic • Model: ${model}${taskName}</small>`, NOTIFICATION_COLORS.WARNING, 5000)
        return await _callAnthropic(prompt, model, options, apiKey)
      }
      case 'gemini': {
        const model = modelOverride || options.model || 'gemini-2.0-flash'
        lastUsedModel.value = { service: 'gemini', model, timestamp: new Date().toISOString() }
        const taskName = options.taskType ? ` • Task: ${options.taskType.replace(/-/g, ' ')}` : ''
        notifyUserStandard(`💰 Cloud AI API Call<small>Provider: Google Gemini • Model: ${model}${taskName}</small>`, NOTIFICATION_COLORS.WARNING, 5000)
        return await _callGemini(prompt, model, options, apiKey)
      }
      case 'grok': {
        const model = modelOverride || options.model || 'grok-4-latest'
        lastUsedModel.value = { service: 'grok', model, timestamp: new Date().toISOString() }
        const taskName = options.taskType ? ` • Task: ${options.taskType.replace(/-/g, ' ')}` : ''
        notifyUserStandard(`💰 Cloud AI API Call<small>Provider: xAI Grok • Model: ${model}${taskName}</small>`, NOTIFICATION_COLORS.WARNING, 5000)
        return await _callGrok(prompt, model, options, apiKey)
      }
      default:
        throw new Error(`Unknown service: ${service}`)
    }
  }

  /**
   * Split a long quote intelligently for FSQ display using LLM
   */
  async function intelligentQuoteSplit(quote, options = {}) {
    const maxLines = options.maxLines || 5
    const charsPerLine = options.charsPerLine || 50
    const minSecondScreen = options.minSecondScreen || 80
    const splitStrategy = options.splitStrategy || 'smart'
    const balanceThresholdPercent = options.balanceThresholdPercent || 30
    const preferSentenceBoundaries = options.preferSentenceBoundaries !== false

    const maxCharsScreen1 = maxLines * charsPerLine
    const balanceThreshold = maxCharsScreen1 + Math.round(minSecondScreen * (balanceThresholdPercent / 100))

    console.log('🧮 Smart Split Configuration:', {
      maxCharsScreen1, minSecondScreen, balanceThreshold, splitStrategy, quoteLength: quote.length
    })

    const prompt = `<task>Split this quote for full-screen display if needed.</task>

<constraints>
- Max ${maxCharsScreen1} chars per screen (${maxLines} lines × ${charsPerLine} chars)
- Min ${minSecondScreen} chars for second screen (no orphan text)
- Quote length: ${quote.length} chars
</constraints>

<quote>
${quote}
</quote>

<rules>
1. If quote ≤ ${maxCharsScreen1} chars: Return as single item ["entire quote"]
2. If quote > ${maxCharsScreen1}: Split at sentence boundary near ${maxCharsScreen1} chars
3. NO overlapping text between segments - each word appears exactly once
4. ${preferSentenceBoundaries ? 'Prefer splitting at sentence endings (. ! ?)' : 'Split at natural pauses'}
</rules>

<output>
Return ONLY a JSON array of strings. No explanation, no markdown.
Example: ["First segment text here.", "Second segment text here."]
</output>`

    try {
      const result = await smartCall(prompt, {
        taskType: 'quote-splitting',
        temperature: 0.2,
        max_tokens: 1000,
        systemPrompt: 'You are a precise quote layout analyzer. Return only valid JSON arrays with no additional text.'
      })

      let jsonText = result.trim()
      jsonText = jsonText.replace(/```json\n?/g, '').replace(/```\n?/g, '')
      jsonText = jsonText.replace(/<\/?(?:task|constraints|quote|rules|output)[^>]*>/gi, '')
      jsonText = jsonText.replace(/^(?:Here(?:'s| is) the|The )?(?:JSON|result|output|array)[\s:]*\n?/i, '')
      jsonText = jsonText.replace(/^(?:Sure|Certainly|Of course)[,!]?\s*(?:here(?:'s| is))?[^[]*\n?/i, '')

      const jsonMatch = jsonText.match(/\[[\s\S]*\]/)
      if (jsonMatch) {
        const segments = JSON.parse(jsonMatch[0])

        if (Array.isArray(segments) && segments.every(s => typeof s === 'string')) {
          const validated = validateAndFixSegments(segments, quote)
          if (validated.valid) {
            console.log(`✅ Quote split analysis: ${validated.segments.length} segment(s) (validated)`)
            return validated.segments
          } else {
            console.warn('⚠️ LLM returned invalid/overlapping segments, using deterministic fallback')
            return deterministicSplit(quote, maxCharsScreen1, minSecondScreen, balanceThreshold, preferSentenceBoundaries)
          }
        }
      }

      console.warn('LLM did not return valid JSON array, using fallback')
      return [quote]
    } catch (err) {
      console.error('Failed to split quote with LLM:', err)
      return deterministicSplit(quote, maxCharsScreen1, minSecondScreen, balanceThreshold, preferSentenceBoundaries)
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
      return quoteText.toLowerCase().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-').substring(0, 50)
    }
  }

  /**
   * Normalize nested quotes according to English language best practices
   */
  async function normalizeNestedQuotes(quoteText) {
    const prompt = `<task>Fix quotation mark nesting in the text below.</task>

<rules>
- Outer quotes must be double quotes: "
- Inner/nested quotes must be single quotes: '
- Apostrophes stay as single quotes: '
- Do NOT change any words, only quotation marks
</rules>

<input>
${quoteText}
</input>

<output>
Return ONLY the corrected text with no explanation. Do not include XML tags in your response.
</output>`

    try {
      const result = await smartCall(prompt, {
        taskType: 'content-expansion',
        temperature: 0.1,
        max_tokens: 800,
        systemPrompt: 'You fix quotation marks in text. Return ONLY the corrected text. No explanations, no tags, no commentary.',
        model: 'llama3:latest'
      })

      let normalized = result.trim()

      // Clean XML tags, prompt echoes, preamble/postamble
      normalized = normalized.replace(/<\/?(?:task|rules|input|output|text|quote)[^>]*>/gi, '')

      const promptEchoPatterns = [
        /^.*?(?:Fix|Correct|Normalize).*?quotation.*?(?:marks?|nesting).*?$/im,
        /^.*?(?:outer|inner)\s*quotes?.*?(?:double|single).*?$/im,
        /^.*?apostrophe.*?single.*?$/im,
        /^.*?(?:do\s*not|don't)\s*change.*?words.*?$/im,
        /^.*?return\s*only.*?(?:corrected|text).*?$/im,
        /^.*?no\s*(?:explanation|commentary).*?$/im,
        /^RULES:.*$/im,
        /^OUTPUT:.*$/im,
        /^TEXT:.*$/im,
        /^EXAMPLE\s*(?:INPUT|OUTPUT):.*$/im,
        /^-\s*(?:Outer|Inner)\s*quotes?:.*$/gim,
        /^-\s*Apostrophes?:.*$/gim,
        /^-\s*(?:Change|Preserve|Do\s*NOT).*$/gim
      ]
      for (const pattern of promptEchoPatterns) {
        normalized = normalized.replace(pattern, '')
      }

      const preamblePatterns = [
        /^Here'?s? the corrected text.*?:\s*/i,
        /^The corrected text is:?\s*/i,
        /^Corrected(?:\s*text)?:?\s*/i,
        /^Result:?\s*/i,
        /^Output:?\s*/i,
        /^\[.*?\]:?\s*/,
        /^Sure,.*?:\s*/i,
        /^Certainly[,!]?\s*/i,
        /^Of course[,!]?\s*/i
      ]
      const postamblePatterns = [
        /\s*I hope this helps!?\s*$/i,
        /\s*Let me know if.*$/i,
        /\s*Is there anything.*$/i,
        /\s*Thank you for.*$/i,
        /\s*I appreciate.*$/i,
        /\s*Please let me know.*$/i,
        /\s*Feel free to.*$/i
      ]

      for (const pattern of preamblePatterns) normalized = normalized.replace(pattern, '')
      for (const pattern of postamblePatterns) normalized = normalized.replace(pattern, '')

      // Remove conversational paragraphs
      const paragraphs = normalized.split(/\n\n+/)
      const cleanedParagraphs = paragraphs.filter(para => {
        const trimmed = para.trim()
        if (!trimmed) return false
        const metaPatterns = [
          /^thank you for/i, /^i appreciate/i, /^i'm (happy|glad|pleased) to/i,
          /^this (demonstrates|shows|illustrates)/i, /^as you can see/i,
          /^note that/i, /^please note/i, /^feel free to/i, /^let me know/i,
          /^if you (need|want|would like)/i, /^i hope/i, /^is there anything/i,
          /^here is the/i, /^the (?:corrected|fixed|normalized)/i,
          /^-\s*(?:outer|inner|apostrophe)/i, /^(?:rules|output|input|text):/i,
          /^example\s*(?:input|output)/i, /^do\s*not\s*(?:write|add|include)/i,
          /^return\s*only/i, /^no\s*explanation/i
        ]
        for (const pattern of metaPatterns) {
          if (pattern.test(trimmed)) return false
        }
        return true
      })

      normalized = cleanedParagraphs.join('\n\n').trim()
      normalized = normalized.replace(/\n{3,}/g, '\n\n')

      if ((normalized.startsWith('"') && normalized.endsWith('"')) ||
          (normalized.startsWith("'") && normalized.endsWith("'"))) {
        const withoutOuter = normalized.slice(1, -1)
        if (withoutOuter.includes('"') || withoutOuter.includes("'")) {
          normalized = withoutOuter
        }
      }

      if (!normalized || normalized.length < quoteText.length * 0.5) {
        console.warn('⚠️ Normalization produced invalid result, returning original')
        return quoteText
      }

      console.log('📝 Normalized nested quotes:', { original: quoteText, normalized })
      return normalized

    } catch (err) {
      console.error('Quote normalization failed:', err)
      return quoteText
    }
  }

  /**
   * Extract people and entities from script content
   */
  async function extractEntities(scriptContent) {
    const prompt = `Extract all people and entities from the following script content. Return ONLY valid JSON with no explanation.

Format:
{
  "people": [{"name": "Full Name", "role": "their role/description", "affiliation": "their org/group"}],
  "entities": {
    "organizations": ["org names"],
    "locations": ["place names"],
    "events": ["event names"],
    "products": ["product/brand names"],
    "other": ["other notable entities"]
  }
}

Script content:
${scriptContent}

Return ONLY the JSON object.`

    try {
      const result = await smartCall(prompt, {
        taskType: 'entity-extraction',
        temperature: 0.2,
        max_tokens: 2000,
        systemPrompt: 'You extract entities from text. Return ONLY valid JSON.'
      })

      let jsonText = result.trim()
      jsonText = jsonText.replace(/```json\n?/g, '').replace(/```\n?/g, '')

      const jsonMatch = jsonText.match(/\{[\s\S]*\}/)
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0])
      }

      return { people: [], entities: { organizations: [], locations: [], events: [], products: [], other: [] } }
    } catch (err) {
      console.error('Entity extraction failed:', err)
      return { people: [], entities: { organizations: [], locations: [], events: [], products: [], other: [] } }
    }
  }

  return {
    loading,
    error,
    lastUsedModel,
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
