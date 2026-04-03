/**
 * Collapse Mode Composable
 *
 * Pure utility functions for collapse mode display in the script editor.
 * These functions compute display values for collapsed paragraph/cue views.
 *
 * Usage (Options API setup()):
 *   const { getCollapsedLineRange, getCollapsedFirstWords, ... } = useCollapseMode()
 *   return { getCollapsedLineRange, getCollapsedFirstWords, ... }
 *
 * Note: getCollapsedLineRange requires getAbsoluteLineNumber and getLineCount
 * to be available on the component instance (passed as params).
 */

export function useCollapseMode() {

  /**
   * Convert hex color to HSL
   */
  function hexToHsl(hex) {
    // Remove # if present
    hex = hex.replace(/^#/, '');

    // Parse RGB values
    const r = parseInt(hex.substring(0, 2), 16) / 255;
    const g = parseInt(hex.substring(2, 4), 16) / 255;
    const b = parseInt(hex.substring(4, 6), 16) / 255;

    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h, s, l = (max + min) / 2;

    if (max === min) {
      h = s = 0; // achromatic
    } else {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
        case g: h = ((b - r) / d + 2) / 6; break;
        case b: h = ((r - g) / d + 4) / 6; break;
      }
    }

    return { h: h * 360, s: s * 100, l: l * 100 };
  }

  /**
   * Get the first 6 words of paragraph content for collapsed mode (left-aligned)
   */
  function getCollapsedFirstWords(content) {
    if (!content) return '(empty)';

    // Strip HTML tags for word counting
    const textOnly = content.replace(/<[^>]*>/g, '').trim();
    if (!textOnly) return '(empty)';

    const words = textOnly.split(/\s+/).filter(w => w.length > 0);

    if (words.length <= 6) {
      return words.join(' ');
    }

    return words.slice(0, 6).join(' ');
  }

  /**
   * Get the last 6 words of paragraph content for collapsed mode (right-aligned)
   */
  function getCollapsedLastWords(content) {
    if (!content) return '';

    // Strip HTML tags for word counting
    const textOnly = content.replace(/<[^>]*>/g, '').trim();
    if (!textOnly) return '';

    const words = textOnly.split(/\s+/).filter(w => w.length > 0);

    if (words.length <= 6) {
      return ''; // Don't show last words if content is short
    }

    return words.slice(-6).join(' ');
  }

  /**
   * Get the style for a collapsed cue based on its type
   * Uses the cue type colors for the border, darkened 30% for background
   */
  function getCollapsedCueStyle(cueType) {
    const typeColors = {
      'IMG': '#4CAF50',
      'GFX': '#9C27B0',
      'FSQ': '#FF9800',
      'SOT': '#2196F3',
      'VO': '#00BCD4',
      'NAT': '#795548',
      'RIF': '#E91E63',
      'PKG': '#607D8B',
      'DIR': '#FF5722',
      'NOTE': '#FF5722',
      'BUMP': '#3F51B5',
      'STING': '#8BC34A',
      'VOX': '#009688',
      'MUS': '#673AB7',
      'LIVE': '#F44336'
    };

    const color = typeColors[cueType] || '#757575';

    // Convert to HSL and darken by 30% (reduce lightness)
    const hsl = hexToHsl(color);
    // Darken: reduce lightness by 30% of its current value, then use with alpha for background
    const darkenedL = Math.max(0, hsl.l * 0.7); // 30% darker
    const bgColor = `hsla(${hsl.h}, ${hsl.s}%, ${darkenedL}%, 0.25)`;

    return {
      borderLeft: `4px solid ${color}`,
      backgroundColor: bgColor
    };
  }

  /**
   * Get the outcue from cue data (for SOT - last 5 words of transcription)
   */
  function getCollapsedOutcue(cueData) {
    if (!cueData) return '';

    // If outcue is already set, use it
    if (cueData.outcue) return cueData.outcue;

    // For SOT, extract from transcription
    if (cueData.type === 'SOT' && cueData.transcription) {
      const words = cueData.transcription.trim().split(/\s+/);
      if (words.length > 5) {
        return '...' + words.slice(-5).join(' ');
      }
      return cueData.transcription;
    }

    return '';
  }

  /**
   * Get the line range for a collapsed paragraph display.
   * Returns a string like "33-43" representing the absolute line numbers.
   *
   * NOTE: This function needs getAbsoluteLineNumber and getLineCount from the component.
   * It is returned as a factory that takes these two functions.
   */
  function makeGetCollapsedLineRange(getAbsoluteLineNumber, getLineCount) {
    return function getCollapsedLineRange(segmentIndex) {
      const startLine = getAbsoluteLineNumber(segmentIndex, 1);
      const lineCount = getLineCount(segmentIndex);
      const endLine = startLine + lineCount - 1;

      if (lineCount === 1) {
        return `${startLine}`;
      }
      return `${startLine}-${endLine}`;
    };
  }

  return {
    hexToHsl,
    getCollapsedFirstWords,
    getCollapsedLastWords,
    getCollapsedCueStyle,
    getCollapsedOutcue,
    makeGetCollapsedLineRange
  }
}
