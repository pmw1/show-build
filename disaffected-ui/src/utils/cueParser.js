/**
 * Cue Block Parser
 * Parses markdown content containing cue blocks and converts them to card data
 */

export class CueParser {

  /**
   * Parse content and extract cue blocks along with text segments
   * @param {string} content - Raw markdown content containing cue blocks
   * @returns {Array} Array of content segments (text or cue card data)
   */
  static parseContent(content) {
    if (!content || typeof content !== 'string') {
      return [];
    }

    const segments = [];
    const cueBlockPattern = /<!-- Begin Cue -->([\s\S]*?)<!-- End Cue -->/g;
    let lastIndex = 0;
    let match;

    while ((match = cueBlockPattern.exec(content)) !== null) {
      // Add text content before this cue block
      const textBefore = content.slice(lastIndex, match.index);
      if (textBefore.trim()) {
        const textSegments = this.parseTextSegments(textBefore);
        segments.push(...textSegments);
      }

      // Parse the cue block
      const cueContent = match[1];
      const cueData = this.parseCueBlock(cueContent);
      if (cueData) {
        segments.push({
          type: 'cue',
          cueType: cueData.type,
          data: cueData
        });
      }

      lastIndex = match.index + match[0].length;
    }

    // Add any remaining text after the last cue block
    const textAfter = content.slice(lastIndex);
    if (textAfter.trim()) {
      const textSegments = this.parseTextSegments(textAfter);
      segments.push(...textSegments);
    }

    return segments;
  }

  /**
   * Parse text content into paragraphs with speaker detection
   * @param {string} textContent - Raw text content to parse
   * @returns {Array} Array of text segments with speaker information
   */
  static parseTextSegments(textContent) {
    if (!textContent || !textContent.trim()) {
      return [];
    }

    const segments = [];

    // Check if content already has <p> tags with speaker classes
    const existingParagraphs = textContent.match(/<p(?:\s+class="([^"]*)")?[^>]*>([\s\S]*?)<\/p>/g);

    if (existingParagraphs) {
      // Parse each paragraph tag into individual speaker segments
      existingParagraphs.forEach(paragraphHtml => {
        // Extract class, data-needs-attention, data-flag-note, and content from paragraph
        const match = paragraphHtml.match(/<p(?:\s+class="([^"]*)")?([^>]*)>([\s\S]*?)<\/p>/);
        if (match) {
          const speaker = match[1] || 'josh'; // Default to josh if no class
          const otherAttributes = match[2] || '';
          const content = match[3].trim();

          // Check for data-needs-attention attribute
          const needsAttention = otherAttributes.includes('data-needs-attention="true"') ||
                                 otherAttributes.includes("data-needs-attention='true'");

          // Extract data-flag-note attribute value
          const flagNoteMatch = otherAttributes.match(/data-flag-note="([^"]*)"/);
          const flagNote = flagNoteMatch ? flagNoteMatch[1] : '';

          // Always push segment, even if empty (allows editing empty paragraphs)
          if (content) {
            // Split content on line breaks to create separate paragraphs
            const contentParagraphs = content.split(/\n\s*\n/).filter(p => p.trim());
            if (contentParagraphs.length > 1) {
              // Multiple paragraphs found - split them
              contentParagraphs.forEach(paragraph => {
                segments.push({
                  type: 'text',
                  content: paragraph.trim(),
                  speaker: speaker,
                  needsParagraphTags: true,
                  needsAttention: needsAttention,
                  flagNote: flagNote
                });
              });
            } else {
              // Single paragraph
              segments.push({
                type: 'text',
                content: content,
                speaker: speaker,
                needsParagraphTags: true,
                needsAttention: needsAttention,
                flagNote: flagNote
              });
            }
          } else {
            // Empty paragraph - still create segment for editing
            segments.push({
              type: 'text',
              content: '',
              speaker: speaker,
              needsParagraphTags: true,
              needsAttention: needsAttention,
              flagNote: flagNote
            });
          }
        }
      });
    } else {
      // Parse raw text into paragraphs and apply speaker detection
      const paragraphs = textContent.split(/\n\s*\n/).filter(p => p.trim());

      for (const paragraph of paragraphs) {
        const cleanParagraph = paragraph.trim();
        if (!cleanParagraph) continue;

        // Detect speaker (default to 'josh' for now)
        const speaker = this.detectSpeaker(cleanParagraph);

        segments.push({
          type: 'text',
          content: cleanParagraph,
          speaker: speaker,
          needsParagraphTags: true
        });
      }
    }

