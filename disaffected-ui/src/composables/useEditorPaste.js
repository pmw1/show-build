/**
 * Editor Paste Composable
 *
 * Pure utility functions for parsing pasted content from various sources
 * (Google Docs, Word, plain text, generic HTML).
 *
 * The main paste handler (handleContentEditablePaste) stays in the component
 * because it's deeply coupled with component state. These are the pure parsing
 * functions it delegates to.
 *
 * Usage (Options API setup()):
 *   const { parseGoogleDocsPaste, cleanGoogleDocsNode, parseGenericPaste } = useEditorPaste()
 *   return { parseGoogleDocsPaste, cleanGoogleDocsNode, parseGenericPaste }
 */

export function useEditorPaste() {

  /**
   * Recursively clean a Google Docs DOM node, preserving bold/italic
   * but stripping spans, styles, and Google-specific markup.
   * Operates on live DOM — no innerHTML regex that would trigger re-parse.
   */
  function cleanGoogleDocsNode(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      return node.textContent;
    }

    if (node.nodeType !== Node.ELEMENT_NODE) {
      return '';
    }

    const tag = node.tagName.toLowerCase();

    // Check for semantic formatting via styles (Google Docs uses inline styles, not tags)
    const style = node.getAttribute('style') || '';
    const isBold = style.includes('font-weight:700') || style.includes('font-weight: 700') ||
                   style.includes('font-weight:bold') || style.includes('font-weight: bold');
    const isItalic = style.includes('font-style:italic') || style.includes('font-style: italic');

    // Recursively clean children
    let childContent = '';
    for (const child of node.childNodes) {
      childContent += cleanGoogleDocsNode(child);
    }

    // Replace &nbsp; with regular spaces
    childContent = childContent.replace(/\u00A0/g, ' ');

    if (!childContent.trim()) {
      return '';
    }

    // Wrap in formatting tags if this node carried bold/italic via styles
    // But only for <span> elements — <b> and <i> tags are preserved directly below
    if (tag === 'span') {
      let result = childContent;
      if (isBold) result = '<b>' + result + '</b>';
      if (isItalic) result = '<i>' + result + '</i>';
      return result;
    }

    // Preserve semantic tags
    if (tag === 'b' || tag === 'strong') {
      // Google Docs sometimes uses <b style="font-weight:normal"> as a wrapper — don't wrap in <b> if normal weight
      if (style.includes('font-weight:normal') || style.includes('font-weight: normal')) {
        return childContent;
      }
      return '<b>' + childContent + '</b>';
    }
    if (tag === 'i' || tag === 'em') {
      return '<i>' + childContent + '</i>';
    }
    if (tag === 'u') {
      return '<u>' + childContent + '</u>';
    }

    // For <p>, <div>, <a>, and everything else — return the inner content unwrapped
    // (paragraph boundaries are handled by the caller iterating over <p> elements)
    if (tag === 'a') {
      const href = node.getAttribute('href');
      if (href && !href.startsWith('https://www.google.com/url')) {
        return '<a href="' + href + '">' + childContent + '</a>';
      }
      // Google Docs wraps links in google.com redirects — extract the real URL
      if (href) {
        try {
          const realUrl = new URL(href).searchParams.get('q');
          if (realUrl) {
            return '<a href="' + realUrl + '">' + childContent + '</a>';
          }
        } catch { /* ignore */ }
      }
      return childContent;
    }

    return childContent;
  }

  /**
   * Google Docs-specific paste parser.
   * Walks the DOM tree structurally instead of using regex on innerHTML.
   * This prevents browser re-parse from merging/destroying paragraph boundaries.
   */
  function parseGoogleDocsPaste(htmlText, plainText) {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlText;

    // Step 1: Find the docs-internal-guid wrapper (Google Docs always wraps in one)
    const gdocWrapper = tempDiv.querySelector('[id^="docs-internal-guid"]');
    const root = gdocWrapper || tempDiv;

    // Step 2: Walk direct children to find paragraph boundaries
    // Google Docs structure is typically:
    //   <b style="font-weight:normal" id="docs-internal-guid-xxx">
    //     <p dir="ltr" style="..."><span style="...">text</span></p>
    //     <p dir="ltr" style="..."><span style="...">text</span></p>
    //   </b>
    // OR sometimes:
    //   <span id="docs-internal-guid-xxx">
    //     <p dir="ltr"><span>text</span></p>
    //   </span>

    const paragraphs = [];

    // Collect leaf <p> elements — Google Docs always uses <p> for paragraphs
    const pElements = root.querySelectorAll('p');

    if (pElements.length > 0) {
      pElements.forEach(p => {
        // Clean each paragraph individually by walking its child nodes
        const cleanedContent = cleanGoogleDocsNode(p);
        if (cleanedContent.trim()) {
          paragraphs.push(cleanedContent.trim());
        }
      });
    }

    // If no <p> elements found, try direct children (some Google Docs variants)
    if (paragraphs.length === 0) {
      for (const child of root.children) {
        const cleanedContent = cleanGoogleDocsNode(child);
        if (cleanedContent.trim()) {
          paragraphs.push(cleanedContent.trim());
        }
      }
    }

    // Sanity check: compare against plain text paragraph count
    const plainParagraphs = plainText
      ? plainText.split(/\n\s*\n/).map(p => p.trim()).filter(p => p.length > 0)
      : [];

    if (paragraphs.length === 0 && plainParagraphs.length > 0) {
      // HTML parsing failed entirely — fall back to plain text
      console.warn('📋 Google Docs HTML parse found 0 paragraphs, falling back to plain text (' + plainParagraphs.length + ' paragraphs)');
      return plainParagraphs;
    }

    if (plainParagraphs.length > paragraphs.length && paragraphs.length <= 1) {
      // HTML collapsed everything into one blob — plain text is more reliable
      console.warn('📋 Google Docs HTML collapsed to', paragraphs.length, 'but plain text has', plainParagraphs.length, '— using plain text');
      return plainParagraphs;
    }

    console.log('📋 Google Docs parser extracted', paragraphs.length, 'paragraphs (plain text had', plainParagraphs.length, ')');
    return paragraphs.length > 0 ? paragraphs : [plainText.trim()];
  }

  /**
   * Generic (non-Google Docs) paste parser.
   * Used for plain text, Word, and other HTML sources.
   */
  function parseGenericPaste(htmlText, plainText) {
    const interfaceSettings = JSON.parse(localStorage.getItem('showbuild_interface_settings') || '{}');
    const pastePlainTextOnly = interfaceSettings.pastePlainTextOnly === true;

    let paragraphs = [];

    if (pastePlainTextOnly || !htmlText) {
      paragraphs = plainText.split(/\n\s*\n/).map(p => p.trim()).filter(p => p.length > 0);
      console.log('📋 Plain text mode - found', paragraphs.length, 'paragraphs');
    } else {
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = htmlText;

      // Remove style attributes
      tempDiv.querySelectorAll('[style]').forEach(el => el.removeAttribute('style'));

      // Strip spans
      tempDiv.querySelectorAll('span').forEach(span => {
        while (span.firstChild) {
          span.parentNode.insertBefore(span.firstChild, span);
        }
        span.remove();
      });

      // Find paragraphs — use only leaf-level <p> elements (avoid double-counting nested <div><p>)
      const pElements = tempDiv.querySelectorAll('p');
      if (pElements.length > 0) {
        pElements.forEach(p => {
          const content = p.textContent.trim();
          if (content) {
            // Get innerHTML but strip div tags
            let html = p.innerHTML.trim()
              .replace(/<div[^>]*>/gi, '')
              .replace(/<\/div>/gi, '')
              .replace(/&nbsp;/gi, ' ');
            paragraphs.push(html);
          }
        });
      }

      // Fallback: if no <p> elements, try <div> elements that don't contain other <div>/<p>
      if (paragraphs.length === 0) {
        const divElements = tempDiv.querySelectorAll('div');
        divElements.forEach(div => {
          // Only use leaf divs (no nested block elements)
          if (!div.querySelector('div, p')) {
            const content = div.textContent.trim();
            if (content) {
              paragraphs.push(div.innerHTML.trim().replace(/&nbsp;/gi, ' '));
            }
          }
        });
      }

      // Final fallback: split by double newlines
      if (paragraphs.length === 0) {
        const text = tempDiv.textContent || '';
        paragraphs = text.split(/\n\s*\n/).map(p => p.trim()).filter(p => p.length > 0);
      }

      console.log('📋 HTML mode - found', paragraphs.length, 'paragraphs');
    }

    if (paragraphs.length === 0) {
      paragraphs = [plainText.trim()];
    }

    return paragraphs;
  }

  return {
    parseGoogleDocsPaste,
    cleanGoogleDocsNode,
    parseGenericPaste
  }
}
