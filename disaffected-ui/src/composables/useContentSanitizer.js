/**
 * Content Sanitizer Composable
 *
 * Pure utility functions for cleaning, sanitizing, and transforming HTML/markdown content.
 * These functions have zero component state dependency — they take input and return output.
 *
 * Usage (Options API setup()):
 *   const { stripYamlFrontmatter, extractYamlFrontmatter, stripRevisionMarkup } = useContentSanitizer()
 *   return { stripYamlFrontmatter, extractYamlFrontmatter, stripRevisionMarkup }
 *
 * Then available as this.stripYamlFrontmatter(...) etc. in methods block.
 */

export function useContentSanitizer() {

  /**
   * Strip revision proposal markup (rev-block, rev-add, rev-kill, etc.)
   * injected by Alt+/ and Alt+. — must never persist into saved content.
   *
   * Unresolved proposals are treated as REJECTED: the original text
   * (inside rev-kill) is kept, and the proposed replacement (rev-add)
   * is discarded. This is the safe default — nothing the user wrote
   * is lost.
   */
  function stripRevisionMarkup(html) {
    if (!html) return html;
    if (!html.includes('<rev')) return html;
    let result = html;
    // Raw markdown form: <rev user="..." ts="...">original|replacement</rev>
    // Treat unresolved as rejected: keep original (left of pipe)
    result = result.replace(/<rev\s+[^>]*>([\s\S]*?)<\/rev>/gi, (match, inner) => {
      const pipeIdx = inner.indexOf('|');
      if (pipeIdx === -1) return inner; // kill-only: keep original
      return inner.substring(0, pipeIdx); // keep original, discard replacement
    });
    // DOM-rendered form: strip UI chrome, keep original, discard proposed
    result = result.replace(/<rev-actions>[\s\S]*?<\/rev-actions>/gi, '');
    result = result.replace(/<rev-meta[^>]*>[\s\S]*?<\/rev-meta>/gi, '');
    result = result.replace(/<rev-btn[^>]*>[\s\S]*?<\/rev-btn>/gi, '');
    result = result.replace(/<rev-add[^>]*>[\s\S]*?<\/rev-add>/gi, '');
    result = result.replace(/<rev-kill[^>]*>([\s\S]*?)<\/rev-kill>/gi, '$1');
    result = result.replace(/<rev-block[^>]*>([\s\S]*?)<\/rev-block>/gi, '$1');
    return result;
  }

  // Strip YAML frontmatter from content for visual display
  function stripYamlFrontmatter(content) {
    if (!content) return '';

    // Helper to detect both '---' and '- - -' (sanitized) frontmatter delimiters
    const isFmDelimiter = (line) => {
      const t = line.trim();
      return t === '---' || t === '- - -';
    };

    // Check if content starts with YAML frontmatter (--- or - - -)
    const trimmed = content.trim();
    if (trimmed.startsWith('---') || trimmed.startsWith('- - -')) {
      const lines = content.split('\n');
      let frontmatterEnd = -1;
      let bodyStart = -1;

      // Find the closing delimiter (skip the first line which is the opening)
      for (let i = 1; i < lines.length; i++) {
        if (isFmDelimiter(lines[i])) {
          frontmatterEnd = i;
          bodyStart = i + 1;
          break;
        }
      }

      // If we found the closing ---, look for actual body content
      if (frontmatterEnd > 0 && bodyStart < lines.length) {
        // Skip empty lines and find the first real content
        for (let i = bodyStart; i < lines.length; i++) {
          const line = lines[i].trim();
          // If this line looks like YAML (key: value), skip it - it's malformed frontmatter
          if (line && line.match(/^[a-zA-Z_][a-zA-Z0-9_]*:\s*.+$/)) {
            console.warn(`🔧 Stripping malformed YAML line: "${line}"`);
            continue;
          }
          // If this line doesn't look like YAML, this is where body content starts
          if (line && !line.match(/^[a-zA-Z_][a-zA-Z0-9_]*:\s*.+$/)) {
            return lines.slice(i).join('\n').trim();
          }
          // If it's an empty line, include it but keep looking
          if (!line) {
            bodyStart = i;
          }
        }

        // If we didn't find any body content, return empty string
        return '';
      }
    }

    // If no frontmatter found, return original content
    return content;
  }

  // Extract YAML frontmatter from content
  function extractYamlFrontmatter(content) {
    if (!content) return '';

    // Helper to detect both '---' and '- - -' (sanitized) frontmatter delimiters
    const isFmDelimiter = (line) => {
      const t = line.trim();
      return t === '---' || t === '- - -';
    };

    const trimmed = content.trim();
    if (trimmed.startsWith('---') || trimmed.startsWith('- - -')) {
      const lines = content.split('\n');
      let frontmatterEnd = -1;

      // Find the closing delimiter (skip the first line which is the opening)
      for (let i = 1; i < lines.length; i++) {
        if (isFmDelimiter(lines[i])) {
          frontmatterEnd = i;
          break;
        }
      }

      // If we found the closing ---, return the frontmatter including delimiters
      if (frontmatterEnd > 0) {
        return lines.slice(0, frontmatterEnd + 1).join('\n');
      }
    }

    return '';
  }

  return {
    stripRevisionMarkup,
    stripYamlFrontmatter,
    extractYamlFrontmatter
  }
}
