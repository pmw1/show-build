/**
 * SINGLE SOURCE OF TRUTH for all rundown item types
 * All components should import from this file to ensure consistency
 */

export const ITEM_TYPES = [
  // Core content types
  { 
    title: 'Segment', 
    value: 'segment', 
    category: 'Core', 
    description: 'Main content segments of the show',
    color: 'info',
    icon: 'mdi-television-classic',
    sortOrder: 1
  },
  { 
    title: 'Advertisement', 
    value: 'ad', 
    category: 'Core', 
    description: 'Commercial advertisement breaks',
    color: 'primary',
    icon: 'mdi-currency-usd',
    sortOrder: 2
  },
  { 
    title: 'Promo', 
    value: 'promo', 
    category: 'Core', 
    description: 'Promotional content for upcoming shows',
    color: 'success',
    icon: 'mdi-bullhorn',
    sortOrder: 3
  },
  { 
    title: 'Call to Action', 
    value: 'cta', 
    category: 'Core', 
    description: 'Direct viewer engagement prompts',
    color: 'accent',
    icon: 'mdi-hand-pointing-right',
    sortOrder: 4
  },
  { 
    title: 'Transition', 
    value: 'trans', 
    category: 'Core', 
    description: 'Smooth transitions between segments',
    color: 'secondary',
    icon: 'mdi-arrow-right',
    sortOrder: 5
  },
  
  // Broadcast production types
  { 
    title: 'Package (PKG)', 
    value: 'pkg', 
    category: 'Production', 
    description: 'Pre-produced story packages',
    color: 'purple',
    icon: 'mdi-package-variant',
    sortOrder: 10
  },
  { 
    title: 'Voice Over (VO)', 
    value: 'vo', 
    category: 'Production', 
    description: 'Narrator voice over content',
    color: 'deep-orange',
    icon: 'mdi-microphone',
    sortOrder: 11
  },
  { 
    title: 'Sound on Tape (SOT)', 
    value: 'sot', 
    category: 'Production', 
    description: 'Pre-recorded audio/video content',
    color: 'amber',
    icon: 'mdi-tape-drive',
    sortOrder: 12
  },
  { 
    title: 'Interview', 
    value: 'interview', 
    category: 'Production', 
    description: 'Guest interviews and conversations',
    color: 'teal',
    icon: 'mdi-account-voice',
    sortOrder: 13
  },
  { 
    title: 'Live Shot', 
    value: 'live', 
    category: 'Production', 
    description: 'Live remote broadcasts and reports',
    color: 'red',
    icon: 'mdi-broadcast',
    sortOrder: 14
  },
  { 
    title: 'Break', 
    value: 'break', 
    category: 'Production', 
    description: 'Commercial or station breaks',
    color: 'brown',
    icon: 'mdi-pause',
    sortOrder: 15
  },
  { 
    title: 'Tease', 
    value: 'tease', 
    category: 'Production', 
    description: 'Content teasers and previews',
    color: 'pink',
    icon: 'mdi-eye-outline',
    sortOrder: 16
  },
  { 
    title: 'Tag', 
    value: 'tag', 
    category: 'Production', 
    description: 'Closing remarks and tags',
    color: 'indigo',
    icon: 'mdi-tag',
    sortOrder: 17
  },
  { 
    title: 'Bump', 
    value: 'bump', 
    category: 'Production', 
    description: 'Short transition elements',
    color: 'deep-purple',
    icon: 'mdi-arrow-decision',
    sortOrder: 18
  },
  
  // Technical elements
  { 
    title: 'Music Bed', 
    value: 'music', 
    category: 'Technical', 
    description: 'Background music and audio beds',
    color: 'orange',
    icon: 'mdi-music',
    sortOrder: 20
  },
  { 
    title: 'Graphics (GFX)', 
    value: 'gfx', 
    category: 'Technical', 
    description: 'Visual graphics and animations',
    color: 'cyan',
    icon: 'mdi-image',
    sortOrder: 21
  },
  { 
    title: 'Full Screen Quote (FSQ)', 
    value: 'fsq', 
    category: 'Technical', 
    description: 'Full screen quote displays',
    color: 'lime',
    icon: 'mdi-format-quote-close',
    sortOrder: 22
  },
  { 
    title: 'Natural Sound (NAT)', 
    value: 'nat', 
    category: 'Technical', 
    description: 'Natural ambient sound',
    color: 'light-green',
    icon: 'mdi-volume-high',
    sortOrder: 23
  },
  { 
    title: 'Vox Pop', 
    value: 'vox', 
    category: 'Technical', 
    description: 'Person-on-the-street interviews',
    color: 'yellow',
    icon: 'mdi-account-group',
    sortOrder: 24
  },
  { 
    title: 'Credits', 
    value: 'credits', 
    category: 'Technical', 
    description: 'End credits and acknowledgments',
    color: 'blue-grey',
    icon: 'mdi-format-list-bulleted',
    sortOrder: 25
  },
  
  // Content categories
  { 
    title: 'Weather', 
    value: 'weather', 
    category: 'Content', 
    description: 'Weather reports and forecasts',
    color: 'light-blue',
    icon: 'mdi-weather-partly-cloudy',
    sortOrder: 30
  },
  { 
    title: 'Sports', 
    value: 'sports', 
    category: 'Content', 
    description: 'Sports news and highlights',
    color: 'green-darken-2',
    icon: 'mdi-soccer',
    sortOrder: 31
  },
  { 
    title: 'News Brief', 
    value: 'brief', 
    category: 'Content', 
    description: 'Short news updates',
    color: 'grey-lighten-2',
    icon: 'mdi-newspaper-variant',
    sortOrder: 32
  },
  { 
    title: 'Reader', 
    value: 'reader', 
    category: 'Content', 
    description: 'Anchor-read news content',
    color: 'amber-lighten-2',
    icon: 'mdi-script-text',
    sortOrder: 33
  },
  { 
    title: 'Open/Close', 
    value: 'openclose', 
    category: 'Content', 
    description: 'Show opening and closing segments',
    color: 'purple-darken-2',
    icon: 'mdi-television-play',
    sortOrder: 34
  }
];

