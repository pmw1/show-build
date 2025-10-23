/**
 * useLLM.js - Composable for LLM API integrations
 * Supports: Ollama, OpenAI, Anthropic, Google Gemini, xAI Grok
 */

import { ref } from 'vue'
import axios from 'axios'
import { notifyUserStandard, NOTIFICATION_COLORS } from '@/composables/useStandardNotification'

export function useLLM() {
  const loading = ref(false)
  const error = ref(null)
  const lastUsedModel = ref(null) // Track last used model {service, model, timestamp}

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
   * Falls back to hardcoded host if config fetch fails
   */
  async function callOllama(prompt, model = 'llama3:latest', options = {}) {
    try {
      // Use backend proxy to avoid HTTPS->HTTP mixed content blocking
      const response = await axios.post('/api/llm/ollama/generate', {
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
        contentExpansion: 'llama3:latest',  // Changed from llama2:13b-chat (too slow)
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

      // If configs failed to load (auth issue), try Ollama directly as fallback
      if (!configs) {
        console.warn('⚠️ Failed to load API configs, attempting direct Ollama fallback')
        try {
          return await callOllama(prompt, options.model || 'llama3:latest', options)
        } catch (err) {
          throw new Error('Failed to load API configuration. Please ensure you are logged in.')
        }
      }

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

      console.log('🔍 Checking enabled services...', {
        hasConfigs: !!configs,
        hasPreproduction: !!configs?.preproduction,
        hasAiServices: !!configs?.preproduction?.ai_services,
        ollamaConfig: configs?.preproduction?.ai_services?.ollama,
        fallbackOrder
      })

      for (const service of fallbackOrder) {
        const isEnabled = configs?.preproduction?.ai_services?.[service]?.enabled
        console.log(`  ${service}: enabled=${isEnabled}`, configs?.preproduction?.ai_services?.[service])

        if (isEnabled) {
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
    // Parse service string if it includes model (e.g., "ollama:llama3:latest")
    let serviceName = service
    let modelOverride = null

    if (service.includes(':')) {
      const parts = service.split(':')
      serviceName = parts[0]
      modelOverride = parts.slice(1).join(':') // Handle models like "llama3:latest"
      console.log(`📦 Parsed service: ${serviceName}, model: ${modelOverride}`)
    }

    // Notify when using cloud-based (paid) services
    const cloudServices = ['openai', 'anthropic', 'gemini', 'grok']
    const isCloudService = cloudServices.includes(serviceName)

    if (isCloudService) {
      const serviceNames = {
        'openai': 'OpenAI',
        'anthropic': 'Anthropic Claude',
        'gemini': 'Google Gemini',
        'grok': 'xAI Grok'
      }
      const displayName = serviceNames[serviceName] || serviceName

      // Send notification to backend for tracking
      try {
        await axios.post('/api/llm/notifications', {
          notifications: [{
            id: `llm-usage-${Date.now()}`,
            title: `💰 Cloud LLM Used`,
            message: `${displayName} is processing your request`,
            priority: 'medium',
            type: 'llm-usage',
            operationId: null,
            success: true,
            read: false,
            dismissed: false,
            timestamp: Date.now(),
            metadata: {
              service: serviceName,
              model: modelOverride || options.model || 'default',
              taskType: options.taskType || 'unknown'
            }
          }]
        })
        console.log(`💰 Cloud service notification sent: ${displayName}`)
      } catch (err) {
        console.warn('Failed to send cloud LLM notification:', err)
      }
    }

    switch (serviceName) {
      case 'ollama': {
        // Use task-specific Ollama model if available
        const routing = getRoutingPreferences()
        let ollamaModel = modelOverride || options.model

        if (!ollamaModel && options.taskType && routing.ollamaModels && routing.ollamaModels[options.taskType]) {
          ollamaModel = routing.ollamaModels[options.taskType]
          console.log(`🤖 Using Ollama (${ollamaModel}) for ${options.taskType}`)
        } else {
          console.log(`🤖 Using Ollama (${ollamaModel || 'default'})`)
        }

        // Track model usage
        lastUsedModel.value = {
          service: 'ollama',
          model: ollamaModel || 'default',
          timestamp: new Date().toISOString()
        }

        // Notify user - LOW priority for local model
        const taskName = options.taskType ? ` for ${options.taskType.replace(/-/g, ' ')}` : ''
        notifyUserStandard(
          `🤖 Local AI Processing<small>Model: ${ollamaModel || 'default'}${taskName}</small>`,
          NOTIFICATION_COLORS.INFO,
          2500
        )

        return await callOllama(prompt, ollamaModel, options)
      }
      case 'openai': {
        const openaiModel = modelOverride || options.model || 'gpt-4'
        lastUsedModel.value = {
          service: 'openai',
          model: openaiModel,
          timestamp: new Date().toISOString()
        }
        // Notify user - HIGH priority for cloud model
        const taskName = options.taskType ? ` • Task: ${options.taskType.replace(/-/g, ' ')}` : ''
        notifyUserStandard(
          `💰 Cloud AI API Call<small>Provider: OpenAI • Model: ${openaiModel}${taskName}</small>`,
          NOTIFICATION_COLORS.WARNING,
          5000
        )
        return await callOpenAI(prompt, modelOverride || options.model, options)
      }
      case 'anthropic': {
        const anthropicModel = modelOverride || options.model || 'claude-3-5-sonnet-20241022'
        lastUsedModel.value = {
          service: 'anthropic',
          model: anthropicModel,
          timestamp: new Date().toISOString()
        }
        // Notify user - HIGH priority for cloud model
        const taskName = options.taskType ? ` • Task: ${options.taskType.replace(/-/g, ' ')}` : ''
        notifyUserStandard(
          `💰 Cloud AI API Call<small>Provider: Anthropic • Model: ${anthropicModel}${taskName}</small>`,
          NOTIFICATION_COLORS.WARNING,
          5000
        )
        return await callAnthropic(prompt, modelOverride || options.model, options)
      }
      case 'gemini': {
        const geminiModel = modelOverride || options.model || 'gemini-2.0-flash'
        lastUsedModel.value = {
          service: 'gemini',
          model: geminiModel,
          timestamp: new Date().toISOString()
        }
        // Notify user - HIGH priority for cloud model
        const taskName = options.taskType ? ` • Task: ${options.taskType.replace(/-/g, ' ')}` : ''
        notifyUserStandard(
          `💰 Cloud AI API Call<small>Provider: Google Gemini • Model: ${geminiModel}${taskName}</small>`,
          NOTIFICATION_COLORS.WARNING,
          5000
        )
        return await callGemini(prompt, modelOverride || options.model, options)
      }
      case 'grok': {
        const grokModel = modelOverride || options.model || 'grok-4-latest'
        lastUsedModel.value = {
          service: 'grok',
          model: grokModel,
          timestamp: new Date().toISOString()
        }
        // Notify user - HIGH priority for cloud model
        const taskName = options.taskType ? ` • Task: ${options.taskType.replace(/-/g, ' ')}` : ''
        notifyUserStandard(
          `💰 Cloud AI API Call<small>Provider: xAI Grok • Model: ${grokModel}${taskName}</small>`,
          NOTIFICATION_COLORS.WARNING,
          5000
        )
        return await callGrok(prompt, modelOverride || options.model, options)
      }
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
    const maxLines = options.maxLines || 5
    const charsPerLine = options.charsPerLine || 50
    const fontSize = options.fontSize || '19px'

    // NEW: Smart split configuration
    const minSecondScreen = options.minSecondScreen || 80
    const splitStrategy = options.splitStrategy || 'smart'
    const balanceThresholdPercent = options.balanceThresholdPercent || 30
    const preferSentenceBoundaries = options.preferSentenceBoundaries !== false
    const allowMidSentenceSplit = options.allowMidSentenceSplit || false

    // Calculate thresholds
    const maxCharsScreen1 = maxLines * charsPerLine
    const balanceThreshold = maxCharsScreen1 + Math.round(minSecondScreen * (balanceThresholdPercent / 100))

    console.log('🧮 Smart Split Configuration:', {
      maxCharsScreen1,
      minSecondScreen,
      balanceThreshold,
      splitStrategy,
      quoteLength: quote.length
    })

    const prompt = `You are an FSQ (Full Screen Quote) layout analyzer with SMART SPLIT logic to prevent orphan text.

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
          // CRITICAL: Validate segments are non-overlapping and cover the full quote
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

      // Fallback: return original quote as single segment
      console.warn('LLM did not return valid JSON array, using fallback')
      return [quote]
    } catch (err) {
      console.error('Failed to split quote with LLM:', err)
      // Fallback: use deterministic algorithm
      return deterministicSplit(quote, maxCharsScreen1, minSecondScreen, balanceThreshold, preferSentenceBoundaries)
    }
  }

  /**
   * Validate segments returned by LLM
   * Checks for overlaps and coverage of original quote
   */
  function validateAndFixSegments(segments, originalQuote) {
    // Single segment is always valid
    if (segments.length === 1) {
      return { valid: true, segments }
    }

    // Check if segments are overlapping by seeing if their combined length
    // is significantly more than the original quote
    const totalLength = segments.reduce((sum, seg) => sum + seg.trim().length, 0)
    const originalLength = originalQuote.trim().length

    // Allow 10% variance for punctuation/spacing differences
    const isOverlapping = totalLength > originalLength * 1.1

    if (isOverlapping) {
      console.warn('❌ Segments overlap detected:', {
        totalLength,
        originalLength,
        ratio: (totalLength / originalLength).toFixed(2)
      })
      return { valid: false, segments }
    }

    // Check if segments cover the full quote by reconstructing
    const reconstructed = segments.join(' ').trim()
    const coverageRatio = reconstructed.length / originalLength

    if (coverageRatio < 0.9) {
      console.warn('❌ Segments don\'t cover full quote:', {
        reconstructedLength: reconstructed.length,
        originalLength,
        coverageRatio: coverageRatio.toFixed(2)
      })
      return { valid: false, segments }
    }

    console.log('✅ Segments validated as non-overlapping and complete')
    return { valid: true, segments }
  }

  /**
   * Deterministic split algorithm (fallback when LLM fails)
   * Implements the same smart split logic without AI
   */
  function deterministicSplit(quote, maxCharsScreen1, minSecondScreen, balanceThreshold, preferSentenceBoundaries = true) {
    const quoteLength = quote.length

    // Case A: Fits on single screen
    if (quoteLength <= maxCharsScreen1) {
      console.log('📏 Quote fits on single screen')
      return [quote]
    }

    // Case B: Gray zone - needs balanced split
    if (quoteLength <= balanceThreshold) {
      const targetSplitPoint = Math.floor(quoteLength / 2)
      console.log(`⚖️ Balanced split at ~${targetSplitPoint} chars (prevents orphan)`)

      const splitPoint = findBestSplitPoint(quote, targetSplitPoint, preferSentenceBoundaries)
      return [
        quote.substring(0, splitPoint).trim(),
        quote.substring(splitPoint).trim()
      ]
    }

    // Case C: Long quote - standard split at max chars
    console.log(`📐 Standard split at ~${maxCharsScreen1} chars`)
    const splitPoint = findBestSplitPoint(quote, maxCharsScreen1, preferSentenceBoundaries)

    const firstSegment = quote.substring(0, splitPoint).trim()
    const remainder = quote.substring(splitPoint).trim()

    // If remainder is still too long, recursively split it
    if (remainder.length > maxCharsScreen1) {
      console.log('🔁 Remainder too long, creating additional segments')
      const additionalSegments = deterministicSplit(
        remainder,
        maxCharsScreen1,
        minSecondScreen,
        balanceThreshold,
        preferSentenceBoundaries
      )
      return [firstSegment, ...additionalSegments]
    }

    return [firstSegment, remainder]
  }

  /**
   * Find the best split point near a target position
   * Prefers sentence boundaries, then clause breaks, then word boundaries
   */
  function findBestSplitPoint(text, targetPosition, preferSentenceBoundaries = true) {
    // Search window around target
    const searchStart = Math.max(0, targetPosition - 50)
    const searchEnd = Math.min(text.length, targetPosition + 50)
    const searchText = text.substring(searchStart, searchEnd)

    // Priority 1: Sentence boundaries (. ! ?)
    if (preferSentenceBoundaries) {
      const sentenceEndings = ['. ', '! ', '? ']
      for (const ending of sentenceEndings) {
        const relativePos = searchText.lastIndexOf(ending, targetPosition - searchStart)
        if (relativePos !== -1) {
          console.log(`  ✂️ Split at sentence boundary: "${ending.trim()}"`)
          return searchStart + relativePos + ending.length
        }
      }
    }

    // Priority 2: Clause breaks (, ; :)
    const clauseBreaks = [', ', '; ', ': ', ' - ']
    for (const breakChar of clauseBreaks) {
      const relativePos = searchText.lastIndexOf(breakChar, targetPosition - searchStart)
      if (relativePos !== -1) {
        console.log(`  ✂️ Split at clause break: "${breakChar.trim()}"`)
        return searchStart + relativePos + breakChar.length
      }
    }

    // Priority 3: Word boundary (space)
    const relativePos = searchText.lastIndexOf(' ', targetPosition - searchStart)
    if (relativePos !== -1) {
      console.log('  ✂️ Split at word boundary')
      return searchStart + relativePos + 1
    }

    // Last resort: exact position
    console.log('  ✂️ Split at exact position (no good boundary found)')
    return targetPosition
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
    const prompt = `Fix quotation marks to follow American English nesting rules (outer: double quotes, inner: single quotes).

TEXT:
${quoteText}

RULES:
- Outer quotes: " (double)
- Inner quotes: ' (single)
- Apostrophes: ' (single)
- Change ONLY quotation marks
- Preserve ALL words exactly as-is

OUTPUT: The corrected text ONLY. NO explanations, NO thank you messages, NO commentary, NO additional text whatsoever.

EXAMPLE INPUT: He said "I think it's 'great'"
EXAMPLE OUTPUT: He said "I think it's 'great'"

DO NOT write thank you messages. DO NOT explain your work. DO NOT add any text beyond the corrected quote.`

    try {
      const result = await smartCall(prompt, {
        taskType: 'content-expansion',
        temperature: 0.1, // Very low temperature for deterministic formatting
        max_tokens: 500,
        systemPrompt: 'You are a silent copy editor. Output ONLY the corrected text. NO explanations. NO thank you messages. NO commentary. Just the corrected text.'
      })

      // Clean response - remove any markdown or quotes the LLM might add
      let normalized = result.trim()

      // Remove LLM preamble/postamble (common patterns)
      const preamblePatterns = [
        /^Here'?s? the corrected text.*?:\s*/i,
        /^The corrected text is:?\s*/i,
        /^Corrected:?\s*/i,
        /^Result:?\s*/i,
        /^Output:?\s*/i,
        /^\[.*?\]:?\s*/,
        /^Sure,.*?:\s*/i
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

      // Remove preamble
      for (const pattern of preamblePatterns) {
        normalized = normalized.replace(pattern, '')
      }

      // Remove postamble
      for (const pattern of postamblePatterns) {
        normalized = normalized.replace(pattern, '')
      }

      // CRITICAL: Remove conversational paragraphs that LLM adds
      // Split by double newlines to find distinct paragraphs
      const paragraphs = normalized.split(/\n\n+/)

      // Keep only paragraphs that look like quote content (not meta-commentary)
      const cleanedParagraphs = paragraphs.filter(para => {
        const trimmed = para.trim()

        // Remove paragraphs that are clearly LLM meta-commentary
        const metaPatterns = [
          /^thank you for/i,
          /^i appreciate/i,
          /^i'm (happy|glad|pleased) to/i,
          /^this (demonstrates|shows|illustrates)/i,
          /^as you can see/i,
          /^note that/i,
          /^please note/i,
          /^feel free to/i,
          /^let me know/i,
          /^if you (need|want|would like)/i,
          /^i hope/i,
          /^is there anything/i
        ]

        for (const pattern of metaPatterns) {
          if (pattern.test(trimmed)) {
            console.log('🗑️ Removing LLM meta-commentary:', trimmed.substring(0, 100))
            return false
          }
        }

        return true
      })

      // Rejoin the cleaned paragraphs
      normalized = cleanedParagraphs.join('\n\n').trim()

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
