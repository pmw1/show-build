/**
 * SpeakerHeaders — a speaker-label header above each run of same-speaker
 * paragraphs in the script editor.
 *
 * Ports the legacy contenteditable editor's `.speaker-header` (EditorPanel
 * shouldShowSpeakerHeader / getSpeakerHeaderStyle): a small uppercase speaker
 * name with a colored bottom border, shown above a paragraph ONLY when the
 * speaker changes — i.e. at the first block, after a cue, or when this
 * paragraph's speaker differs from the previous paragraph's. Consecutive
 * same-speaker paragraphs share one header (a header per speaker-run).
 *
 * Implementation mirrors LineNumbers.js: a thin TipTap Extension whose only job
 * is one ProseMirror Plugin returning widget decorations. The header is a
 * non-editable widget injected at the start of each "speaker changes here"
 * paragraph. Because it's a decoration (not a real node), it never enters the
 * document or the markdown — the speaker still lives purely on the paragraph's
 * `speaker` attr, exactly as before. Decorations recompute on every doc change,
 * so changing a speaker (e.g. via the multi-select "Change speaker") immediately
 * re-flows which paragraphs show a header.
 *
 * Speaker display names + colors come from CueParser.getSpeakerOptions() so the
 * header matches the rest of the app (and the legacy editor) exactly.
 */

import { Extension } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';
import CueParser from '@/utils/cueParser.js';

export const speakerHeadersKey = new PluginKey('speakerHeaders');

// Speaker -> { label, color }. Built once from CueParser's canonical list.
const SPEAKER_MAP = (() => {
  const map = {};
  CueParser.getSpeakerOptions().forEach((o) => {
    map[o.value] = { label: o.label, color: o.color };
  });
  return map;
})();

function speakerInfo(speaker) {
  const key = speaker || 'josh';
  if (SPEAKER_MAP[key]) return SPEAKER_MAP[key];
  // Unknown speaker: title-case the value, neutral color (matches legacy fallback).
  const label = key.charAt(0).toUpperCase() + key.slice(1);
  return { label, color: '#666666' };
}

/** Darken a #rrggbb hex by `amount` (0..1) -> "rgb(r, g, b)". Matches legacy darkenColor. */
function darken(hex, amount) {
  if (!/^#[0-9a-fA-F]{6}$/.test(hex)) return hex;
  const r = Math.max(0, parseInt(hex.slice(1, 3), 16) * (1 - amount));
  const g = Math.max(0, parseInt(hex.slice(3, 5), 16) * (1 - amount));
  const b = Math.max(0, parseInt(hex.slice(5, 7), 16) * (1 - amount));
  return `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`;
}

/** Build the speaker-header DOM widget for one paragraph. */
function buildHeaderDOM(speaker) {
  const info = speakerInfo(speaker);
  const wrap = document.createElement('div');
  wrap.className = 'pm-speaker-header';
  wrap.setAttribute('contenteditable', 'false');
  // Colored bottom border = the speaker color darkened (legacy getSpeakerHeaderStyle).
  wrap.style.borderBottomColor = darken(info.color, 0.3);

  const name = document.createElement('span');
  name.className = 'pm-speaker-name';
  name.textContent = info.label;
  name.style.color = info.color;
  wrap.appendChild(name);
  return wrap;
}

/**
 * Walk the top-level blocks; emit a header widget at the start of every
 * paragraph that begins a new speaker run (first block, after a cue, or speaker
 * differs from the previous paragraph).
 */
function buildDecorations(doc) {
  const decos = [];
  let prevType = null;
  let prevSpeaker = null;

  doc.forEach((node, offset) => {
    if (node.type.name === 'paragraph') {
      const speaker = node.attrs.speaker || 'josh';
      const showHeader = prevType === null || prevType === 'cue' || speaker !== prevSpeaker;
      if (showHeader) {
        // side:-1 puts the widget BEFORE the paragraph content; key ties it to
        // the speaker so PM reuses/replaces the right widget on redraw.
        decos.push(
          Decoration.widget(offset + 1, () => buildHeaderDOM(speaker), {
            side: -1,
            key: `pm-speaker-${offset}-${speaker}`,
          })
        );
      }
      prevSpeaker = speaker;
    }
    prevType = node.type.name;
  });

  return DecorationSet.create(doc, decos);
}

export const SpeakerHeaders = Extension.create({
  name: 'speakerHeaders',

  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: speakerHeadersKey,
        state: {
          init(_, { doc }) {
            return buildDecorations(doc);
          },
          apply(tr, old) {
            // Only rebuild when the doc actually changed (speaker attr edits are
            // doc changes), otherwise keep the mapped set.
            if (!tr.docChanged) return old.map(tr.mapping, tr.doc);
            return buildDecorations(tr.doc);
          },
        },
        props: {
          decorations(state) {
            return this.getState(state);
          },
        },
      }),
    ];
  },
});

export default SpeakerHeaders;
