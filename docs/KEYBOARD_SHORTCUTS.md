# Keyboard Shortcuts — Master Reference

This is the authoritative list of every keyboard shortcut in show-build. The
same data is used by the in-app help dialog (press <kbd>?</kbd> or <kbd>F1</kbd>
from anywhere in the app). When you add or change a shortcut, update **both**
this file and `disaffected-ui/src/data/keyboardShortcuts.js` so they stay in sync.

**Convention:** `Ctrl+X` means Control (or ⌘ Command on macOS) + X. Modifier
combinations read left-to-right in the order Ctrl → Alt → Shift → key.

---

## Help

| Shortcut | Action |
|---|---|
| `?` / `F1` | Open the keyboard shortcuts dialog |
| `Esc` | Close any open modal / cancel current action |

Source: `App.vue` (global listener), `KeyboardShortcutsModal.vue`

---

## Global — Content Editor

Active when the Content Editor view is focused and no modal is open.

| Shortcut | Action |
|---|---|
| `Ctrl+Z` / `Cmd+Z` | Undo last change (script + scratch; scoped to current rundown item) |
| `Ctrl+Y` / `Ctrl+Shift+Z` | Redo (up to 50 states) |
| `Ctrl+Shift+S` | Save everything |
| `Ctrl+Shift+R` | Reload rundown from database |
| `Ctrl+Shift+[` | Toggle left sidebar (Rundown panel) |
| `Ctrl+Shift+]` | Toggle right sidebar (Metadata panel) |
| `Ctrl+Shift+J` | Start "Join Items" mode |
| `Ctrl+Shift+I` | Create new rundown item |

Source: `components/ContentEditor.vue` (~line 4326+)

---

## Rundown Navigation

Active when focus is outside any input field and the rundown panel has items.

| Shortcut | Action |
|---|---|
| `↑` | Select previous rundown item |
| `↓` | Select next rundown item |
| `Enter` | Edit selected rundown item |
| `Delete` | Delete selected rundown item |
| `Ctrl+Click` | Multi-select / toggle individual item |
| `Shift+Click` | Range select from anchor to clicked item |
| `Esc` | Cancel multi-selection |
| `Alt+Shift+R` | Toggle regions visibility |
| `Ctrl+Alt+Shift+0` | Clear entire rundown (with confirmation) |

Source: `components/content-editor/RundownPanel.vue` (~line 2359+), `components/ContentEditor.vue` (~line 4409+)

---

## Script / Code Editor

Active when editing script paragraphs (contenteditable) or the raw markdown textarea.

| Shortcut | Action |
|---|---|
| `Ctrl+S` | Save all |
| `Ctrl+B` | Bold selection |
| `Ctrl+I` | Italic selection |
| `Ctrl+U` | Underline selection |
| `Ctrl+Alt+H` | Highlight selection (`<mark>` tag) |
| `Alt+/` | Propose revision (cut or cut+replace) |
| `Alt+.` | Propose addition (insert new text) |
| `Enter` | Insert line break within paragraph |
| `Enter Enter` (<1s) | Split paragraph at cursor |
| `Backspace` (at start of line) | Merge with previous paragraph |
| `Ctrl+Alt+Shift+X` | Read selection / segment aloud (TTS) |
| `Ctrl+Shift+C` | Toggle collapse mode ⚠️ overrides DevTools inspector |
| `Alt+Shift+A` | Regenerate current cue AssetID |
| `Shift+Delete` | Delete cue at cursor |
| `Ctrl+Click` | Multi-select paragraphs (toggle) |
| `Shift+Click` | Range-select paragraphs |

Source: `components/content-editor/EditorPanel.vue` (~lines 2757+, 4597+, 6480+)

---

## Cue Insertion (Alt + key)

Hold `Alt` and press a letter to insert a cue of that type, or press `Alt+C`
to open the cue selector menu first.

| Shortcut | Cue type |
|---|---|
| `Alt+C` | Toggle cue selector menu |
| `Alt+S` | SOT (Sound on Tape) |
| `Alt+V` | VO (Voice Over) |
| `Alt+N` | NAT (Natural sound) |
| `Alt+P` | PKG (Package) |
| `Alt+G` | GFX (Graphics) |
| `Alt+I` | IMG (Image) |
| `Alt+D` | DIR (Director note) |
| `Alt+B` | BUMP |
| `Alt+R` | STING (ring) |

Source: `components/ContentEditor.vue` (~line 4477+), `components/content-editor/EditorPanel.vue` (~line 6576)

---

## Cue Placement Overlay

Active when the cue placement zone-picker is visible.

| Shortcut | Action |
|---|---|
| `↑` | Navigate to previous placement zone |
| `↓` | Navigate to next placement zone |
| `Enter` | Confirm placement at current zone |
| `Esc` | Cancel placement |

Source: `components/content-editor/CuePlacementOverlay.vue` (~line 378+)

---

## SOT / VO Video Editor

Active when the SOT or VO modal is open with a loaded video.

### Playback

| Shortcut | Action |
|---|---|
| `Space` / `K` | Play / pause |
| `Shift+Space` | Preview IN → OUT |
| `J` | Step back 1 second |
| `L` | Step forward 1 second |
| `←` | Step back 1 frame |
| `→` | Step forward 1 frame |
| `Shift+←` | Step back 10 frames |
| `Shift+→` | Step forward 10 frames |
| `Ctrl+←` / `↓` | Jump back 10 seconds |
| `Ctrl+→` / `↑` | Jump forward 10 seconds |

