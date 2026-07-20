/**
 * "Interpret cues & media from pasted script" toggle.
 *
 * Gates the LLM-flavored paste interpretation added 2026-07-18:
 *   - PasteHandler flagging of loose video tokens + technical lines
 *   - the ScriptEditor sweeper's video-block anchors/members
 *     (IN/OUT lines, "FULL VIDEO IS TITLED …", all-caps tech lines)
 *   - the Attempt Fix button (ALL instances, per user direction)
 *
 * NOT gated: Auto-Scrub-style flagging of strict {TYPE/slug} tokens —
 * those keep their red "Invalid cue code" flag as a validity warning
 * whether interpretation is on or off (same rule as the original
 * Legacy Cue Convert plan's Q5).
 *
 * Plain function (not a composable) because the consumers are
 * non-reactive contexts: a ProseMirror decoration builder
 * (NeedsAttention.js), a paste handler, and an interval sweep — each
 * reads the flag at the moment it runs, so a Settings change takes
 * effect on the next paste / sweep pass / decoration rebuild without
 * any event plumbing.
 *
 * Default: ON (current behavior for users with no stored preference).
 * The Settings UI (InterfaceSettings.vue) mirrors this key the same
 * way it mirrors legacyCueConvertEnabled.
 */

export const PASTE_INTERPRET_LS_KEY = 'show-build:pasteCueInterpretEnabled'

export function isPasteInterpretEnabled() {
  try {
    const v = localStorage.getItem(PASTE_INTERPRET_LS_KEY)
    return v === null ? true : v === 'true'
  } catch (_e) {
    return true
  }
}
