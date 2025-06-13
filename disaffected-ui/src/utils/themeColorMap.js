// Default fallback colors if nothing is loaded
const defaultColors = {
  'segment': 'purple-accent',
  'advert': 'blue-accent',
  'promo': 'green-accent',
  'cta': 'red-accent',
  'trans': 'yellow-accent',
  'unknown': 'grey-light'
};

// Load colors from storage
const loadSavedColors = () => {
  try {
    const saved = localStorage.getItem('rundownColorMap');
    if (saved) {
      console.log("[DEBUG] Loading saved colors:", JSON.parse(saved));
      return JSON.parse(saved);
    }
  } catch (err) {
    console.error("[ERROR] Failed to load saved colors:", err);
  }
  return defaultColors;
};

// Initialize colors with saved values or defaults
let currentColors = loadSavedColors();

// Save current color mappings
export const saveColorMap = (newColors) => {
  try {
    localStorage.setItem('rundownColorMap', JSON.stringify(newColors));
    currentColors = newColors;
    console.log("[DEBUG] Saved new color mappings:", newColors);
  } catch (err) {
    console.error("[ERROR] Failed to save color mappings:", err);
  }
};

// Add the missing updateColor function
export const updateColor = (type, newColor) => {
  try {
    console.log("[DEBUG] Updating color:", { type, newColor });
    const updatedColors = { ...currentColors };
    updatedColors[type.toLowerCase()] = newColor;
    saveColorMap(updatedColors);
    return true;
  } catch (err) {
    console.error("[ERROR] Failed to update color:", err);
    return false;
  }
};

// Export getColorValue function
export const getColorValue = (type) => {
  if (!type) return 'grey-light';
  
  const normalizedType = type.toLowerCase();
  const color = currentColors[normalizedType] || defaultColors[normalizedType] || 'grey-light';
  
  console.log("[DEBUG] Color lookup:", {
    type,
    normalized: normalizedType,
    result: color
  });
  
  return color;
};

export { defaultColors };