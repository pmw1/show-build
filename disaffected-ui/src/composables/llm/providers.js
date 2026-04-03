/**
 * LLM Provider API call implementations
 * Each function handles the HTTP request to a specific LLM provider.
 */

import axios from 'axios'

/**
 * Call Ollama (local LLM via backend proxy)
 */
export async function callOllama(prompt, model = 'deepseek-r1:32b-qwen-distill-q4_K_M', options = {}) {
  try {
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
export async function callOpenAI(prompt, model = 'gpt-4', options = {}, apiKey = null) {
  try {
    console.log('🔍 OpenAI API Request:', {
      model,
      apiKeyPresent: !!apiKey,
      apiKeyLength: apiKey?.length,
      apiKeyPrefix: apiKey?.substring(0, 10) + '...'
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
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    })

    console.log('✅ OpenAI API Success')
    return response.data.choices[0].message.content
  } catch (err) {
    console.error('❌ OpenAI API error:', {
      message: err.message,
      responseData: err.response?.data,
      status: err.response?.status
    })
    throw err
  }
}

/**
 * Call Anthropic Claude API
 */
export async function callAnthropic(prompt, model = 'claude-3-5-sonnet-20241022', options = {}, apiKey = null) {
  try {
    console.log('🔍 Anthropic API Request:', {
      model,
      apiKeyPresent: !!apiKey,
      apiKeyLength: apiKey?.length,
      apiKeyPrefix: apiKey?.substring(0, 10) + '...'
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
        'x-api-key': apiKey,
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
      status: err.response?.status
    })
    throw err
  }
}

/**
 * Call Google Gemini API
 */
export async function callGemini(prompt, model = 'gemini-2.0-flash', options = {}, apiKey = null) {
  try {
    console.log('🔍 Gemini API Request:', {
      model,
      apiKeyPresent: !!apiKey,
      apiKeyLength: apiKey?.length,
      apiKeyPrefix: apiKey?.substring(0, 10) + '...'
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
          'X-goog-api-key': apiKey
        }
      }
    )

    console.log('✅ Gemini API Success')
    return response.data.candidates[0].content.parts[0].text
  } catch (err) {
    console.error('❌ Gemini API error:', {
      message: err.message,
      responseData: err.response?.data,
      status: err.response?.status
    })
    throw err
  }
}

/**
 * Call xAI Grok API (OpenAI-compatible)
 */
export async function callGrok(prompt, model = 'grok-4-latest', options = {}, apiKey = null) {
  try {
    console.log('🔍 Grok API Request:', {
      model,
      apiKeyPresent: !!apiKey,
      apiKeyLength: apiKey?.length,
      apiKeyPrefix: apiKey?.substring(0, 10) + '...'
    })

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
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    })

    console.log('✅ Grok API Success')
    return response.data.choices[0].message.content
  } catch (err) {
    console.error('❌ Grok API error:', {
      message: err.message,
      responseData: err.response?.data,
      status: err.response?.status
    })
    throw err
  }
}
