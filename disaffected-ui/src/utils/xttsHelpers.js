/**
 * DEPRECATED: This file is a backward-compatibility shim.
 * Import from '@/utils/ttsHelpers' instead.
 */
export {
  isTtsReady as isXttsReady,
  isTtsReady,
  getTtsStatus as getXttsStatus,
  getTtsStatus,
  generateSpeech,
  playText,
  getAvailableSpeakers,
  getTtsStatusText as getXttsStatusText,
  getTtsStatusText,
  addTtsButton,
  ttsDirective
} from './ttsHelpers'
