/**
 * Master keyboard shortcut registry for show-build.
 *
 * This is the single source of truth used by both:
 *   - The in-app "Keyboard Shortcuts" help modal (triggered by ? or F1)
 *   - docs/KEYBOARD_SHORTCUTS.md (kept in sync manually when shortcuts change)
 *
 * Each shortcut entry has:
 *   keys:    array of key chord labels (e.g. ['Ctrl+S'], or ['J', 'L'] for alternatives)
 *   label:   short human-readable description
 *   notes:   optional extra context (e.g. "double-press within 1s")
 *
 * Sections are displayed in the order defined here.
 */

export const shortcutSections = [
  {
    id: 'help',
    title: 'Help',
    icon: 'mdi-help-circle',
    shortcuts: [
      { keys: ['?', 'F1'], label: 'Show this keyboard shortcuts dialog' },
      { keys: ['Esc'], label: 'Close any open modal / cancel current action' }
    ]
  },

  {
    id: 'global',
    title: 'Global (Content Editor)',
    icon: 'mdi-earth',
    shortcuts: [
      { keys: ['Ctrl+Z', 'Cmd+Z'], label: 'Undo last action (script edit, cue insert/edit/delete, scratch)' },
      { keys: ['Ctrl+Y', 'Ctrl+Shift+Z'], label: 'Redo last undone action' },
      { keys: ['Ctrl+Shift+S'], label: 'Save everything' },
      { keys: ['Ctrl+Shift+R'], label: 'Reload rundown from database' },
      { keys: ['Ctrl+Shift+['], label: 'Toggle left sidebar (Rundown panel)' },
      { keys: ['Ctrl+Shift+]'], label: 'Toggle right sidebar (Metadata panel)' },
      { keys: ['Ctrl+Shift+J'], label: 'Start "Join Items" mode' },
      { keys: ['Ctrl+Shift+I'], label: 'Create new rundown item' }
    ]
  },

  {
    id: 'rundown',
    title: 'Rundown Navigation',
    icon: 'mdi-format-list-numbered',
    shortcuts: [
      { keys: ['↑'], label: 'Select previous rundown item' },
      { keys: ['↓'], label: 'Select next rundown item' },
      { keys: ['Enter'], label: 'Edit selected rundown item' },
      { keys: ['Delete'], label: 'Delete selected rundown item' },
      { keys: ['Ctrl+Click'], label: 'Multi-select / toggle individual item' },
      { keys: ['Shift+Click'], label: 'Range select from anchor to clicked item' },
      { keys: ['Esc'], label: 'Cancel multi-selection' },
      { keys: ['Alt+Shift+R'], label: 'Toggle regions visibility' },
      { keys: ['Ctrl+Alt+Shift+0'], label: 'Clear entire rundown (with confirmation)' }
    ]
  },

  {
    id: 'script-editor',
    title: 'Script / Code Editor',
    icon: 'mdi-script-text',
    shortcuts: [
      { keys: ['Ctrl+S'], label: 'Save all' },
      { keys: ['Ctrl+B'], label: 'Bold selection' },
      { keys: ['Ctrl+I'], label: 'Italic selection' },
      { keys: ['Ctrl+U'], label: 'Underline selection' },
      { keys: ['Ctrl+Alt+H'], label: 'Highlight selection (mark tag)' },
      { keys: ['Alt+/'], label: 'Propose revision (cut / cut+replace selection)' },
      { keys: ['Alt+.'], label: 'Propose addition (insert new text)' },
      { keys: ['Enter'], label: 'Insert line break within paragraph' },
      { keys: ['Enter Enter'], label: 'Split paragraph at cursor (double-press <1s)' },
      { keys: ['Backspace'], label: 'Merge with previous paragraph (when at start of line)' },
      { keys: ['Ctrl+Alt+Shift+X'], label: 'Read selection / segment aloud (TTS)' },
      { keys: ['Ctrl+Shift+C'], label: 'Toggle collapse mode', notes: 'Overrides browser DevTools inspector shortcut' },
      { keys: ['Alt+Shift+A'], label: 'Regenerate current cue AssetID' },
      { keys: ['Shift+Delete'], label: 'Delete cue at cursor' },
      { keys: ['Ctrl+Click'], label: 'Multi-select paragraphs (toggle)' },
      { keys: ['Shift+Click'], label: 'Range-select paragraphs' }
    ]
  },

  {
    id: 'cue-insert',
    title: 'Cue Insertion (Alt+key)',
    icon: 'mdi-plus-box-multiple',
    shortcuts: [
      { keys: ['Alt+C'], label: 'Toggle cue selector menu' },
      { keys: ['Alt+S'], label: 'Insert SOT (Sound on Tape)' },
      { keys: ['Alt+V'], label: 'Insert VO (Voice Over)' },
      { keys: ['Alt+N'], label: 'Insert NAT (Natural Sound)' },
      { keys: ['Alt+P'], label: 'Insert PKG (Package)' },
      { keys: ['Alt+G'], label: 'Insert GFX (Graphics)' },
      { keys: ['Alt+I'], label: 'Insert IMG (Image)' },
      { keys: ['Alt+D'], label: 'Insert DIR (Director note)' },
      { keys: ['Alt+B'], label: 'Insert BUMP' },
      { keys: ['Alt+R'], label: 'Insert STING (ring)' }
    ]
  },

  {
    id: 'cue-placement',
    title: 'Cue Placement Overlay',
    icon: 'mdi-target',
    shortcuts: [
      { keys: ['↑'], label: 'Navigate to previous placement zone' },
      { keys: ['↓'], label: 'Navigate to next placement zone' },
      { keys: ['Enter'], label: 'Confirm placement at current zone' },
      { keys: ['Esc'], label: 'Cancel placement' }
    ]
  },

  {
    id: 'sot-vo-modal',
    title: 'SOT / VO Video Editor',
    icon: 'mdi-movie-edit',
    shortcuts: [
      { keys: ['Space', 'K'], label: 'Play / pause' },
      { keys: ['Shift+Space'], label: 'Preview IN → OUT' },
      { keys: ['J'], label: 'Step back 1 second' },
      { keys: ['L'], label: 'Step forward 1 second' },
      { keys: ['←'], label: 'Step back 1 frame' },
      { keys: ['→'], label: 'Step forward 1 frame' },
      { keys: ['Shift+←'], label: 'Step back 10 frames' },
      { keys: ['Shift+→'], label: 'Step forward 10 frames' },
      { keys: ['Ctrl+←', '↓'], label: 'Jump back 10 seconds' },
      { keys: ['Ctrl+→', '↑'], label: 'Jump forward 10 seconds' },
      { keys: ['I'], label: 'Mark IN point (trim start)' },
      { keys: ['O'], label: 'Mark OUT point (trim end)' },
      { keys: ['Q'], label: 'Jump to IN point' },
      { keys: ['W'], label: 'Jump to OUT point' },
      { keys: ['T', 'Alt+.'], label: 'Set thumbnail marker at current time' },
      { keys: ['['], label: 'Decrease playback speed' },
      { keys: [']'], label: 'Increase playback speed' },
      { keys: ['\\'], label: 'Reset playback speed to 1.0×' },
      { keys: ['Ctrl+Enter'], label: 'Take / commit current cut' },
      { keys: ['Alt+Enter'], label: 'Submit for processing / inject cue' },
      { keys: ['Enter Enter'], label: 'Take (in Multiple Clips mode, double-press <500ms)' },
      { keys: ['N'], label: 'Clip mode: None' },
      { keys: ['S'], label: 'Clip mode: Single trim' },
      { keys: ['M'], label: 'Clip mode: Multiple clips' },
      { keys: ['B'], label: 'Browse for local video file' },
      { keys: ['Ctrl+1'], label: 'Toggle hotkey reference menu' }
    ]
  },

  {
    id: 'img-cue-modal',
    title: 'Image Cue Modal',
    icon: 'mdi-image',
    shortcuts: [
      { keys: ['Ctrl+V', 'Cmd+V'], label: 'Paste image from clipboard' },
      { keys: ['Ctrl+O', 'Cmd+O'], label: 'Open local file browser' },
      { keys: ['Esc'], label: 'Cancel and close' }
    ]
  },

  {
    id: 'text-modals',
    title: 'Text Modals (BUMP / RIF / STING / DIR / NAT / PKG)',
    icon: 'mdi-form-textbox',
    shortcuts: [
      { keys: ['Shift+Enter'], label: 'Submit form' },
      { keys: ['Esc'], label: 'Close modal' },
      { keys: ['↑ / ↓'], label: 'Increment / decrement time value (RIF modal only)' }
    ]
  },

  {
    id: 'whiteboard',
    title: 'Whiteboard / Scratchpad',
    icon: 'mdi-draw',
    shortcuts: [
      { keys: ['Ctrl+Shift+S'], label: 'Save whiteboard' },
      { keys: ['T'], label: 'Add text card' },
      { keys: ['L'], label: 'Add link card' },
      { keys: ['I'], label: 'Upload image' },
      { keys: ['V'], label: 'Upload video' },
      { keys: ['A'], label: 'Upload audio' },
      { keys: ['H'], label: 'Add HTML card' },
      { keys: ['C'], label: 'Add code card' },
      { keys: ['M'], label: 'Add markdown card' },
      { keys: ['F'], label: 'Fit all nodes to screen' },
      { keys: ['K'], label: 'Add contact card' },
      { keys: ['Q'], label: 'Add question card' },
      { keys: ['P'], label: 'Toggle parent menu' },
      { keys: ['Delete'], label: 'Delete active card (with confirmation)' },
      { keys: ['Right-click'], label: 'Node menu: edit / delete / delete full branch' },
      { keys: ['Esc'], label: 'Close menus / cancel subtree drag' },
      { keys: ['Scroll'], label: 'Zoom (toward the cursor)' },
      { keys: ['Ctrl', '+ drag'], label: 'Move node with all its linked children' },
      { keys: ['Ctrl+Shift', '+ drag'], label: 'Move children and pack them tightly on release' }
    ]
  },

  {
    id: 'dev',
    title: 'Developer / Testing',
    icon: 'mdi-code-braces',
    shortcuts: [
      { keys: ['Ctrl+Alt+Shift+1', '…', 'Ctrl+Alt+Shift+9'], label: 'Insert test segment with N paragraphs' }
    ]
  }
]