    return segments;
  }

  /**
   * Detect speaker from paragraph content
   * @param {string} paragraph - Paragraph text
   * @returns {string} Speaker identifier
   */
  // eslint-disable-next-line no-unused-vars
  static detectSpeaker(paragraph) {
    // For now, default to 'josh' but this can be enhanced with:
    // - Pattern matching for speaker indicators
    // - Context analysis
    // - User preferences
    // - AI-based speaker detection

    // Example patterns that could indicate different speakers:
    if (paragraph.match(/^(GUEST|CALLER|INTERVIEW)/i)) return 'guest';
    if (paragraph.match(/^(ANNOUNCER|NARRATOR)/i)) return 'announcer';

    return 'josh'; // Default speaker
  }

  /**
   * Parse individual cue block content
   * @param {string} cueContent - Content between Begin/End Cue markers
   * @returns {Object|null} Parsed cue data object
   */
  static parseCueBlock(cueContent) {
    if (!cueContent) return null;

    const cueData = {};

    // Parse field lines [Field: Value]
    // Use a more sophisticated pattern that handles JSON arrays containing brackets
    // Pattern matches: [FieldName: value] where value can contain balanced brackets
    const lines = cueContent.split('\n');

    for (const line of lines) {
      // Match field pattern [FieldName: Value]
      const fieldMatch = line.match(/^\s*\[([^:]+):\s*(.*)\]\s*$/);
      if (!fieldMatch) continue;

      const fieldName = fieldMatch[1].trim();
      let fieldValue = fieldMatch[2].trim();

      // Strip surrounding quotes from Quote field (both single and double)
      if (fieldName.toLowerCase() === 'quote' && fieldValue) {
        // Remove leading quote
        if (fieldValue.startsWith('"') || fieldValue.startsWith("'")) {
          fieldValue = fieldValue.substring(1);
        }
        // Remove trailing quote
        if (fieldValue.endsWith('"') || fieldValue.endsWith("'")) {
          fieldValue = fieldValue.substring(0, fieldValue.length - 1);
        }
      }

      // Convert field names to camelCase and store values
      const camelFieldName = this.toCamelCase(fieldName);
      cueData[camelFieldName] = fieldValue || '';
    }

    // Extract embedded image tag for GFX/IMG cues
    const imgMatch = cueContent.match(/<img[^>]+src="([^"]+)"[^>]*>/);
    if (imgMatch) {
      cueData.imageTag = imgMatch[0];
      cueData.imageSrc = imgMatch[1];
    }

    // Extract analysis metadata (for async LLM analysis persistence)
    cueData.analysisState = this.extractAnalysisState(cueData);
    cueData.analysisField = cueData.analysisField || null;
    cueData.analysisRecommendations = this.parseAnalysisRecommendations(cueData.analysisRecommendations);

    // Ensure we have at least a type
    if (!cueData.type) {
      return null;
    }

    return cueData;
  }

  /**
   * Extract analysis state from cue data
   * @param {Object} cueData - Parsed cue data
   * @returns {string|null} 'analyzing' | 'needs_review' | 'complete' | null
   */
  static extractAnalysisState(cueData) {
    const state = cueData.analysisState;
    if (!state) return null;

    const validStates = ['analyzing', 'needs_review', 'complete', 'error', 'cancelled'];
    return validStates.includes(state) ? state : null;
  }

  /**
   * Parse analysis recommendations from JSON string
   * @param {string} recommendationsJson - JSON string of recommendations
   * @returns {Object|null} Parsed recommendations or null
   */
  static parseAnalysisRecommendations(recommendationsJson) {
    if (!recommendationsJson) return null;

    try {
      return JSON.parse(recommendationsJson);
    } catch (error) {
      console.error('Failed to parse analysis recommendations:', error);
      return null;
    }
  }

  /**
   * Convert field name to camelCase
   * Handles PascalCase (FontSize), spaces (Font Size), and snake_case (font_size)
   * @param {string} fieldName - Field name to convert
   * @returns {string} camelCase field name
   */
  static toCamelCase(fieldName) {
    // First, handle PascalCase by inserting spaces before uppercase letters
    // This converts "FontSize" → "Font Size", "AssetID" → "Asset ID"
    const spacedName = fieldName.replace(/([a-z])([A-Z])/g, '$1 $2');

    return spacedName
      .split(/[\s_-]+/)
      .map((word, index) => {
        if (index === 0) {
          return word.toLowerCase();
        }
        return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
      })
      .join('');
  }

  /**
   * Check if content contains cue blocks
   * @param {string} content - Content to check
   * @returns {boolean} True if content contains cue blocks
   */
  static containsCueBlocks(content) {
    if (!content) return false;
    return /<!-- Begin Cue -->/.test(content);
  }

  /**
   * Get cue types that should render as image cards
   * @returns {Array} Array of cue types that display images
   */
  static getImageCueTypes() {
    return ['IMG', 'GFX'];
  }

  /**
   * Check if a cue type should render as an image card
   * @param {string} cueType - Cue type to check
   * @returns {boolean} True if should render as image card
   */
  static isImageCueType(cueType) {
    return this.getImageCueTypes().includes(cueType?.toUpperCase());
  }

  /**
   * Generate card title for cue
   * @param {Object} cueData - Parsed cue data
   * @returns {string} Card title
   */
  static generateCardTitle(cueData) {
    if (!cueData) return 'Unknown Cue';

    const type = cueData.type || 'Unknown';
    const slug = cueData.slug || '';

    if (slug) {
      return `${type}: ${slug}`;
    }

    return type;
  }

  /**
   * Generate card subtitle for cue
   * @param {Object} cueData - Parsed cue data
   * @returns {string} Card subtitle
   */
  static generateCardSubtitle(cueData) {
    if (!cueData) return '';

    const description = cueData.description;
    const assetId = cueData.assetId;

    if (description) {
      return description;
    }

    if (assetId) {
      return `AssetID: ${assetId}`;
    }

    return '';
  }

  /**
   * Format cue data for display in script mode
   * @param {Object} cueData - Parsed cue data
   * @returns {Object} Formatted data for card display
   */
  static formatForCard(cueData) {
    if (!cueData) return null;

    // Parse thumbnailOptions if it's a JSON string
    // Check both camelCase (thumbnailOptions) and lowercase (thumbnailoptions) variants
    let thumbnailOptions = null;
    const rawThumbnailOptions = cueData.thumbnailOptions || cueData.thumbnailoptions;
    if (rawThumbnailOptions) {
      try {
        thumbnailOptions = typeof rawThumbnailOptions === 'string'
          ? JSON.parse(rawThumbnailOptions)
          : rawThumbnailOptions;
      } catch (e) {
        console.warn('Failed to parse thumbnailOptions:', e);
        thumbnailOptions = null;
      }
    }

    return {
      id: `cue-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: cueData.type,
      title: this.generateCardTitle(cueData),
      subtitle: this.generateCardSubtitle(cueData),
      assetId: cueData.assetId || cueData.assetid, // Check both camelCase and lowercase
      slug: cueData.slug,
      description: cueData.description,
      mediaUrl: cueData.mediaUrl || cueData.mediaurl, // Check both camelCase and lowercase (MediaURL -> mediaurl)
      thumbnailUrl: cueData.thumbnailUrl || cueData.thumbnailurl,  // SOT thumbnail (primary) - check both cases
      thumbnailOptions: thumbnailOptions,   // All 15 thumbnail URLs as array
      audioUrl: cueData.audioUrl || cueData.audiourl,  // SOT audio - check both cases
      processingStatus: cueData.processingStatus || cueData.processingstatus, // SOT processing status
      transcription: cueData.transcription, // SOT transcription text
      outcue: cueData.outcue, // SOT outcue (last 5 words of transcription)
      imageSrc: cueData.imageSrc,
      imageTag: cueData.imageTag,
      duration: cueData.duration,
      quote: cueData.quote,
      attribution: cueData.attribution,
      // FSQ style fields
      fontSize: cueData.fontSize,
      fontFamily: cueData.fontFamily,
      boxHeight: cueData.boxHeight,
      boxOpacity: cueData.boxOpacity,
      lineSpacing: cueData.lineSpacing,
      alignment: cueData.alignment || cueData.style, // 'style' is legacy field name for alignment
      isImageType: this.isImageCueType(cueData.type),
      analysisState: cueData.analysisState,
      analysisField: cueData.analysisField,
      analysisRecommendations: cueData.analysisRecommendations,
      enumerator: cueData.enumerator,  // Enumeration number for display
      needsAttention: cueData.needsAttention === 'true' || cueData.needsAttention === true, // Parse boolean from string
      flagNote: cueData.flagNote || '', // Attention note for flagged cues
      rawData: cueData
    };
  }

  /**
   * Convert text segments back to properly formatted content
   * @param {Array} segments - Array of content segments
   * @returns {string} Formatted content with proper paragraph tags
   */
  static reconstructContent(segments) {
    const result = [];
    let i = 0;

    while (i < segments.length) {
      const segment = segments[i];

      if (segment.type === 'text' && segment.needsParagraphTags) {
        // Create individual paragraph for each text segment
        const speaker = segment.speaker;
        const needsAttentionAttr = segment.needsAttention ? ' data-needs-attention="true"' : '';
        const flagNoteAttr = segment.flagNote ? ` data-flag-note="${segment.flagNote.replace(/"/g, '&quot;')}"` : '';
        result.push(`<p class="${speaker}"${needsAttentionAttr}${flagNoteAttr}>${segment.content}</p>`);
        i++;
      } else if (segment.type === 'text') {
        if (segment.hasStructuredParagraphs) {
          // Already has proper paragraph structure
          result.push(segment.content);
        } else {
          // Fallback to plain text
          result.push(segment.content);
        }
        i++;
      } else if (segment.type === 'cue') {
        // Convert cue data back to cue block format
        result.push(this.formatCueToMarkdown(segment.data.rawData));
        i++;
      } else {
        i++;
      }
    }

    return result.join('\n\n');
  }

  /**
   * Format cue data back to markdown cue block format
   * @param {Object} cueData - Cue data to format
   * @returns {string} Formatted cue block
   */
  static formatCueToMarkdown(cueData) {
    if (!cueData) return '';

    let cueBlock = '<!-- Begin Cue -->\n';

    // Field order priority: important fields first, analysis fields last
    const fieldOrder = ['type', 'assetId', 'slug', 'duration', 'description'];
    const analysisFields = ['analysisState', 'analysisField', 'analysisRecommendations'];

    // Add priority fields first
    fieldOrder.forEach(key => {
      if (cueData[key] && key !== 'imageTag' && key !== 'imageSrc') {
        const displayKey = this.formatFieldForDisplay(key);
        cueBlock += `[${displayKey}: ${cueData[key]}]\n`;
      }
    });

    // Add remaining fields (excluding special fields and analysis fields)
    Object.keys(cueData).forEach(key => {
      if (!fieldOrder.includes(key) &&
          !analysisFields.includes(key) &&
          key !== 'imageTag' &&
          key !== 'imageSrc' &&
          cueData[key]) {
        const displayKey = this.formatFieldForDisplay(key);
        cueBlock += `[${displayKey}: ${cueData[key]}]\n`;
      }
    });

    // Add analysis metadata last (if present)
    if (cueData.analysisState) {
      cueBlock += `[Analysis State: ${cueData.analysisState}]\n`;
    }
    if (cueData.analysisField) {
      cueBlock += `[Analysis Field: ${cueData.analysisField}]\n`;
    }
    if (cueData.analysisRecommendations) {
      const recommendationsJson = typeof cueData.analysisRecommendations === 'string'
        ? cueData.analysisRecommendations
        : JSON.stringify(cueData.analysisRecommendations);
      cueBlock += `[Analysis Recommendations: ${recommendationsJson}]\n`;
    }

    // Add image tag if it exists
    if (cueData.imageTag) {
      cueBlock += `${cueData.imageTag}\n`;
    }

    cueBlock += '<!-- End Cue -->';
    return cueBlock;
  }

  /**
   * Convert camelCase field name back to display format
   * @param {string} camelCaseField - Field name in camelCase
   * @returns {string} Formatted field name for display
   */
  static formatFieldForDisplay(camelCaseField) {
    return camelCaseField
      .replace(/([A-Z])/g, ' $1')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  /**
   * Get available speaker options
   * @returns {Array} Array of speaker options
   */
  static getSpeakerOptions() {
    return [
      { value: 'josh', label: 'Josh', color: '#1976d2' },
      { value: 'guest', label: 'Guest', color: '#388e3c' },
      { value: 'caller', label: 'Caller', color: '#f57c00' },
      { value: 'announcer', label: 'Announcer', color: '#7b1fa2' },
      { value: 'narrator', label: 'Narrator', color: '#5d4037' },
      { value: 'host', label: 'Host', color: '#1976d2' }
    ];
  }

  /**
   * Get speaker color for styling
   * @param {string} speaker - Speaker identifier
   * @returns {string} Color code for speaker
   */
  static getSpeakerColor(speaker) {
    const options = this.getSpeakerOptions();
    const option = options.find(opt => opt.value === speaker);
    return option ? option.color : '#666666';
  }
}

export default CueParser;