/**
 * Minimal client-side feature flags, backed by localStorage so they can be
 * toggled per-browser without a backend or rebuild. Used to gate the
 * ProseMirror/TipTap script editor migration (useProseMirrorEditor) so the new
 * editor ships dark and is opt-in until parity is proven (migration Phase 5).
 *
 * Toggle from the browser console:
 *   localStorage.setItem('ff:useProseMirrorEditor', 'true')   // enable
 *   localStorage.removeItem('ff:useProseMirrorEditor')        // disable
 * then reload.
 */

import { ref } from 'vue';

const PREFIX = 'ff:';

const KNOWN_FLAGS = {
  // Mount the new TipTap/ProseMirror ScriptEditor instead of the legacy
  // contenteditable EditorPanel script surface.
  // DEFAULT ON for the dev/migration branch — the dev site uses the new editor
  // by default. (This file only exists on the migration branch; live/main runs
  // the legacy editor.) To opt OUT in a given browser:
  //   localStorage.setItem('ff:useProseMirrorEditor', 'false')
  useProseMirrorEditor: true,
};

function read(name) {
  try {
    const raw = localStorage.getItem(PREFIX + name);
    if (raw === null) return KNOWN_FLAGS[name] ?? false;
    return raw === 'true';
  } catch {
    return KNOWN_FLAGS[name] ?? false;
  }
}

export function useFeatureFlags() {
  const isEnabled = (name) => read(name);

  const setFlag = (name, value) => {
    try {
      if (value) localStorage.setItem(PREFIX + name, 'true');
      else localStorage.removeItem(PREFIX + name);
    } catch {
      /* ignore storage failures */
    }
  };

  // The ProseMirror/TipTap ScriptEditor is now the ONLY script editor — the
  // legacy contenteditable surface is retired. This is no longer flag-gated:
  // it is always on, regardless of any stale `ff:useProseMirrorEditor` value a
  // browser may still have in localStorage from the migration period.
  const useProseMirrorEditor = ref(true);

  return { isEnabled, setFlag, useProseMirrorEditor };
}

export default useFeatureFlags;
