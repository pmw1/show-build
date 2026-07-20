/**
 * PasteHandler — port of the legacy contenteditable editor's paste pipeline
 * into the TipTap/ProseMirror script editor.
 *
 * The legacy editor (EditorPanel.vue) cleaned pasted content (especially from
 * Google Docs) and ran an "Auto Scrub" pass that flagged any paragraph
 * containing a legacy cue token like `(IMG/karmalo)` or `{SOT/foo}` so the user
 * could convert it. The new ProseMirror editor shipped with NO paste handling
 * at all — raw browser paste, no cleaning, no flagging. This extension restores
 * that behaviour.
 *
 * What it does on paste:
 *   1. Read text/html + text/plain from the clipboard.
 *   2. Clean the HTML — Google Docs (docs-internal-guid) gets the structural
 *      gdocs cleaner; everything else gets the generic cleaner. Both are the
 *      pure functions from useEditorPaste.js (reused, not reimplemented), and
 *      both respect the `pastePlainTextOnly` interface setting.
 *   3. Insert the cleaned paragraphs as `paragraph` nodes at the selection.
 *   4. Scan each inserted paragraph for a legacy cue token (LEGACY_CUE_REGEX).
 *      Any match → set that paragraph's `needsAttention: true` +
 *      `flagNote: LEGACY_CUE_FLAG_LABEL` so it red-tints and shows the Convert
 *      button (rendered by NeedsAttention.js). Conversion itself is NOT done
 *      here — the user clicks Convert (flag-and-wait-for-button, per spec).
 *
 * If there's no useful clipboard content we return false and let ProseMirror's
 * default paste run.
 */

import { Extension } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { useEditorPaste } from '@/composables/useEditorPaste.js';
import {
  LEGACY_CUE_REGEX,
  VIDEO_CUE_LOOSE_REGEX,
  VIDEO_TECH_LINE_REGEX,
  LEGACY_CUE_FLAG_LABEL,
} from '@/modules/legacyCueConvert/patterns.js';
import { isPasteInterpretEnabled } from '@/modules/legacyCueConvert/interpretSetting.js';

export const pasteHandlerKey = new PluginKey('pasteHandler');

const { parseGoogleDocsPaste, parseGenericPaste } = useEditorPaste();

/**
 * Turn cleaned-paragraph HTML strings into ProseMirror `paragraph` node JSON.
 * Each string is the inner HTML of a paragraph (may contain <b>/<i>/<u>/<a>).
 * We strip the inline markup to plain text for the text node — the script
 * editor's paragraph model carries prose as plain text + speaker/flag attrs,
 * matching how markdownToDoc builds paragraphs. Bold/italic round-tripping at
 * the mark level is out of scope for this port (the legacy editor stored the
 * same plain-text-with-markup string; we keep parity by flattening to text,
 * which is what the markdown layer persists for prose paragraphs).
 */
function paragraphsToNodes(paragraphHtmlList, schema) {
  const tmp = document.createElement('div');
  const nodes = [];
  for (const html of paragraphHtmlList) {
    tmp.innerHTML = html;
    const text = (tmp.textContent || '').replace(/\u00A0/g, ' ').trim();
    if (!text) continue;
    // Strict token, a loose/broken video token ("( SOT / slug" missing its
    // closing bracket), or a technical "FULL VIDEO IS TITLED '…'" line —
    // the video-block LLM path can convert all three. (If a tech line sits
    // inside a token-anchored block, the sweeper demotes it to a tint-only
    // block member on its next pass.) The loose/tech flavors are part of
    // paste interpretation and honor its setting; strict-token flagging is
    // a validity warning and always runs.
    const needsFlag = LEGACY_CUE_REGEX.test(text) ||
      (isPasteInterpretEnabled() &&
        (VIDEO_CUE_LOOSE_REGEX.test(text) || VIDEO_TECH_LINE_REGEX.test(text)));
    nodes.push(
      schema.nodes.paragraph.create(
        needsFlag ? { needsAttention: true, flagNote: LEGACY_CUE_FLAG_LABEL } : {},
        schema.text(text)
      )
    );
  }
  return nodes;
}

export const PasteHandler = Extension.create({
  name: 'pasteHandler',

  // handlePaste lives on a ProseMirror plugin's `props` — the same mechanism
  // NeedsAttention uses for its DOM handlers. Returning true takes over paste.
  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: pasteHandlerKey,
        props: {
          handlePaste: (view, event) => {
            const cb = event.clipboardData;
            if (!cb) return false;
            const htmlText = cb.getData('text/html') || '';
            const plainText = cb.getData('text/plain') || '';
            if (!htmlText && !plainText) return false;

            // Choose the right cleaner. Google Docs always wraps content in a
            // docs-internal-guid element; route those through the structural
            // gdocs cleaner that preserves paragraph boundaries. Everything
            // else uses the generic cleaner (which also honours the
            // plain-text-only interface setting).
            const isGoogleDocs = htmlText.includes('docs-internal-guid');
            let paragraphs;
            try {
              paragraphs = isGoogleDocs
                ? parseGoogleDocsPaste(htmlText, plainText)
                : parseGenericPaste(htmlText, plainText);
            } catch (e) {
              // If cleaning throws for any reason, fall back to default paste
              // rather than dropping the user's content.
              console.warn('[PasteHandler] clean failed, using default paste:', e);
              return false;
            }

            if (!paragraphs || paragraphs.length === 0) return false;

            const { state, dispatch } = view;
            const nodes = paragraphsToNodes(paragraphs, state.schema);
            if (nodes.length === 0) return false;

            // Replace the current selection with the cleaned paragraphs. Using
            // the selection range (not just the cursor) means a paste over
            // selected text behaves like a normal paste-replace.
            const { from, to } = state.selection;
            const tr = state.tr.replaceWith(from, to, nodes);
            tr.setMeta('addToHistory', true);
            dispatch(tr.scrollIntoView());
            return true;
          },
        },
      }),
    ];
  },
});

export default PasteHandler;
