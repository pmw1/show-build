# IQ Quantization Research Bookmark

**Date**: October 6, 2025
**Topic**: Importance-weighted Quantization (IQ) for LLMs

## What is IQ Quantization?

**IQ** = "Importance-weighted Quantization" - an advanced quantization method that preserves model quality better than traditional methods.

### Key Concepts

**Traditional Quantization (Q4, Q5, Q8):**
- Treats all weights equally
- Simple bit reduction (32-bit → 4-bit)
- Standard approach, predictable quality loss

**IQ Quantization:**
- Uses **importance matrix** to identify critical weights
- Preserves important weights with higher precision
- Less important weights get more aggressive quantization
- Better quality-to-size ratio

## IQ Variants for Grok 2.5 (270B parameters)

| Quantization | Size | Bits | Quality | Hardware Requirement |
|--------------|------|------|---------|---------------------|
| **IQ1_M** | 61 GB | 1-bit | Minimal | 16GB GPU + 64GB RAM |
| **IQ2_M** | 84 GB | 2-bit | Lower | 24GB GPU + 80GB RAM |
| **IQ3_XXS** | ~105 GB | 3-bit | Moderate | 24GB GPU + 100GB RAM |
| **IQ4_XS** | 145 GB | 4-bit | Good | 24GB GPU + 128GB RAM |

### Comparison: IQ vs Traditional Q

For same model size:
- **IQ2_M** (2-bit importance-weighted) ≈ quality of **Q3** (3-bit traditional)
- **IQ4_XS** (4-bit importance-weighted) ≈ quality of **Q5** (5-bit traditional)

**Advantage**: Better quality at smaller file sizes

## Kairo Hardware Constraints

**Available:**
- GPU: RTX 3090 (24GB VRAM)
- RAM: 94GB
- **Total: 118 GB**

**What Fits:**
- ✅ **IQ2_M (84 GB)** - Best option for local Grok
- ✅ **IQ1_M (61 GB)** - Fits easily but very low quality
- ❌ **IQ4_XS (145 GB)** - Too large (27 GB over)

## Research Topics to Explore

### 1. **How IQ Quantization Works**
- Importance matrix calculation
- Weight sensitivity analysis
- Mixed-precision techniques
- Calibration dataset requirements

### 2. **IQ Implementation**
- Which inference engines support IQ?
  - llama.cpp: ✅ Full support
  - Ollama: ✅ Via llama.cpp backend
  - vLLM: ❓ Unknown
- How to create custom IQ quantizations
- Performance vs quality tradeoffs

### 3. **Comparison Studies**
- IQ2_M vs Q3_K_M quality benchmarks
- IQ4_XS vs Q4_K_M vs Q5_K_S
- Speed differences (IQ vs traditional)
- VRAM efficiency

### 4. **Advanced Techniques**
- **Dynamic quantization** (runtime)
- **Hybrid quantization** (different layers, different precision)
- **MoE-specific quantization** (for Grok's Mixture of Experts architecture)

## Practical Applications for Show-Build

### Option 1: IQ2_M Grok 2.5 (Local)
**Pros:**
- Runs on kairo (24GB GPU + 60GB RAM used)
- Local inference, no API costs
- Privacy for Disaffected content

**Cons:**
- Lower quality than cloud Grok API
- Slower than smaller models
- Large storage requirement (84GB)

**Use Case:** Batch content generation overnight where quality is acceptable and API costs add up

### Option 2: Hybrid Strategy
- **Cloud Grok API**: High-quality, critical content
- **IQ2_M Local Grok**: Drafts, summaries, batch processing
- **Qwen2.5-Coder 32B**: Fast local coding/editing tasks
- **Ollama llama3.2**: Quick local tasks

## Resources to Study

### Documentation
- **Unsloth AI Docs**: https://docs.unsloth.ai/models/grok-2
- **llama.cpp GitHub**: https://github.com/ggml-org/llama.cpp
- **GGUF Quantization Methods**: https://github.com/ggml-org/llama.cpp/blob/master/examples/quantize/README.md

### Hugging Face Models
- **Unsloth Grok-2 GGUF**: https://huggingface.co/unsloth/grok-2-GGUF
- **Bartowski Grok-2 GGUF**: https://huggingface.co/bartowski/xai-org_grok-2-GGUF

### Papers & Articles
- Search: "Importance-weighted quantization LLM"
- Search: "IQ quantization vs traditional quantization"
- Search: "Mixed precision quantization neural networks"

## Next Steps

1. **Learn More About IQ:**
   - Read llama.cpp quantization documentation
   - Compare IQ2_M vs Q3 quality benchmarks
   - Understand importance matrix calculation

2. **Evaluate for Disaffected:**
   - Test IQ2_M quality on sample content
   - Measure actual inference speed on kairo
   - Calculate cost savings vs cloud API

3. **Consider Alternatives:**
   - Qwen2.5-Coder 32B (Q4: 20GB) - fits entirely in GPU
   - Wait for hardware upgrade (add 64GB RAM → enables Q4_K_M)
   - Cloud API remains viable option

## Questions to Answer

- [ ] What's the actual quality difference between IQ2_M and Q3_K_XL?
- [ ] Can IQ quantizations be combined with expert offloading for Grok's MoE?
- [ ] What calibration data is best for Disaffected content?
- [ ] Is IQ2_M fast enough for interactive use or only batch?
- [ ] Can we create custom IQ quantizations optimized for our use case?

---

**Status**: Research bookmark - not implemented yet
**Decision**: TBD - need to evaluate IQ2_M quality vs cloud Grok API
**Hardware**: Kairo (RTX 3090 24GB + 94GB RAM) supports up to IQ2_M (84GB)
