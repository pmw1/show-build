/**
 * Test LLM API Connectivity
 * Run with: node test_llm_connectivity.js
 */

const axios = require('axios');
const fs = require('fs');

// Load API configs
const configPath = './app/app/storage/api_configs.json';
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
const aiServices = config.preproduction.ai_services;

// Test prompt
const TEST_PROMPT = "Say 'Hello from [service name]!' and nothing else.";

async function testOpenAI() {
  console.log('\n🔍 Testing OpenAI...');
  try {
    const openaiConfig = aiServices.openai;

    if (!openaiConfig.enabled) {
      console.log('❌ OpenAI is not enabled');
      return false;
    }

    const response = await axios.post('https://api.openai.com/v1/chat/completions', {
      model: openaiConfig.model,
      messages: [
        { role: 'system', content: 'You are a helpful assistant.' },
        { role: 'user', content: TEST_PROMPT }
      ],
      temperature: 0.7,
      max_tokens: 50
    }, {
      headers: {
        'Authorization': `Bearer ${openaiConfig.apiKey}`,
        'Content-Type': 'application/json'
      }
    });

    const result = response.data.choices[0].message.content;
    console.log('✅ OpenAI Success!');
    console.log(`   Response: ${result}`);
    return true;
  } catch (err) {
    console.log('❌ OpenAI Failed:');
    console.log(`   Status: ${err.response?.status}`);
    console.log(`   Error: ${err.response?.data?.error?.message || err.message}`);
    return false;
  }
}

async function testAnthropic() {
  console.log('\n🔍 Testing Anthropic Claude...');
  try {
    const anthropicConfig = aiServices.anthropic;

    if (!anthropicConfig.enabled) {
      console.log('❌ Anthropic is not enabled');
      return false;
    }

    const response = await axios.post('https://api.anthropic.com/v1/messages', {
      model: anthropicConfig.model,
      max_tokens: 50,
      messages: [
        { role: 'user', content: TEST_PROMPT }
      ]
    }, {
      headers: {
        'x-api-key': anthropicConfig.apiKey,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json'
      }
    });

    const result = response.data.content[0].text;
    console.log('✅ Anthropic Success!');
    console.log(`   Response: ${result}`);
    return true;
  } catch (err) {
    console.log('❌ Anthropic Failed:');
    console.log(`   Status: ${err.response?.status}`);
    console.log(`   Error: ${JSON.stringify(err.response?.data)}`);
    return false;
  }
}

async function testGemini() {
  console.log('\n🔍 Testing Google Gemini...');
  try {
    const geminiConfig = aiServices.gemini;

    if (!geminiConfig.enabled) {
      console.log('❌ Gemini is not enabled');
      return false;
    }

    const response = await axios.post(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`,
      {
        contents: [{
          parts: [{
            text: TEST_PROMPT
          }]
        }],
        generationConfig: {
          temperature: 0.7,
          maxOutputTokens: 50
        }
      },
      {
        headers: {
          'Content-Type': 'application/json',
          'X-goog-api-key': geminiConfig.apiKey
        }
      }
    );

    const result = response.data.candidates[0].content.parts[0].text;
    console.log('✅ Gemini Success!');
    console.log(`   Response: ${result}`);
    return true;
  } catch (err) {
    console.log('❌ Gemini Failed:');
    console.log(`   Status: ${err.response?.status}`);
    console.log(`   Error: ${JSON.stringify(err.response?.data)}`);
    return false;
  }
}

async function testGrok() {
  console.log('\n🔍 Testing xAI Grok...');
  try {
    const grokConfig = aiServices.grok;

    if (!grokConfig.enabled) {
      console.log('❌ Grok is not enabled');
      return false;
    }

    const response = await axios.post('https://api.x.ai/v1/chat/completions', {
      model: grokConfig.model,
      messages: [
        { role: 'system', content: 'You are Grok, a helpful assistant.' },
        { role: 'user', content: TEST_PROMPT }
      ],
      temperature: 0.7,
      max_tokens: 50,
      stream: false
    }, {
      headers: {
        'Authorization': `Bearer ${grokConfig.apiKey}`,
        'Content-Type': 'application/json'
      }
    });

    const result = response.data.choices[0].message.content;
    console.log('✅ Grok Success!');
    console.log(`   Response: ${result}`);
    return true;
  } catch (err) {
    console.log('❌ Grok Failed:');
    console.log(`   Status: ${err.response?.status}`);
    console.log(`   Error: ${JSON.stringify(err.response?.data)}`);
    return false;
  }
}

async function testOllama() {
  console.log('\n🔍 Testing Ollama (local)...');
  try {
    const ollamaConfig = aiServices.ollama;

    if (!ollamaConfig.enabled) {
      console.log('⏭️  Ollama is not enabled (local service)');
      return null;
    }

    const host = ollamaConfig.host || 'http://localhost:11434';

    const response = await axios.post(`${host}/api/generate`, {
      model: ollamaConfig.model,
      prompt: TEST_PROMPT,
      stream: false,
      options: {
        temperature: 0.7,
        max_tokens: 50
      }
    }, {
      timeout: 5000
    });

    const result = response.data.response;
    console.log('✅ Ollama Success!');
    console.log(`   Response: ${result}`);
    return true;
  } catch (err) {
    console.log('⚠️  Ollama Failed (expected if not running locally):');
    console.log(`   Error: ${err.message}`);
    return null;
  }
}

async function runAllTests() {
  console.log('═══════════════════════════════════════════════════════');
  console.log('🧪 LLM API Connectivity Test Suite');
  console.log('═══════════════════════════════════════════════════════');

  const results = {
    openai: await testOpenAI(),
    anthropic: await testAnthropic(),
    gemini: await testGemini(),
    grok: await testGrok(),
    ollama: await testOllama()
  };

  console.log('\n═══════════════════════════════════════════════════════');
  console.log('📊 Test Results Summary:');
  console.log('═══════════════════════════════════════════════════════');

  const successCount = Object.values(results).filter(r => r === true).length;
  const failCount = Object.values(results).filter(r => r === false).length;
  const skipCount = Object.values(results).filter(r => r === null).length;

  console.log(`✅ Successful: ${successCount}`);
  console.log(`❌ Failed: ${failCount}`);
  console.log(`⏭️  Skipped: ${skipCount}`);

  console.log('\nDetailed Results:');
  console.log(`  OpenAI:    ${results.openai === true ? '✅' : results.openai === false ? '❌' : '⏭️'}`);
  console.log(`  Anthropic: ${results.anthropic === true ? '✅' : results.anthropic === false ? '❌' : '⏭️'}`);
  console.log(`  Gemini:    ${results.gemini === true ? '✅' : results.gemini === false ? '❌' : '⏭️'}`);
  console.log(`  Grok:      ${results.grok === true ? '✅' : results.grok === false ? '❌' : '⏭️'}`);
  console.log(`  Ollama:    ${results.ollama === true ? '✅' : results.ollama === false ? '❌' : '⏭️'}`);

  console.log('═══════════════════════════════════════════════════════\n');

  if (failCount > 0) {
    process.exit(1);
  }
}

// Run tests
runAllTests().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