// Helper functions to work with item types
export const getItemTypeByValue = (value) => {
  return ITEM_TYPES.find(type => type.value === value);
};

export const getItemTypesByCategory = (category) => {
  return ITEM_TYPES.filter(type => type.category === category);
};

export const getAllItemTypes = () => {
  return [...ITEM_TYPES].sort((a, b) => a.sortOrder - b.sortOrder);
};

export const getItemTypesForDropdown = () => {
  return ITEM_TYPES.map(type => ({
    title: type.title,
    value: type.value
  })).sort((a, b) => a.title.localeCompare(b.title));
};

export const getItemTypesForColorSelector = () => {
  const excludedTypes = ['gfx', 'fsq', 'nat', 'vox', 'credits', 'weather', 'sports', 'brief', 'openclose'];
  return ITEM_TYPES
    .filter(type => !excludedTypes.includes(type.value))
    .map(type => type.value);
};

export const getItemTypeIcon = (value) => {
  const type = getItemTypeByValue(value);
  return type ? type.icon : 'mdi-help-circle';
};

export const getItemTypeColor = (value) => {
  const type = getItemTypeByValue(value);
  return type ? type.color : 'grey';
};

export const CATEGORIES = [
  { name: 'Core', description: 'Essential content types for any show', icon: 'mdi-television-classic' },
  { name: 'Production', description: 'Production workflow elements', icon: 'mdi-broadcast' },
  { name: 'Technical', description: 'Technical and audio/visual elements', icon: 'mdi-cog' },
  { name: 'Content', description: 'Specialized content categories', icon: 'mdi-newspaper-variant' }
];

// Generate color mappings for the theme system
export const generateColorMappings = () => {
  const mappings = {};
  ITEM_TYPES.forEach(type => {
    mappings[type.value] = type.color;
  });
  return mappings;
};