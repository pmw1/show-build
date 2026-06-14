/**
 * SlashCommand — type "/" at the caret to open an inline, filterable cue menu.
 *
 * Built on @tiptap/suggestion. Because ProseMirror tracks a real caret, the cue
 * inserts EXACTLY where you are — no cursor-snapshot hack (which the legacy
 * contenteditable bar needed). Keep typing to filter (/fsq, /sot); ↑/↓ + Enter
 * to pick; Esc to dismiss.
 *
 * On select, the matched "/query" text is removed and a cue node is inserted via
 * the CueNode `insertCue` command with a minimal field bag — the same node the
 * markdown layer round-trips, so it serializes to a normal <!-- Begin Cue -->
 * block. The cue card then opens to fill in details (handled by the NodeView).
 */

import { Extension } from '@tiptap/core';
import Suggestion from '@tiptap/suggestion';
import { VueRenderer } from '@tiptap/vue-3';
import CueSlashMenu from './CueSlashMenu.vue';

// Cue catalogue (mirrors EditorPanel cueDefinitions). color drives the chip.
export const CUE_ITEMS = [
  { type: 'IMG', key: 'i', tooltip: 'Image / Photo', color: '#90caf9' },
  { type: 'GFX', key: 'g', tooltip: 'Graphics & Lower Thirds', color: '#a5d6a7' },
  { type: 'FSQ', key: 'q', tooltip: 'Full Screen Quote', color: '#ffcc80' },
  { type: 'SOT', key: 's', tooltip: 'Sound on Tape', color: '#ef9a9a' },
  { type: 'VO', key: 'v', tooltip: 'Voice Over', color: '#ce93d8' },
  { type: 'NAT', key: 'n', tooltip: 'Natural Sound', color: '#80cbc4' },
  { type: 'PKG', key: 'p', tooltip: 'Package', color: '#bcaaa4' },
  { type: 'NOTE', key: 'd', tooltip: 'Note / Direction', color: '#e6ee9c' },
  { type: 'BUMP', key: 'b', tooltip: 'Bumper', color: '#9fa8da' },
  { type: 'STING', key: 't', tooltip: 'Stinger', color: '#f48fb1' },
  { type: 'RIF', key: 'r', tooltip: 'Riff', color: '#b0bec5' },
];

function filterItems(query) {
  const q = (query || '').toLowerCase();
  if (!q) return CUE_ITEMS;
  return CUE_ITEMS.filter(
    (it) => it.type.toLowerCase().startsWith(q) || it.tooltip.toLowerCase().includes(q)
  );
}

// Minimal field bag for a freshly inserted cue of a given type. The NodeView /
// Position a popup element near a client rect, flipping above if it would
// overflow the viewport bottom. No external positioning lib needed.
function placePopup(el, rect) {
  if (!rect) return;
  const margin = 6;
  el.style.position = 'absolute';
  el.style.left = `${window.scrollX + rect.left}px`;
  const belowTop = window.scrollY + rect.bottom + margin;
  const wouldOverflow = rect.bottom + el.offsetHeight + margin > window.innerHeight;
  if (wouldOverflow && rect.top - el.offsetHeight - margin > 0) {
    el.style.top = `${window.scrollY + rect.top - el.offsetHeight - margin}px`;
  } else {
    el.style.top = `${belowTop}px`;
  }
}

export const SlashCommand = Extension.create({
  name: 'cueSlashCommand',

  addOptions() {
    return {
      // Called when the user picks a cue type from the slash menu. The editor
      // does NOT insert a cue node itself — instead this hands the cue type up to
      // EditorPanel, which launches the SAME modal the ADD CUE buttons launch
      // (via insertCueFromMenu). The modal then inserts the finished cue. So "/"
      // is just a keyboard shortcut for the ADD CUE buttons.
      onSelectCue: null,
      suggestion: {
        char: '/',
        startOfLine: false,
      },
    };
  },

  addProseMirrorPlugins() {
    // Capture in a closure — `this` is the extension here, but NOT inside the
    // suggestion `command` (which @tiptap/suggestion re-binds), so referencing
    // `this.options` there throws. Bind it now instead.
    const onSelectCue = this.options.onSelectCue;
    return [
      Suggestion({
        editor: this.editor,
        ...this.options.suggestion,
        command: ({ editor, range, props }) => {
          // Remove the "/query" text the user typed, then hand the chosen cue
          // type up to the host (EditorPanel) to launch its modal.
          editor.chain().focus().deleteRange(range).run();
          if (typeof onSelectCue === 'function') onSelectCue(props.type);
        },
        items: ({ query }) => filterItems(query),
        render: () => {
          let component;
          let popup;

          const mount = (props) => {
            component = new VueRenderer(CueSlashMenu, {
              props: { items: props.items, command: props.command },
              editor: props.editor,
            });
            popup = document.createElement('div');
            popup.className = 'cue-slash-popup';
            popup.style.zIndex = '3000';
            popup.appendChild(component.element);
            document.body.appendChild(popup);
            placePopup(popup, props.clientRect && props.clientRect());
          };

          return {
            onStart: mount,
            onUpdate(props) {
              component?.updateProps({ items: props.items, command: props.command });
              placePopup(popup, props.clientRect && props.clientRect());
            },
            onKeyDown(props) {
              if (props.event.key === 'Escape') {
                this.onExit?.();
                return true;
              }
              return component?.ref?.onKeyDown?.(props.event) ?? false;
            },
            onExit() {
              popup?.remove();
              component?.destroy();
              component = null;
              popup = null;
            },
          };
        },
      }),
    ];
  },
});

export default SlashCommand;
