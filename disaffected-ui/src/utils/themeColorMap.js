// Default fallback colors using Vuetify theme colors
const defaultColors = {
  // Core content types
  'segment': 'info',         // #2196F3 - Blue
  'ad': 'primary',           // #1976D2 - Dark Blue
  'promo': 'success',        // #4CAF50 - Green
  'cta': 'accent',           // #82B1FF - Light Blue
  'trans': 'secondary',      // #424242 - Grey
  'unknown': 'grey',         // #9E9E9E - Light Grey
  
  // Broadcast production types
  'pkg': 'purple',           // #9C27B0 - Purple for packages
  'vo': 'deep-orange',       // #FF5722 - Orange for voice over
  'sot': 'amber',            // #FFC107 - Amber for sound on tape
  'interview': 'teal',       // #009688 - Teal for interviews
  'live': 'red',             // #F44336 - Red for live shots
  'break': 'brown',          // #795548 - Brown for breaks
  'tease': 'pink',           // #E91E63 - Pink for teases
  'tag': 'indigo',           // #3F51B5 - Indigo for tags
  'bump': 'deep-purple',     // #673AB7 - Deep purple for bumps
  'music': 'orange',         // #FF9800 - Orange for music
  'gfx': 'cyan',             // #00BCD4 - Cyan for graphics
  'fsq': 'lime',             // #CDDC39 - Lime for full screen quotes
  'nat': 'light-green',      // #8BC34A - Light green for natural sound
  'vox': 'yellow',           // #FFEB3B - Yellow for vox pops
  'credits': 'blue-grey',    // #607D8B - Blue grey for credits
  'weather': 'light-blue',   // #03A9F4 - Light blue for weather
  'sports': 'green-darken-2',// #388E3C - Dark green for sports
  'brief': 'grey-lighten-2', // #E0E0E0 - Light grey for news briefs
  'reader': 'amber-lighten-2', // #FFD54F - Light amber for readers
  'openclose': 'purple-darken-2', // #7B1FA2 - Dark purple for open/close
  
  // UI/System colors
  'selection': 'warning',    // #FB8C00 - Orange
  'hover': 'blue-lighten-4', // #BBDEFB - Very light blue
  'draglight': 'cyan-lighten-4', // #B2EBF2 - Very light cyan
  'highlight': 'yellow-lighten-3', // #FFF9C4 - Very light yellow
  'dropline': 'green-lighten-4', // #C8E6C9 - Very light green
  
  // Status highlight colors
  'draft': 'grey-darken-2',  // #616161 - Dark grey
  'approved': 'green-accent', // #69F0AE - Bright green
  'production': 'blue-accent', // #448AFF - Bright blue
  'completed': 'yellow-accent' // #FFD740 - Bright yellow
};

// Export defaultColors for external use
export { defaultColors };

// Initialize with defaults only - no localStorage loading on import
let currentColors = { ...defaultColors };
let hasLoadedFromDatabase = false;

