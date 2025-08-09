// Default fallback colors using Vuetify theme colors
const defaultColors = {
  'segment': 'info',         // #2196F3
  'ad': 'primary',           // #1976D2
  'promo': 'success',        // #4CAF50
  'cta': 'accent',           // #82B1FF
  'trans': 'secondary',      // #424242
  'unknown': 'grey',         // #9E9E9E
  // UI/System colors
  'selection': 'warning',    // #FB8C00
  'hover': 'blue-lighten-4', // #BBDEFB
  'draglight': 'cyan-lighten-4', // #B2EBF2
  'highlight': 'yellow-lighten-3', // #FFF9C4
  'dropline': 'green-lighten-4', // #C8E6C9
  // Status highlight colors
  'draft': 'grey-darken-2',  // #616161
  'approved': 'green-accent', // #69F0AE
  'production': 'blue-accent', // #448AFF
  'completed': 'yellow-accent' // #FFD740
};

// Export defaultColors for external use
export { defaultColors };

// Load colors from localStorage or use defaults
let currentColors = { ...defaultColors };
try {
  const storedColors = localStorage.getItem('themeColors');
  if (storedColors) {
    currentColors = { ...defaultColors, ...JSON.parse(storedColors) };
  }
} catch (err) {
  console.warn('Failed to load stored colors, using defaults:', err);
}

export const updateColor = (type, newColor) => {
  try {
    const updatedColors = { ...currentColors, [type.toLowerCase()]: newColor };
    currentColors = updatedColors;
    localStorage.setItem('themeColors', JSON.stringify(updatedColors));
    
    // Also send to backend if available
    fetch('/api/settings/colors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ colors: updatedColors })
    }).catch(err => console.warn('Failed to save colors to backend:', err));
    
    return true;
  } catch (err) {
    console.error('Failed to update color:', err);
    return false;
  }
};

export const getColorValue = (type) => {
  return currentColors[type.toLowerCase()] || defaultColors[type.toLowerCase()] || 'grey';
};

export const getAllColors = () => {
  return { ...currentColors };
};

export const resolveVuetifyColor = (colorName, vuetifyInstance, textColor = '#FFFFFF') => {
  if (!colorName) return '#000000';
  if (!vuetifyInstance?.theme?.themes) return '#000000';
  
  const theme = vuetifyInstance.theme.themes[vuetifyInstance.theme.dark ? 'dark' : 'light'].colors;
  const color = theme[colorName] || '#000000';
  
  // Check contrast ratio for accessibility
  const contrastRatio = getContrastRatio(color, textColor);
  if (contrastRatio < 4.5) {
    console.warn(`Low contrast for ${colorName}: ${color} (ratio: ${contrastRatio})`);
    return '#000000'; // Return black for better contrast
  }
  
  return color;
};

// Calculate contrast ratio for WCAG compliance
const getContrastRatio = (color1, color2) => {
  const luminance = (hex) => {
    const rgb = parseInt(hex.replace('#', ''), 16);
    const r = (rgb >> 16) & 0xff;
    const g = (rgb >> 8) & 0xff;
    const b = rgb & 0xff;
    
    // Convert to relative luminance
    const toLinear = (c) => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    };
    
    return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
  };
  
  const lum1 = luminance(color1);
  const lum2 = luminance(color2);
  
  return (Math.max(lum1, lum2) + 0.05) / (Math.min(lum1, lum2) + 0.05);
};