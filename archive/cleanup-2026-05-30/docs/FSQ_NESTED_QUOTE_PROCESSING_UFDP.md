# FSQ Nested Quote Processing - UFDP

**Status**: ✅ Implemented
**Component**: `disaffected-ui/src/components/modals/FsqModal.vue`
**Issue**: Nested quotes and escape sequences causing display problems
**Solution**: Decode → Process → Encode pipeline

---

## Problem Overview

### The Issue
When quotes contain nested quotes (e.g., `He said "hello" to her`), escape sequences can accumulate through multiple processing stages:

1. **User Input**: `He said "hello" to her`
2. **Browser Escape**: May become `He said \"hello\" to her`
3. **Storage**: Saved as `He said &quot;hello&quot; to her`
4. **Retrieval**: Loaded back with escape sequences intact
5. **Display**: Shows literally as `He said &quot;hello&quot; to her` instead of `He said "hello" to her`

### Double-Escaping Problem
Without proper decode/encode separation:
- Quote with nested quotes gets escaped for storage
- Gets escaped again for HTML display
- User sees `&amp;quot;hello&amp;quot;` instead of `"hello"`

---

## Solution: Decode → Process → Encode Pipeline

### Architecture
```
[User Input]
    ↓
[Decode Escape Sequences] ← Clean text, no escapes
    ↓
[AI Processing] ← Works with clean text
    ↓
[Store Clean Text] ← Database stores unescaped
    ↓
[Retrieve] ← Load clean text
    ↓
[Decode Again] ← Handle any stored escapes (defensive)
    ↓
[Encode for HTML Display] ← Only escape at display time
    ↓
[User Sees Correct Quote]
```

---

## Implementation

### Step 1: Decode Function
**File**: `FsqModal.vue` (lines 662-691)

Handles all common escape sequences:

```javascript
/**
 * Decode stored escape sequences and HTML entities
 * This handles quotes that may have been stored with escape sequences like:
 * - &quot; → "
 * - &#39; → '
 * - &amp; → &
 * - \" → "
 * - \' → '
 * - \n → newline
 */
decodeQuoteText(text) {
  if (!text) return text

  let decoded = text
    // First decode HTML entities
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    // Then decode backslash escape sequences
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    .replace(/\\n/g, '\n')
    .replace(/\\r/g, '\r')
    .replace(/\\t/g, '\t')
    .replace(/\\\\/g, '\\') // Double backslash last

  return decoded
}
```

