/**
 * SINGLE SOURCE OF TRUTH for CORE rundown item types
 * Core types are hardcoded and cannot be deleted by users.
 * Custom types are stored in the database (content_type_settings table).
 *
 * NOTE: This file is for RUNDOWN ITEM TYPES only.
 * Cue types (SOT, VO, GFX, FSQ, etc.) are handled separately in the cue system.
 */

// Category constants
export const TYPE_CATEGORY = {
  CORE: 'Core Rundown Items',
  CUSTOM: 'Custom Rundown Items'
};

/**
 * CORE RUNDOWN ITEM TYPES
 * These are the structural building blocks of a rundown/show.
 * NOT cue types (SOT, VO, GFX, etc.) - those go INSIDE rundown items.
 */
export const CORE_ITEM_TYPES = [
  {
    title: 'Segment',
    value: 'segment',
    category: TYPE_CATEGORY.CORE,
    description: 'Main content segments of the show',
    color: 'info',
    icon: 'mdi-television-classic',
    sortOrder: 1,
    isCore: true
  },
  {
    title: 'Cold Open',
    value: 'coldopen',
    category: TYPE_CATEGORY.CORE,
    description: 'Opening segment before title sequence',
    color: 'blue',
    icon: 'mdi-play-circle-outline',
    sortOrder: 2,
    isCore: true
  },
  {
    title: 'Tease',
    value: 'tease',
    category: TYPE_CATEGORY.CORE,
    description: 'Content teasers and coming-up previews',
    color: 'pink',
    icon: 'mdi-eye-outline',
    sortOrder: 3,
    isCore: true
  },
  {
    title: 'Interview',
    value: 'interview',
    category: TYPE_CATEGORY.CORE,
    description: 'Guest interviews and conversations',
    color: 'teal',
    icon: 'mdi-account-voice',
    sortOrder: 4,
    isCore: true
  },
  {
    title: 'Reader',
    value: 'reader',
    category: TYPE_CATEGORY.CORE,
    description: 'Anchor-read news stories',
    color: 'amber-lighten-2',
    icon: 'mdi-script-text',
    sortOrder: 5,
    isCore: true
  },
  {
    title: 'Advertisement',
    value: 'ad',
    category: TYPE_CATEGORY.CORE,
    description: 'Commercial advertisement breaks',
    color: 'primary',
    icon: 'mdi-currency-usd',
    sortOrder: 10,
    isCore: true
  },
  {
    title: 'Promo',
    value: 'promo',
    category: TYPE_CATEGORY.CORE,
    description: 'Promotional content for upcoming shows',
    color: 'success',
    icon: 'mdi-bullhorn',
    sortOrder: 11,
    isCore: true
  },
  {
    title: 'Call to Action',
    value: 'cta',
    category: TYPE_CATEGORY.CORE,
    description: 'Direct viewer engagement prompts',
    color: 'accent',
    icon: 'mdi-hand-pointing-right',
    sortOrder: 12,
    isCore: true
  }
];

// Legacy export for backward compatibility
export const ITEM_TYPES = CORE_ITEM_TYPES;

// ============================================================================
// HELPER FUNCTIONS - Work with both Core and Custom types
// ============================================================================

// Internal cache for custom types (populated via mergeWithCustomTypes)
let _customTypes = [];

/**
 * Merge core types with custom types from API
 * Call this after fetching custom types from the backend
 * @param {Array} customTypes - Custom types from content_type_settings API
 */
export const mergeWithCustomTypes = (customTypes) => {
  _customTypes = (customTypes || []).map(ct => ({
    title: ct.display_name || ct.title,
    value: ct.type_name || ct.value,
    category: TYPE_CATEGORY.CUSTOM,
    description: ct.description || '',
    color: ct.color || 'grey',
    icon: ct.icon || 'mdi-shape',
    sortOrder: ct.sort_order || 100,
    isCore: false,
    isReusable: ct.is_reusable || false,
    defaultDuration: ct.default_duration || '00:00:30'
  }));
};

/**
 * Get all item types (core + custom merged)
 * @returns {Array} Combined and sorted list of all item types
 */
export const getAllItemTypes = () => {
  // Filter out custom types that override core types (by value)
  const coreValues = CORE_ITEM_TYPES.map(t => t.value);
  const uniqueCustom = _customTypes.filter(ct => !coreValues.includes(ct.value));
  return [...CORE_ITEM_TYPES, ...uniqueCustom].sort((a, b) => a.sortOrder - b.sortOrder);
};

/**
 * Get only core item types
 * @returns {Array} Core item types only
 */
export const getCoreItemTypes = () => {
  return [...CORE_ITEM_TYPES].sort((a, b) => a.sortOrder - b.sortOrder);
};

/**
 * Get only custom item types
 * @returns {Array} Custom item types only
 */
export const getCustomItemTypes = () => {
  return [..._customTypes].sort((a, b) => a.sortOrder - b.sortOrder);
};

/**
 * Get item type by value (searches both core and custom)
 * @param {string} value - The type value to find
 * @returns {Object|undefined} The matching item type
 */
export const getItemTypeByValue = (value) => {
  const coreMatch = CORE_ITEM_TYPES.find(type => type.value === value);
  if (coreMatch) return coreMatch;
  return _customTypes.find(type => type.value === value);
};

/**
 * Get item types by category (Core Rundown Items or Custom Rundown Items)
 * @param {string} category - TYPE_CATEGORY.CORE or TYPE_CATEGORY.CUSTOM
 * @returns {Array} Filtered item types
 */
export const getItemTypesByCategory = (category) => {
  if (category === TYPE_CATEGORY.CORE) {
    return getCoreItemTypes();
  } else if (category === TYPE_CATEGORY.CUSTOM) {
    return getCustomItemTypes();
  }
  return getAllItemTypes().filter(type => type.category === category);
};

/**
 * Get item types for dropdown selection
 * @returns {Array} Types formatted for dropdown
 */
export const getItemTypesForDropdown = () => {
  return getAllItemTypes().map(type => ({
    title: type.title,
    value: type.value,
    isCore: type.isCore
  })).sort((a, b) => a.title.localeCompare(b.title));
};

/**
 * Get icon for an item type
 * @param {string} value - The type value
 * @returns {string} MDI icon name
 */
export const getItemTypeIcon = (value) => {
  const type = getItemTypeByValue(value);
  return type ? type.icon : 'mdi-help-circle';
};

/**
 * Get default color for an item type
 * @param {string} value - The type value
 * @returns {string} Color name
 */
export const getItemTypeColor = (value) => {
  const type = getItemTypeByValue(value);
  return type ? type.color : 'grey';
};

/**
 * Check if a type value is a core type
 * @param {string} value - The type value to check
 * @returns {boolean} True if core type
 */
export const isCoreType = (value) => {
  return CORE_ITEM_TYPES.some(type => type.value === value);
};

/**
 * Check if a type value is a custom type
 * @param {string} value - The type value to check
 * @returns {boolean} True if custom type
 */
export const isCustomType = (value) => {
  return _customTypes.some(type => type.value === value);
};

// Category definitions
export const CATEGORIES = [
  { name: TYPE_CATEGORY.CORE, description: 'Built-in rundown item types', icon: 'mdi-television-classic' },
  { name: TYPE_CATEGORY.CUSTOM, description: 'User-defined custom types', icon: 'mdi-shape-plus' }
];

/**
 * Generate color mappings for the theme system
 * @returns {Object} Type value -> color mappings
 */
export const generateColorMappings = () => {
  const mappings = {};
  getAllItemTypes().forEach(type => {
    mappings[type.value] = type.color;
  });
  return mappings;
};