### Trim / Clip

| Shortcut | Action |
|---|---|
| `I` | Mark IN point (trim start) |
| `O` | Mark OUT point (trim end) |
| `Q` | Jump to IN point |
| `W` | Jump to OUT point |
| `T` / `Alt+.` | Set thumbnail marker at current time |
| `[` | Decrease playback speed |
| `]` | Increase playback speed |
| `\` | Reset playback speed to 1.0× |
| `Ctrl+Enter` | Take / commit current cut |
| `Alt+Enter` | Submit for processing / inject cue |
| `Enter Enter` (<500ms) | Take (in Multiple Clips mode) |

### Clip Mode

| Shortcut | Action |
|---|---|
| `N` | Clip mode: None |
| `S` | Clip mode: Single trim |
| `M` | Clip mode: Multiple clips |
| `B` | Browse for local video file |
| `Ctrl+1` | Toggle hotkey reference menu |

Source: `components/modals/SotModal.vue` (~line 1770+), `components/modals/VoModal.vue` (~line 815+)

---

## Image Cue Modal

| Shortcut | Action |
|---|---|
| `Ctrl+V` / `Cmd+V` | Paste image from clipboard (supports Google image paste) |
| `Ctrl+O` / `Cmd+O` | Open local file browser |
| `Esc` | Cancel and close |

Source: `components/content-editor/modals/ImgCueModal.vue` (~line 293+)

---

## Text Modals — BUMP / RIF / STING / DIR / NAT / PKG

All these modals share a common keyboard pattern.

| Shortcut | Action |
|---|---|
| `Shift+Enter` | Submit form |
| `Esc` | Close modal |
| `↑` / `↓` | Increment / decrement time value (RIF modal only) |

Source: `components/modals/BumpModal.vue`, `RifModal.vue`, `StingModal.vue`, `DirModal.vue`, `NatModal.vue`, `PkgModal.vue`

---

## Whiteboard / Scratchpad

Active when the whiteboard canvas is focused.

| Shortcut | Action |
|---|---|
| `Ctrl+Shift+S` | Save whiteboard |
| `T` | Add text card |
| `L` | Add link card |
| `I` | Upload image |
| `V` | Upload video |
| `A` | Upload audio |
| `H` | Add HTML card |
| `C` | Add code card |
| `M` | Add markdown card |
| `P` | Toggle parent menu |
| `Delete` | Delete active card |
| `Esc` | Exit connection mode / close menus |

Source: `views/ScratchpadView.vue` (~line 2349+)

---

## Developer / Testing

| Shortcut | Action |
|---|---|
| `Ctrl+Alt+Shift+1` … `Ctrl+Alt+Shift+9` | Insert test segment with N paragraphs |

Source: `components/ContentEditor.vue` (~line 4523+)

---

## Known Conflicts & Browser Overrides

Most conflicts are context-isolated (different view, different modal), so they
don't fire at the same time. Listed here so developers adding new shortcuts
know where the collision space is.

| Keys | Contexts | Note |
|---|---|---|
| `Space` / `I` / `O` / `J` / `K` / `L` / `T` | SOT/VO modal vs Whiteboard canvas | Same letters, different meanings. Only one context is active at a time. |
| `Ctrl+Shift+C` | EditorPanel (collapse mode) vs Browser DevTools | App intercepts it. Use F12 or menu for DevTools. |
| `Ctrl+S` | EditorPanel (save) vs Browser "save page" | App `preventDefault()` and saves the script. |
| `Ctrl+O` | ImgCueModal (file picker) vs Browser "open file" | Only intercepted while the Image Cue modal is open. |
| `Ctrl+1` | SOT modal (toggle hotkey menu) vs Browser "switch to tab 1" | SOT takes priority only when the modal is focused. |
| `Ctrl+Shift+R` | ContentEditor (reload rundown) vs Browser "hard reload" | App handler fires when the Content Editor is active. |
| `Delete` | Rundown navigation (delete item) vs text field (delete char) | Global handler checks focus — only fires when no input is active. |
| `Alt+I` / `Alt+S` / `Alt+G` / etc. | ContentEditor cue-insert vs EditorPanel cue-insert | Both listen; only one fires depending on focus. Historically no double-fire observed. |

---

## Implementation Notes

### Single source of truth

- Runtime data: `disaffected-ui/src/data/keyboardShortcuts.js`
- Displayed by: `disaffected-ui/src/components/KeyboardShortcutsModal.vue`
- Opened from: `disaffected-ui/src/App.vue` via `?` or `F1` global listener
- This markdown file is the human-readable mirror — keep it synchronized manually

### Where to add a new shortcut

1. **Implement it** in the relevant component (`@keydown` or `addEventListener('keydown', …)`).
2. **Register it** as an entry in the matching section of `keyboardShortcuts.js`.
3. **Document it** here under the matching section.
4. **Check for conflicts** — if it shares a chord with an existing shortcut, add an entry to the "Known Conflicts" table in both places.

### Text-field exclusion pattern

Almost every global hotkey skips execution when focus is inside an
`<input>`, `<textarea>`, or `[contenteditable=true]` element, so typing
normally never triggers an unintended action. The shortcuts modal listener
in `App.vue` uses this same pattern — typing `?` in a comment field
does not open the help dialog.