/**
 * Known potential conflicts — displayed in the help modal as a warning tab.
 * Most are context-isolated (different view or modal), but listed here so
 * developers adding new shortcuts know where the collision space is.
 */
export const knownConflicts = [
  {
    keys: 'Space / I / O / J / K / L / T',
    contexts: ['SOT/VO modal', 'Whiteboard canvas'],
    note: 'Same single-letter keys mean different things in different views. Isolated — no runtime conflict because only one context is active at a time.'
  },
  {
    keys: 'Ctrl+Shift+C',
    contexts: ['EditorPanel (collapse mode)', 'Browser DevTools (inspect element)'],
    note: 'EditorPanel intentionally intercepts this to toggle collapse mode. Open DevTools via F12 or its menu instead.'
  },
  {
    keys: 'Ctrl+S',
    contexts: ['EditorPanel (save)', 'Browser (save page)'],
    note: 'Intercepted and preventDefault() to save the script instead of the HTML page.'
  },
  {
    keys: 'Ctrl+O',
    contexts: ['ImgCueModal (open file picker)', 'Browser (open file)'],
    note: 'Only intercepted while the Image Cue modal is open.'
  },
  {
    keys: 'Ctrl+1',
    contexts: ['SOT modal (toggle hotkey menu)', 'Browser (switch to tab 1)'],
    note: 'SOT modal takes priority only when focused; otherwise the browser handles it.'
  },
  {
    keys: 'Ctrl+Shift+R',
    contexts: ['ContentEditor global (reload rundown)', 'RundownPanel (refresh rundown)', 'Browser (hard reload)'],
    note: 'App handler fires when the Content Editor is active; browser default is overridden.'
  },
  {
    keys: 'Delete',
    contexts: ['Rundown navigation (delete selected item)', 'Script editor (normal delete char)'],
    note: 'Global handler checks focus — only triggers rundown delete when no input/contenteditable is active.'
  }
]
