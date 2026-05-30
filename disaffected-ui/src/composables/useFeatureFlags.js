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
  // contenteditable EditorPanel script surface. Default OFF.
  useProseMirrorEditor: false,
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

  // Reactive snapshot of the ProseMirror editor flag, read once at setup.
  const useProseMirrorEditor = ref(read('useProseMirrorEditor'));

  return { isEnabled, setFlag, useProseMirrorEditor };
}

export default useFeatureFlags;