export const updateColor = (type, newColor) => {
  try {
    const updatedColors = { ...currentColors, [type.toLowerCase()]: newColor };
    currentColors = updatedColors;
    localStorage.setItem('themeColors', JSON.stringify(updatedColors));
    
    // Note: Individual color updates are now handled by ColorSelector component
    // which saves the complete color profile to the database
    
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

export const loadColorsFromDatabase = async (profile = 'default') => {
  try {
    console.log(`Loading colors from database for profile: ${profile}`);
    const response = await fetch(`/api/settings/colors?profile=${profile}`);
    
    if (response.ok) {
      const data = await response.json();
      console.log('Database response:', data);
      if (data.success && data.colors) {
        // Update current colors with database values
        currentColors = { ...defaultColors, ...data.colors };
        hasLoadedFromDatabase = true;
        // Also update localStorage as backup
        localStorage.setItem('themeColors', JSON.stringify(currentColors));
        console.log('Colors loaded from database successfully:', currentColors);
        return currentColors;
      }
    }
  } catch (error) {
    console.log('Could not load colors from database, trying localStorage fallback:', error);
    
    // Fallback to localStorage only if database fails AND we haven't loaded before
    if (!hasLoadedFromDatabase) {
      try {
        const storedColors = localStorage.getItem('themeColors');
        if (storedColors) {
          const parsedColors = JSON.parse(storedColors);
          currentColors = { ...defaultColors, ...parsedColors };
          console.log('Colors loaded from localStorage fallback:', currentColors);
        }
      } catch (localStorageError) {
        console.warn('Failed to load from localStorage, using defaults:', localStorageError);
      }
    }
  }
  
  return currentColors;
};

export const resolveVuetifyColor = (colorName, vuetifyInstance) => {
  if (!colorName) return '#9E9E9E'; // Return grey instead of black
  
  // If it's already a hex color, return it
  if (colorName.startsWith('#')) {
    return colorName;
  }
  
  // Standard Vuetify color palette with variants
  const vuetifyColors = {
    'red': '#F44336',
    'red-lighten-1': '#EF5350',
    'red-lighten-2': '#E57373',
    'red-lighten-3': '#EF9A9A',
    'red-lighten-4': '#FFCDD2',
    'red-darken-1': '#E53935',
    'red-darken-2': '#D32F2F',
    'red-darken-3': '#C62828',
    'red-darken-4': '#B71C1C',
    'pink': '#E91E63',
    'purple': '#9C27B0',
    'deep-purple': '#673AB7',
    'deep-purple-lighten-1': '#7986CB',
    'deep-purple-lighten-2': '#9575CD',
    'deep-purple-lighten-3': '#B39DDB',
    'deep-purple-lighten-4': '#D1C4E9',
    'deep-purple-lighten-5': '#EDE7F6',
    'deep-purple-darken-1': '#5E35B1',
    'deep-purple-darken-2': '#512DA8',
    'deep-purple-darken-3': '#4527A0',
    'deep-purple-darken-4': '#311B92',
    'indigo': '#3F51B5',
    'blue': '#2196F3',
    'blue-lighten-1': '#42A5F5',
    'blue-lighten-2': '#64B5F6',
    'blue-lighten-3': '#90CAF9',
    'blue-lighten-4': '#BBDEFB',
    'blue-lighten-5': '#E3F2FD',
    'blue-darken-1': '#1E88E5',
    'blue-darken-2': '#1976D2',
    'blue-darken-3': '#1565C0',
    'blue-darken-4': '#0D47A1',
    'light-blue': '#03A9F4',
    'light-blue-lighten-1': '#29B6F6',
    'light-blue-lighten-2': '#4FC3F7',
    'light-blue-lighten-3': '#81D4FA',
    'light-blue-lighten-4': '#B3E5FC',
    'light-blue-lighten-5': '#E1F5FE',
    'light-blue-darken-1': '#039BE5',
    'light-blue-darken-2': '#0288D1',
    'light-blue-darken-3': '#0277BD',
    'light-blue-darken-4': '#01579B',
    'cyan': '#00BCD4',
    'cyan-lighten-1': '#26C6DA',
    'cyan-lighten-2': '#4DD0E1',
    'cyan-lighten-3': '#80DEEA',
    'cyan-lighten-4': '#B2EBF2',
    'teal': '#009688',
    'green': '#4CAF50',
    'green-lighten-1': '#66BB6A',
    'green-lighten-2': '#81C784',
    'green-lighten-3': '#A5D6A7',
    'green-lighten-4': '#C8E6C9',
    'green-darken-1': '#43A047',
    'green-darken-2': '#388E3C',
    'green-darken-3': '#2E7D32',
    'green-darken-4': '#1B5E20',
    'green-accent': '#69F0AE',
    'light-green': '#8BC34A',
    'light-green-lighten-1': '#9CCC65',
    'light-green-lighten-2': '#AED581',
    'light-green-lighten-3': '#C5E1A5',
    'light-green-lighten-4': '#DCEDC8',
    'light-green-lighten-5': '#F1F8E9',
    'light-green-darken-1': '#7CB342',
    'light-green-darken-2': '#689F38',
    'light-green-darken-3': '#558B2F',
    'light-green-darken-4': '#33691E',
    'lime': '#CDDC39',
    'yellow': '#FFEB3B',
    'yellow-lighten-1': '#FFEE58',
    'yellow-lighten-2': '#FFF176',
    'yellow-lighten-3': '#FFF59D',
    'yellow-lighten-4': '#FFF9C4',
    'yellow-accent': '#FFD740',
    'amber': '#FFC107',
    'amber-lighten-1': '#FFCA28',
    'amber-lighten-2': '#FFD54F',
    'amber-lighten-3': '#FFE082',
    'amber-lighten-4': '#FFECB3',
    'amber-darken-1': '#FFB300',
    'amber-darken-2': '#FFA000',
    'amber-darken-3': '#FF8F00',
    'amber-darken-4': '#FF6F00',
    'orange': '#FF9800',
    'orange-lighten-1': '#FFA726',
    'orange-lighten-2': '#FFB74D',
    'orange-lighten-3': '#FFCC80',
    'orange-lighten-4': '#FFE0B2',
    'orange-lighten-5': '#FFF3E0',
    'orange-darken-1': '#FB8C00',
    'orange-darken-2': '#F57C00',
    'orange-darken-3': '#EF6C00',
    'orange-darken-4': '#E65100',
    'deep-orange': '#FF5722',
    'deep-orange-lighten-1': '#FF6434',
    'deep-orange-lighten-2': '#FF7043',
    'deep-orange-lighten-3': '#FF8A65',
    'deep-orange-lighten-4': '#FFAB91',
    'deep-orange-lighten-5': '#FBE9E7',
    'deep-orange-darken-1': '#F4511E',
    'deep-orange-darken-2': '#E64A19',
    'deep-orange-darken-3': '#D84315',
    'deep-orange-darken-4': '#BF360C',
    'brown': '#795548',
    'grey': '#9E9E9E',
    'grey-lighten-1': '#BDBDBD',
    'grey-lighten-2': '#E0E0E0',
    'grey-lighten-3': '#EEEEEE',
    'grey-lighten-4': '#F5F5F5',
    'grey-darken-1': '#757575',
    'grey-darken-2': '#616161',
    'grey-darken-3': '#424242',
    'grey-darken-4': '#212121',
    'blue-grey': '#607D8B',
    'blue-grey-lighten-1': '#78909C',
    'blue-grey-lighten-2': '#90A4AE',
    'blue-grey-lighten-3': '#B0BEC5',
    'blue-grey-lighten-4': '#CFD8DC',
    'blue-grey-lighten-5': '#ECEFF1',
    'blue-grey-darken-1': '#546E7A',
    'blue-grey-darken-2': '#455A64',
    'blue-grey-darken-3': '#37474F',
    'blue-grey-darken-4': '#263238',
    // Theme colors
    'primary': '#1976D2',
    'primary-lighten-1': '#42A5F5',
    'primary-lighten-2': '#64B5F6',
    'primary-lighten-3': '#90CAF9',
    'primary-lighten-4': '#BBDEFB',
    'primary-darken-1': '#1565C0',
    'primary-darken-2': '#0D47A1',
    'secondary': '#424242',
    'secondary-lighten-1': '#616161',
    'secondary-lighten-2': '#757575',
    'secondary-lighten-3': '#9E9E9E',
    'secondary-lighten-4': '#BDBDBD',
    'secondary-darken-1': '#212121',
    'accent': '#82B1FF',
    'error': '#FF5252',
    'info': '#2196F3',
    'info-lighten-1': '#42A5F5',
    'info-lighten-2': '#64B5F6',
    'info-lighten-3': '#90CAF9',
    'info-lighten-4': '#BBDEFB',
    'info-darken-1': '#1E88E5',
    'info-darken-2': '#1976D2',
    'success': '#4CAF50',
    'success-lighten-1': '#66BB6A',
    'success-lighten-2': '#81C784',
    'success-lighten-3': '#A5D6A7',
    'success-lighten-4': '#C8E6C9',
    'success-darken-1': '#43A047',
    'success-darken-2': '#388E3C',
    'warning': '#FB8C00',
    'warning-lighten-1': '#FFA726',
    'warning-lighten-2': '#FFB74D',
    'warning-lighten-3': '#FFCC80',
    'warning-lighten-4': '#FFE0B2',
    'warning-darken-1': '#F57C00',
    'warning-darken-2': '#EF6C00',
    'warning-darken-3': '#E65100'
  };
  
  // Try to get from Vuetify theme if available
  if (vuetifyInstance && vuetifyInstance.theme && vuetifyInstance.theme.themes) {
    const currentTheme = vuetifyInstance.theme.dark ? 'dark' : 'light';
    const theme = vuetifyInstance.theme.themes[currentTheme];
    if (theme && theme.colors && theme.colors[colorName]) {
      return theme.colors[colorName];
    }
  }
  
  // Return from standard palette or grey as fallback
  return vuetifyColors[colorName] || vuetifyColors[colorName.split('-')[0]] || '#9E9E9E';
};

// Contrast ratio function removed - was causing colors to display as black
// If contrast checking is needed in the future, it should be done differently

// Legacy themeColorMap export for backward compatibility
export const themeColorMap = {
  // Core content types
  get segment() { return { textColor: '#ffffff', backgroundColor: getColorValue('segment') } },
  get ad() { return { textColor: '#ffffff', backgroundColor: getColorValue('ad') } },
  get promo() { return { textColor: '#ffffff', backgroundColor: getColorValue('promo') } },
  get cta() { return { textColor: '#ffffff', backgroundColor: getColorValue('cta') } },
  get trans() { return { textColor: '#ffffff', backgroundColor: getColorValue('trans') } },
  get unknown() { return { textColor: '#ffffff', backgroundColor: getColorValue('unknown') } },
  
  // Broadcast production types
  get pkg() { return { textColor: '#ffffff', backgroundColor: getColorValue('pkg') } },
  get vo() { return { textColor: '#ffffff', backgroundColor: getColorValue('vo') } },
  get sot() { return { textColor: '#ffffff', backgroundColor: getColorValue('sot') } },
  get interview() { return { textColor: '#ffffff', backgroundColor: getColorValue('interview') } },
  get live() { return { textColor: '#ffffff', backgroundColor: getColorValue('live') } },
  get break() { return { textColor: '#ffffff', backgroundColor: getColorValue('break') } },
  get tease() { return { textColor: '#ffffff', backgroundColor: getColorValue('tease') } },
  get tag() { return { textColor: '#ffffff', backgroundColor: getColorValue('tag') } },
  get bump() { return { textColor: '#ffffff', backgroundColor: getColorValue('bump') } },
  get music() { return { textColor: '#ffffff', backgroundColor: getColorValue('music') } },
  get gfx() { return { textColor: '#ffffff', backgroundColor: getColorValue('gfx') } },
  get fsq() { return { textColor: '#ffffff', backgroundColor: getColorValue('fsq') } },
  get nat() { return { textColor: '#ffffff', backgroundColor: getColorValue('nat') } },
  get vox() { return { textColor: '#ffffff', backgroundColor: getColorValue('vox') } },
  get credits() { return { textColor: '#ffffff', backgroundColor: getColorValue('credits') } },
  get weather() { return { textColor: '#ffffff', backgroundColor: getColorValue('weather') } },
  get sports() { return { textColor: '#ffffff', backgroundColor: getColorValue('sports') } },
  get brief() { return { textColor: '#ffffff', backgroundColor: getColorValue('brief') } },
  get reader() { return { textColor: '#ffffff', backgroundColor: getColorValue('reader') } },
  get openclose() { return { textColor: '#ffffff', backgroundColor: getColorValue('openclose') } },
  
  // Status colors
  get draft() { return { textColor: '#ffffff', backgroundColor: getColorValue('draft') } },
  get approved() { return { textColor: '#ffffff', backgroundColor: getColorValue('approved') } },
  get production() { return { textColor: '#ffffff', backgroundColor: getColorValue('production') } },
  get completed() { return { textColor: '#ffffff', backgroundColor: getColorValue('completed') } }
};