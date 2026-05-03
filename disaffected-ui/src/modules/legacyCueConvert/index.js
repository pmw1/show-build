/**
 * Legacy Cue Convert — public API barrel.
 *
 * Consumers should import everything from this file, never directly
 * from the internal sub-files. That keeps the module's public surface
 * narrow and makes future internal restructuring (e.g. adopting the
 * shared cueTypeSchema — see README.md) a non-breaking change.
 */

export {
  LEGACY_CUE_REGEX,
  LEGACY_CUE_REGEX_GLOBAL,
  LEGACY_CUE_FLAG_LABEL,
  ALIAS_MAP,
  DEFAULT_DURATION_BY_TYPE,
  MEDIA_BEARING_TYPES,
  normalizeTokenType,
  sanitizeSlug,
} from './patterns'

export { convertLegacyToken } from './conversion'

export {
  useLegacyCueConvertEnabled,
  LEGACY_CUE_CONVERT_LS_KEY,
} from './useLegacyCueConvertEnabled'

export { default as ConvertButton } from './ConvertButton.vue'
