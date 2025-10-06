# Ollama Model Recommendations for Show-Build Tasks

## Your Available Models

### 🌟 **Best General Purpose Models**

#### 1. **llama3:latest** (4.34 GB, 8.0B params)
- **Best for:** General tasks, creative writing, summaries
- **Speed:** Fast
- **Quality:** Excellent for most tasks
- **Recommended for:**
  - Script summaries
  - Title generation
  - Content expansion
  - General text processing

#### 2. **mistral:7b** (4.07 GB, 7.2B params)
- **Best for:** Fast, high-quality responses
- **Speed:** Very fast
- **Quality:** Excellent instruction following
- **Recommended for:**
  - Quick text transformations
  - Slug generation
  - Simple formatting tasks

#### 3. **llama2:13b-chat** (6.86 GB, 13B params)
- **Best for:** Conversational, detailed responses
- **Speed:** Moderate
- **Quality:** Very good for nuanced tasks
- **Recommended for:**
  - Complex summaries
  - Content expansion with context
  - Multi-step reasoning

---

### 🔧 **Specialized Code & Technical Models**

#### 4. **Qwen2.5-Coder:7b** (4.36 GB, 7.6B params) ⭐
- **Best for:** Code generation, technical writing
- **Speed:** Fast
- **Quality:** Excellent for structured output
- **Recommended for:**
  - JSON generation (quote splitting)
  - Structured data formatting
  - Technical documentation
  - Asset ID generation

#### 5. **Qwen2.5-Coder:32b** (18.49 GB, 32.8B params)
- **Best for:** Complex code tasks, large projects
- **Speed:** Slower (model switching takes time)
- **Quality:** Exceptional for technical work
- **Use when:** You need very high quality code/technical output

#### 6. **codellama:34b** (17.74 GB, 34B params)
- **Best for:** Code generation, debugging
- **Speed:** Slower
- **Quality:** Very high for code
- **Use when:** Working with code-heavy tasks

#### 7. **Devstral:24B** (13.35 GB, 23.6B params)
- **Best for:** Development-focused tasks
- **Speed:** Moderate
- **Quality:** Good for dev workflows

---

### 🎯 **Specialized Task Models**

#### 8. **deepseek-r1:8b** (4.87 GB, 8.2B params) ⭐⭐
- **Best for:** Reasoning, fact-checking, logical analysis
- **Speed:** Fast
- **Quality:** Excellent reasoning capabilities
- **Recommended for:**
  - Fact checking
  - Logic verification
  - Script analysis
  - Quality control

#### 9. **wizardlm-uncensored:13b** (6.86 GB, 13B params)
- **Best for:** Creative writing, no content restrictions
- **Speed:** Moderate
- **Quality:** Very creative
- **Recommended for:**
  - Creative content expansion
  - Alternative viewpoints
  - Controversial topics

#### 10. **ifioravanti/mistral-grammar-checker:7b** (3.83 GB, 7B params) ⭐
- **Best for:** Grammar checking, proofreading
- **Speed:** Fast
- **Quality:** Specialized for grammar
- **Recommended for:**
  - Script proofreading
  - Quote cleanup
  - Text quality control

---

### 🤖 **Premium Large Models** (Use Sparingly)

#### 11. **mistral-large:latest** (68.19 GB, 122.6B params)
- **Best for:** Highest quality tasks, complex reasoning
- **Speed:** Very slow (requires significant memory)
- **Quality:** Top-tier
- **Use when:** You need absolute best quality and have time to wait

#### 12. **gemma3:27b** (16.20 GB, 27.4B params)
- **Best for:** High-quality general tasks
- **Speed:** Slow
- **Quality:** Very high

#### 13. **gemma3:latest** (3.11 GB, 4.3B params)
- **Best for:** Lightweight tasks
- **Speed:** Fast
- **Quality:** Good for simple tasks

---

### 🎭 **Novelty/Experimental Models**

#### 14. **ALIENTELLIGENCE/psychiatrist:latest** (4.34 GB, 8.0B params)
- **Best for:** Psychological analysis, empathetic responses
- **Speed:** Fast
- **Quality:** Specialized
- **Fun for:** Analyzing interview content, guest psychology

#### 15. **llama2:latest** (3.56 GB, 7B params)
- **Best for:** Legacy compatibility
- **Speed:** Very fast
- **Quality:** Good baseline

---

## 💡 Recommended Task Routing for Show-Build

### High Priority Tasks (Quality Matters)
```javascript
{
  "scriptSummary": "deepseek-r1:8b",        // Best reasoning
  "titleGeneration": "llama3:latest",        // Creative + fast
  "contentExpansion": "llama2:13b-chat",     // Conversational depth
  "factChecking": "deepseek-r1:8b"          // Specialized reasoning
}
```

### Fast Tasks (Speed Matters)
```javascript
{
  "quoteSplitting": "Qwen2.5-Coder:7b",     // JSON output specialist
  "slugGeneration": "mistral:7b",            // Fast text transform
  "grammarCheck": "ifioravanti/mistral-grammar-checker:7b"
}
```

### Balanced (Quality + Speed)
```javascript
{
  "general": "llama3:latest",                // Best all-rounder
  "technical": "Qwen2.5-Coder:7b",          // Code/structure
  "creative": "wizardlm-uncensored:13b"      // No limits
}
```

---

## 🚀 Quick Start Recommendations

### **Top 3 Models for Show-Build:**

1. **Qwen2.5-Coder:7b** - Quote splitting, JSON tasks, structured output
2. **deepseek-r1:8b** - Fact checking, reasoning, script analysis
3. **llama3:latest** - Everything else (default)

### **Specialized Add-ons:**

- **Grammar:** `ifioravanti/mistral-grammar-checker:7b`
- **Heavy lifting:** `mistral-large:latest` (use when quality > speed)
- **Creative:** `wizardlm-uncensored:13b`

---

## ⚡ Performance Notes

**Fast Models** (< 5 GB, immediate response):
- mistral:7b
- llama3:latest
- Qwen2.5-Coder:7b
- gemma3:latest

**Moderate Models** (5-10 GB, quick switch):
- llama2:13b-chat
- deepseek-r1:8b
- wizardlm-uncensored:13b

**Heavy Models** (> 15 GB, slow to load):
- Qwen2.5-Coder:32b
- codellama:34b
- gemma3:27b
- mistral-large:latest (68 GB!)

**Pro Tip:** Keep one model from each category "warm" by using them regularly. Model switching adds 10-30 seconds depending on size.