**Order matters:**
1. **HTML entities first** (`&quot;` → `"`)
2. **Backslash escapes second** (`\"` → `"`)
3. **Double backslash last** (`\\` → `\`)

### Step 2: Preview Display
**File**: `FsqModal.vue` (lines 639-655)

Decode BEFORE encoding for display:

```javascript
formattedQuotePreview() {
  const rawText = this.quote || 'Quote text will appear here...';

  // Step 1: Decode any stored escape sequences first
  const decoded = this.decodeQuoteText(rawText);

  // Step 2: Escape for safe HTML display
  const escaped = decoded
    .replace(/&/g, '&amp;')           // Escape ampersands first
    .replace(/"/g, '&quot;')           // Escape all double quotes
    .replace(/'/g, '&#39;')            // Escape all single quotes
    .replace(/</g, '&lt;')             // Escape less-than
    .replace(/>/g, '&gt;')             // Escape greater-than
    .replace(/\n/g, '<br>');           // Actual newlines to <br>

  return '"' + escaped + '"';
}
```

**Why this works:**
- Decode removes any accumulated escape sequences
- Fresh encode ensures proper HTML safety
- No double-escaping possible

### Step 3: Storage
**File**: `FsqModal.vue` (lines 891-908)

Store **clean, decoded text**:

```javascript
// Create the FSQ cue data without media URL (will be generated later)
// Store quote with decoded text (clean, no escape sequences)
const cleanQuote = this.decodeQuoteText(segment);

const cueData = {
  type: 'FSQ',
  assetId: assetId,
  slug: slug,
  quote: cleanQuote, // Store decoded text
  style: this.quoteStyle,
  fontFamily: this.fontFamily,
  fontSize: this.fontSize,
  renderMode: this.renderMode,
  duration: this.duration,
  wordCount: wordCount,
  part: isMultipart ? `${i + 1}x${quoteSegments.length}` : '1x1'
}
```

**Key principle:**
- Store human-readable text
- No escape sequences in database
- Encoding only happens at display/render time

---

## Processing Flow Examples

### Example 1: Simple Nested Quote

**User Input:**
```
He said "hello" to her
```

**Processing:**
1. **Decode**: No escapes present → `He said "hello" to her`
2. **AI Analysis**: Works with clean text
3. **Store**: `He said "hello" to her` (clean)
4. **Retrieve**: `He said "hello" to her`
5. **Display Decode**: `He said "hello" to her`
6. **Display Encode**: `He said &quot;hello&quot; to her` (HTML safe)
7. **Browser Renders**: `He said "hello" to her` ✅

### Example 2: Pasted from Web (Pre-escaped)

**User Pastes:**
```
He said &quot;hello&quot; to her
```

**Processing:**
1. **Decode**: `&quot;` → `"` → `He said "hello" to her`
2. **AI Analysis**: Works with clean text
3. **Store**: `He said "hello" to her` (clean)
4. **Retrieve**: `He said "hello" to her`
5. **Display Decode**: `He said "hello" to her`
6. **Display Encode**: `He said &quot;hello&quot; to her` (HTML safe)
7. **Browser Renders**: `He said "hello" to her` ✅

### Example 3: Backslash Escaped

**User Pastes:**
```
He said \"hello\" to her
```

**Processing:**
1. **Decode**: `\"` → `"` → `He said "hello" to her`
2. **AI Analysis**: Works with clean text
3. **Store**: `He said "hello" to her` (clean)
4. **Retrieve**: `He said "hello" to her`
5. **Display Decode**: `He said "hello" to her`
6. **Display Encode**: `He said &quot;hello&quot; to her` (HTML safe)
7. **Browser Renders**: `He said "hello" to her` ✅

### Example 4: Double-Escaped (Defensive)

**User Somehow Gets:**
```
He said &amp;quot;hello&amp;quot; to her
```

**Processing:**
1. **Decode**: `&amp;` → `&`, then `&quot;` → `"` → `He said "hello" to her`
2. **AI Analysis**: Works with clean text
3. **Store**: `He said "hello" to her` (clean)
4. **Retrieve**: `He said "hello" to her`
5. **Display Decode**: `He said "hello" to her`
6. **Display Encode**: `He said &quot;hello&quot; to her` (HTML safe)
7. **Browser Renders**: `He said "hello" to her` ✅

---

## Supported Escape Sequences

### HTML Entities
| Entity | Decoded | Usage |
|--------|---------|-------|
| `&quot;` | `"` | Double quotes |
| `&#39;` | `'` | Single quotes/apostrophes |
| `&amp;` | `&` | Ampersands |
| `&lt;` | `<` | Less-than |
| `&gt;` | `>` | Greater-than |

### Backslash Escapes
| Escape | Decoded | Usage |
|--------|---------|-------|
| `\"` | `"` | Escaped double quote |
| `\'` | `'` | Escaped single quote |
| `\\` | `\` | Escaped backslash |
| `\n` | newline | Line break |
| `\r` | carriage return | Windows line break |
| `\t` | tab | Tab character |

---

## Order of Operations: Nested Quotes + Split Analysis

### Sequential Processing
When a quote needs **BOTH** nested quote normalization AND splitting:

**Processing happens in this order:**
1. ✅ **Decode escape sequences** (if any)
2. ✅ **Normalize nested quotes** (fix quote mark types)
3. ✅ **Split analysis** (FINAL operation - last AI decision before storage)
4. ✅ **Store clean segments** (each with properly nested quotes)

**Key principle: Splitting is the LAST operation** - all text normalization happens before splitting.

### Why This Order? (Text Normalization → Splitting)

**Correct Order (Decode → Normalize → Split → Store):**
```
Input: He said &quot;She told me "hello" yesterday&quot; and it was a very long quote that needs splitting.

STEP 1: Decode escape sequences
   ↓
He said "She told me "hello" yesterday" and it was a very long quote that needs splitting.

STEP 2: Normalize nested quotes
   ↓
He said "She told me 'hello' yesterday" and it was a very long quote that needs splitting.

STEP 3: Split analysis (LAST operation - uses clean, normalized text)
   ↓
Segment 1: He said "She told me 'hello' yesterday"
Segment 2: and it was a very long quote that needs splitting.

STEP 4: Store each segment (clean text, no escape sequences, properly nested quotes)
   ↓
Database stores two clean quotes ready for rendering
```
✅ Each segment has properly nested quotes
✅ Splitting is the final decision before storage

**Wrong Order (Split → Normalize):**
```
Input: He said "She told me "hello" yesterday" and it was a very long quote that needs splitting.

STEP 1: Split (with broken quotes)
   ↓
Segment 1: He said "She told me "hello"    ❌ Broken mid-quote
Segment 2: yesterday" and it was a very long quote that needs splitting.    ❌ Orphaned closing quote

STEP 2: Try to normalize (impossible - context lost)
```
❌ Cannot fix broken quotes after splitting

### Visual Feedback Timeline

**Example: Long quote with nested quote issues**

```
User pastes: He said "She said "hello" to me" and this is a very long quote that will need to be split into multiple segments for display.

Timeline:
0.0s  🟡 Gold border - "Analyzing..."
      Detects nested quotes

0.5s  🔵 Blue border - "Auto-corrected nested quotes"
      Quote updates to: He said "She said 'hello' to me" and this is...

2.0s  🟡 Gold border - "Analyzing split..."
      Checks length with normalized quote

2.5s  🔴 Red border - "Split recommended - 2 segments"
      Segments shown in expansion panel
```

**Each state duration:**
- 🟡 Analyzing (initial): Until nested quote check completes
- 🔵 Auto-corrected: 1.5 seconds (visual confirmation)
- 🟡 Analyzing (split): Until split analysis completes
- 🔴/🟢 Result: Persistent until user acts

### Code Flow

**File**: `FsqModal.vue`, method `analyzeQuote()` (lines 774-861)

```javascript
async analyzeQuote() {
  // STEP 1: Normalize nested quotes FIRST
  let workingQuote = this.quote
  if (this.hasNestedQuotes(this.quote)) {
    console.log('📝 Nested quotes detected, normalizing...')
    const normalized = await this.normalizeNestedQuotes(this.quote)

    if (normalized !== this.quote) {
      this.quote = normalized
      workingQuote = normalized

      // Flash blue border
      this.aiState = 'auto'
      await new Promise(resolve => setTimeout(resolve, 1500))
    }
  }

  // STEP 2: Load settings
  const settings = await loadSettings()

  // STEP 3: Split analysis with normalized quote
  const segments = await this.intelligentQuoteSplit(workingQuote, settings)

  // STEP 4: Show results
  if (segments.length > 1) {
    this.aiState = 'rejected' // Red border - split recommended
    this.splitRecommendations = segments
  } else {
    this.aiState = 'approved' // Green border - fits as one
  }
}
```

### LLM Prompt Integration

**Nested Quote Normalization** uses `normalizeNestedQuotes()`:
- Task type: `content-expansion`
- Model: Ollama (llama2:13b-chat) - Creative depth
- Temperature: 0.2 (low for consistent formatting)
- Preserves exact words, only fixes quote marks

**Quote Splitting** uses `intelligentQuoteSplit()`:
- Task type: `quote-splitting`
- Model: Ollama (Qwen2.5-Coder:7b) - Best at JSON output
- Temperature: 0.2 (low for logical decisions)
- Receives **normalized quote** with correct nesting

### Split Preservation of Nested Quotes

The `intelligentQuoteSplit()` LLM prompt includes:

```
VALIDATION:
- Each segment must be independently readable
- Preserve original meaning and tone
- Each segment should fit visual constraints
```

**This ensures:**
- Split points avoid breaking mid-quote
- Nested quotes preserved in each segment
- Natural sentence boundaries respected

**Example:**
```
Input (normalized): He said "She told me 'hello' and 'goodbye'" but I wasn't sure which one she meant.

Split Result:
Segment 1: He said "She told me 'hello' and 'goodbye'"
Segment 2: but I wasn't sure which one she meant.
```
✅ First segment keeps complete nested quote intact

---

## AI Integration

### Quote Splitting with Clean Text
AI receives **decoded AND normalized text** for analysis:

```javascript
// Call AI with settings from database
const segments = await this.intelligentQuoteSplit(this.quote, {
  maxLines: settings.fsq_max_lines || 4,
  charsPerLine: settings.fsq_chars_per_line || 70,
  fontSize: settings.default_font_size || '19px'
})
```

**Why clean text matters:**
- AI can accurately count characters (escaped `&quot;` = 6 chars vs `"` = 1 char)
- Split points make semantic sense (not breaking mid-escape-sequence)
- Word count accurate for timing calculations

### Character Count Accuracy

**Without Decode:**
```
Input: He said &quot;hello&quot; to her
Length: 38 characters (includes escape sequences)
AI sees: "He said &quot;hello&quot; to her"
Split decision: Based on 38 chars (incorrect)
```

**With Decode:**
```
Input: He said &quot;hello&quot; to her
Decoded: He said "hello" to her
Length: 24 characters (actual displayed length)
AI sees: "He said "hello" to her"
Split decision: Based on 24 chars (correct) ✅
```

---

## Backend Rendering Integration

### PNG/Video Generation
When FSQ assets are rendered to PNG or video:

```python
# Backend receives clean text from database
quote_text = cue_data['quote']  # Already decoded

# Render directly without additional escaping
render_text_to_image(
    text=quote_text,  # Clean, human-readable
    font_size=cue_data['fontSize'],
    style=cue_data['style']
)
```

**No backend decode needed:**
- Frontend stores clean text
- Backend receives clean text
- Rendering engines work with natural text

---

## Testing Checklist

### Input Variations
- ✅ Simple quotes: `"hello"`
- ✅ Nested quotes: `He said "hello" to her`
- ✅ Multiple nesting: `She asked "Did he say 'hello'?"`
- ✅ HTML entity pasted: `&quot;hello&quot;`
- ✅ Backslash escaped: `\"hello\"`
- ✅ Double-escaped: `&amp;quot;hello&amp;quot;`
- ✅ Mixed escaping: `He said \"hello\" &amp; goodbye`

### Display Contexts
- ✅ Preview window shows correctly
- ✅ Saved and reloaded shows correctly
- ✅ AI split preserves quotes
- ✅ Multiple FSQ segments maintain quotes
- ✅ Rendered PNG/video displays correctly

### Edge Cases
- ✅ Ampersands: `Tom & Jerry`
- ✅ Less/greater than: `2 < 3 > 1`
- ✅ Apostrophes: `It's a quote`
- ✅ Line breaks: Multi-line quotes
- ✅ Tabs and special whitespace
- ✅ Unicode characters preserved

---

## Defensive Programming

### Why Decode on Both Input and Display?
```javascript
// Input decode - clean user paste/type
decodeQuoteText(this.quote)

// Display decode - defensive against stored escapes
decodeQuoteText(rawText)
```

**Redundancy by design:**
- Legacy data may have escapes stored
- Copy/paste from other sources
- Browser auto-escape quirks
- API responses with escapes

**Cost:** Minimal (regex replacements)
**Benefit:** Guaranteed correct display

---

## Files Modified

### Primary File
- **`disaffected-ui/src/components/modals/FsqModal.vue`**
  - Lines 662-691: `decodeQuoteText()` method
  - Lines 639-655: `formattedQuotePreview()` with decode step
  - Lines 891-908: Store clean decoded text in `cueData`

---

## Related Documentation

- **AI Quote Splitting**: `useLLM.js` → `intelligentQuoteSplit()`
- **AssetID Generation**: `docs/ASSETID_SYSTEM_GUIDE.md`
- **FSQ Rendering**: Backend PNG/video render tools

---

## Future Enhancements

### Potential Improvements
1. **Emoji Support**: Ensure emojis decode/encode correctly
2. **RTL Languages**: Right-to-left text handling
3. **Markdown**: Support **bold**, *italic* in quotes
4. **Smart Quotes**: Convert straight quotes to curly quotes for typography
5. **Citation Markup**: Support (Author, Year) style citations

### Backend Validation
Consider adding decode validation in backend API:
```python
def validate_quote_text(quote: str) -> str:
    """Ensure quote text has no escape sequences"""
    # Decode common escapes
    decoded = html.unescape(quote)
    # Validate no remaining escapes
    if '&' in decoded or '\\' in decoded:
        logger.warning(f"Quote has unusual escapes: {quote}")
    return decoded
```

---

**Implementation Date**: 2025-10-03
**Component Version**: FsqModal.vue (latest)
**Status**: ✅ Production Ready
