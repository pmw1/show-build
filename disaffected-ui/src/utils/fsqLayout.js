/**
 * FSQ Layout Constants & Helpers
 *
 * Single source of truth for FSQ (Full Screen Quote) visual layout rules.
 * Mirrors the rendering logic in tools/render_fsq_png.py (lines 66-119, 283-336).
 * The PNG renderer is the authority — these values are extracted from it
 * so that frontend previews match the generated output.
 */

// Reference canvas (renderer uses 1920x1080)
export const FSQ_CANVAS = { width: 1920, height: 1080 }

// Default style parameters — matches render_fsq_png.py __init__ defaults
export const FSQ_DEFAULTS = {
  fontFamily: 'sans-serif',
  alignment: 'center',
  boxHeight: 80,           // % of canvas height (matches render_fsq_png.py)
  boxOpacity: 75,          // % opacity
  lineSpacing: 30,         // % of font size added as extra spacing (matches render_fsq_png.py)
  attributionRatio: 0.6,   // attribution font = 60% of quote font
  fontSize: 34,            // UI default (max_font_size hint for auto-fit)
  attributionSize: 16,     // UI default for attribution font size
}

// Preview scaling factor: the FSQ fontSize value (e.g. 34) is a UI-level
// number. In-editor previews multiply by this factor to get CSS px.
// The PNG renderer receives fontSize * FSQ_PNG_SCALE as max_font_size.
// PNG renderer scale: rendered px = fontSize * FSQ_PNG_SCALE.
// Quote and attribution use the SAME multiplier so the quote-to-attribution
// ratio in the PNG matches the modal preview exactly. To make attribution
// larger, drag the per-cue Attrib Size slider.
export const FSQ_PNG_SCALE = 4
export const FSQ_PNG_ATTRIBUTION_SCALE = FSQ_PNG_SCALE

// PNG canvas reference height. Used to convert pixel-space text sizes into
// canvas-fraction percentages for WYSIWYG preview rendering.
export const FSQ_PNG_REF_HEIGHT = 1080

// Legacy preview-to-pixel multiplier — retained for backward compatibility
// with any consumer that hasn't migrated to container-query-based preview
// sizing yet. Prefer fsqPreviewCanvasHeightUnit() below for new code.
export const FSQ_PREVIEW_SCALE = 0.5

/**
 * Convert a UI font-size value into a CSS length string sized as a fraction
 * of its preview container's HEIGHT. The fraction equals exactly what the
 * same UI value occupies on the PNG canvas (1080px tall), so previews
 * become WYSIWYG: the text-to-canvas ratio is identical between preview
 * and PNG no matter how big the preview container is rendered.
 *
 * Returns a string like "12.59cqh" — `cqh` is "container-query height"
 * (1cqh = 1% of the nearest size-containment ancestor's height).
 *
 * Requires the preview container to declare `container-type: size`.
 *
 * @param {number} uiValue — UI font size value (e.g. 34 for default quote)
 * @returns {string} CSS length, e.g. "12.59cqh"
 */
export function fsqPreviewCanvasHeightUnit(uiValue) {
  if (!uiValue || !Number.isFinite(uiValue)) return '0cqh'
  const pct = (uiValue * FSQ_PNG_SCALE / FSQ_PNG_REF_HEIGHT) * 100
  return `${pct.toFixed(3)}cqh`
}

// Padding: 10% of black region dimensions (symmetric)
// render_fsq_png.py lines 112-113
export const FSQ_PADDING = {
  horizontal: 10, // % of black bar width (= canvas width)
  vertical: 10,   // % of black bar height
}

// Colors — render_fsq_png.py lines 108-109
export const FSQ_COLORS = {
  text: 'rgba(255, 255, 255, 1)',
  attribution: 'rgb(200, 200, 200)',
}

// Font family CSS map — ordered to match server-side fonts first
// render_fsq_png.py lines 39-53 uses Liberation/DejaVu TTF files
export const FSQ_FONT_MAP = {
  'sans-serif': 'Arial, Helvetica, "Liberation Sans", sans-serif',
  'serif': '"Liberation Serif", Georgia, "Times New Roman", serif',
  'monospace': '"Courier New", Courier, monospace',
}

/**
 * Line height from lineSpacing parameter.
 * Matches: 1 + (line_spacing_percent / 100) in render_fsq_png.py line 209
 */
export function computeLineHeight(lineSpacing) {
  return 1 + ((lineSpacing ?? FSQ_DEFAULTS.lineSpacing) / 100)
}

/**
 * CSS styles for the black bar overlay.
 * Renderer centers the bar vertically: black_region_y = (height - black_region_height) // 2
 * render_fsq_png.py line 103
 */
export function computeBlackBarStyle(boxHeight, boxOpacity) {
  const h = boxHeight ?? FSQ_DEFAULTS.boxHeight
  const o = boxOpacity ?? FSQ_DEFAULTS.boxOpacity
  const topPercent = (100 - h) / 2
  return {
    position: 'absolute',
    top: `${topPercent}%`,
    left: '0',
    width: '100%',
    height: `${h}%`,
    background: `rgba(0, 0, 0, ${o / 100})`,
    zIndex: 2,
    pointerEvents: 'none',
  }
}

/**
 * CSS styles for the quote content overlay.
 *
 * The renderer uses 10% of the black bar's OWN dimensions for padding:
 *   padding_x = black_region_width * 0.1   (10% of width)
 *   padding_y = black_region_height * 0.1  (10% of height)
 *
 * In CSS, percentage padding is relative to the element's WIDTH (not height).
 * The overlay element has height = boxHeight% of a 16:9 container.
 * So the black bar's pixel height = (boxHeight/100) * containerWidth * (9/16).
 * 10% of that = (boxHeight/100) * (9/16) * 10% of containerWidth.
 * As a CSS padding percentage: vertPad = boxHeight * 9 / 160.
 *
 * For boxHeight=80: 80 * 9 / 160 = 4.5%
 */
export function computeQuoteOverlayStyle(boxHeight) {
  const h = boxHeight ?? FSQ_DEFAULTS.boxHeight
  const topPercent = (100 - h) / 2
  const vertPad = (h * 9 / 160).toFixed(2)
  const horizPad = FSQ_PADDING.horizontal
  return {
    position: 'absolute',
    top: `${topPercent}%`,
    left: '0',
    width: '100%',
    height: `${h}%`,
    padding: `${vertPad}% ${horizPad}%`,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    zIndex: 3,
    boxSizing: 'border-box',
    color: FSQ_COLORS.text,
  }
}

/**
 * CSS styles for attribution positioning.
 * Renderer: positioned at bottom of black bar with 10% margin.
 * For centered text: bottom-right. For left/right: bottom-left.
 * render_fsq_png.py lines 319-336
 */
export function computeAttributionStyle(alignment) {
  const a = alignment ?? FSQ_DEFAULTS.alignment
  const vertPad = (FSQ_DEFAULTS.boxHeight * 9 / 160).toFixed(2)
  return {
    position: 'absolute',
    bottom: `${vertPad}%`,
    left: `${FSQ_PADDING.horizontal}%`,
    right: `${FSQ_PADDING.horizontal}%`,
    color: FSQ_COLORS.attribution,
    textAlign: a === 'center' ? 'right' : 'left',
    fontWeight: '500',
    textShadow: '1px 1px 3px rgba(0,0,0,0.8)',
  }
}
