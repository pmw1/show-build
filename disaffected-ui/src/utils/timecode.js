/**
 * Timecode formatting helpers (todo #38).
 *
 * The ffprobe / analysis pipeline reports a clip's duration as a raw seconds
 * decimal (e.g. 12.34). The editor's cue cards must show it as broadcast
 * timecode `hh:mm:ss:ff`. This is the single shared formatter so every display
 * point (SOT card body, footer, header, chip) renders the same way.
 *
 * Ported from useTrimmableMediaModal.js `secondsToTimecode`, generalized to a
 * standalone util that ALSO accepts a value that is already a timecode string
 * (some persistence paths store "00:00:05:00") and passes it through untouched
 * so we never double-format.
 */

const DEFAULT_FRAMERATE = 30; // trim modal default; analysis data rarely carries fps

const pad = (n) => n.toString().padStart(2, '0');

/** True if `v` already looks like an hh:mm:ss or hh:mm:ss:ff timecode string. */
export function isTimecodeString(v) {
  return typeof v === 'string' && /^\d{1,2}:\d{2}:\d{2}(:\d{2})?$/.test(v.trim());
}

/**
 * Format a duration as `hh:mm:ss:ff`.
 * @param {number|string} value seconds decimal, OR an already-formatted timecode string.
 * @param {object} [opts]
 * @param {number} [opts.framerate=30] frames per second used for the :ff field.
 * @param {boolean} [opts.showFrames=true] include the trailing :ff field.
 * @returns {string|null} timecode string, or null for an unusable value.
 */
export function formatTimecode(value, { framerate = DEFAULT_FRAMERATE, showFrames = true } = {}) {
  // Already a timecode string: normalize to hh:mm:ss[:ff] but don't re-derive it.
  if (isTimecodeString(value)) {
    const parts = value.trim().split(':');
    if (!showFrames && parts.length === 4) return parts.slice(0, 3).join(':');
    if (showFrames && parts.length === 3) return `${value.trim()}:00`;
    return value.trim();
  }

  const seconds = typeof value === 'string' ? parseFloat(value) : value;
  if (!Number.isFinite(seconds) || seconds < 0) return null;

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const frames = Math.floor((seconds % 1) * framerate);

  return showFrames
    ? `${pad(hours)}:${pad(minutes)}:${pad(secs)}:${pad(frames)}`
    : `${pad(hours)}:${pad(minutes)}:${pad(secs)}`;
}

export default formatTimecode;
