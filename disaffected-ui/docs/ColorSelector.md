# Color Selector Component Documentation

## Overview
The ColorSelector component provides a UI for selecting and previewing Vuetify theme colors. It uses Vuetify's built-in theme system and Material Design color palette.

## File Structure
```
disaffected-ui/
├── src/
│   ├── plugins/
│   │   └── vuetify.js       # Theme configuration
│   └── components/
│       └── ColorSelector.vue # Main component
```

## Theme Configuration
The colors are defined in `vuetify.js`:

```javascript
theme: {
  themes: {
    light: {
      colors: {
        primary: colors.blue.darken1,    // Used for Advert
        secondary: colors.blue.lighten4,  // Used for Trans
        accent: colors.amber.accent4,     // Used for CTA
        success: colors.green.darken1,    // Used for Promo
        info: colors.blue.lighten3,       // Used for Segment
        highlight: colors.yellow.accent4,  // Used for Highlight
        dropline: colors.blue.lighten5    // Used for Dropline
      }
    }
  }
}
```

## Component Features

### 1. Data Structure
- `types`: Array of rundown item types
- `typeColors`: Object mapping types to their selected colors
- `colorOptions`: Array of available colors with labels and values

### 2. Local Storage
Colors persist across sessions using localStorage:
```javascript
// Save color
localStorage.setItem(`color_${type}`, color)

// Retrieve color
localStorage.getItem(`color_${type}`)
```

### 3. CSS Implementation
Key styling features:

#### Table Layout
```css
table {
  width: 100% !important;
  border-collapse: collapse;
  table-layout: fixed;
}
```

#### Column Distribution
```css
td:first-child  { width: 15%; }  /* Type column */
td:nth-child(2) { width: 65%; }  /* Color selector */
td:last-child   { width: 20%; }  /* Preview */
```

#### Color Preview Implementation
The full-cell color preview uses absolute positioning:
```css
td:last-child {
  padding: 0;
  height: 100%;
  position: relative;
}

.preview-box {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
```

#### Color Dots
```css
.color-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1px solid #888;
}
```

## Usage Example
```vue
<template>
  <ColorSelector />
</template>

<script>
import ColorSelector from '@/components/ColorSelector.vue'

export default {
  components: {
    ColorSelector
  }
}
</script>
```

## Default Color Mappings
```javascript
const defaults = {
  Advert: 'primary',     // Blue Darken-1
  CTA: 'accent',         // Amber Accent-4
  Promo: 'success',      // Green Darken-1
  Segment: 'info',       // Blue Lighten-3
  Trans: 'secondary',    // Blue Lighten-4
  Highlight: 'highlight' // Yellow Accent-4
  Dropline: 'dropline'   // Blue Lighten-5
}
```

## Key Design Decisions
1. Uses Vuetify's semantic color system instead of direct color classes
2. Full-width table layout with fixed column proportions
3. Edge-to-edge color previews using absolute positioning
4. Persistent storage using localStorage
5. Dropdown selection with color dot previews

## Dependencies
- Vuetify 3.x
- Vue 3.x
- Local Storage API

## Browser Support
- All modern browsers
- Requires localStorage support
- Requires CSS position: absolute support
```// filepath: w:\disaffected-ui\docs\ColorSelector.md
# Color Selector Component Documentation

## Overview
The ColorSelector component provides a UI for selecting and previewing Vuetify theme colors. It uses Vuetify's built-in theme system and Material Design color palette.

## File Structure
```
disaffected-ui/
├── src/
│   ├── plugins/
│   │   └── vuetify.js       # Theme configuration
│   └── components/
│       └── ColorSelector.vue # Main component
```

## Theme Configuration
The colors are defined in `vuetify.js`:

```javascript
theme: {
  themes: {
    light: {
      colors: {
        primary: colors.blue.darken1,    // Used for Advert
        secondary: colors.blue.lighten4,  // Used for Trans
        accent: colors.amber.accent4,     // Used for CTA
        success: colors.green.darken1,    // Used for Promo
        info: colors.blue.lighten3,       // Used for Segment
        highlight: colors.yellow.accent4,  // Used for Highlight
        dropline: colors.blue.lighten5    // Used for Dropline
      }
    }
  }
}
```

## Component Features

### 1. Data Structure
- `types`: Array of rundown item types
- `typeColors`: Object mapping types to their selected colors
- `colorOptions`: Array of available colors with labels and values

### 2. Local Storage
Colors persist across sessions using localStorage:
```javascript
// Save color
localStorage.setItem(`color_${type}`, color)

// Retrieve color
localStorage.getItem(`color_${type}`)
```

### 3. CSS Implementation
Key styling features:

#### Table Layout
```css
table {
  width: 100% !important;
  border-collapse: collapse;
  table-layout: fixed;
}
```

#### Column Distribution
```css
td:first-child  { width: 15%; }  /* Type column */
td:nth-child(2) { width: 65%; }  /* Color selector */
td:last-child   { width: 20%; }  /* Preview */
```

#### Color Preview Implementation
The full-cell color preview uses absolute positioning:
```css
td:last-child {
  padding: 0;
  height: 100%;
  position: relative;
}

.preview-box {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
```

#### Color Dots
```css
.color-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1px solid #888;
}
```

## Usage Example
```vue
<template>
  <ColorSelector />
</template>

<script>
import ColorSelector from '@/components/ColorSelector.vue'

export default {
  components: {
    ColorSelector
  }
}
</script>
```

## Default Color Mappings
```javascript
const defaults = {
  Advert: 'primary',     // Blue Darken-1
  CTA: 'accent',         // Amber Accent-4
  Promo: 'success',      // Green Darken-1
  Segment: 'info',       // Blue Lighten-3
  Trans: 'secondary',    // Blue Lighten-4
  Highlight: 'highlight' // Yellow Accent-4
  Dropline: 'dropline'   // Blue Lighten-5
}
```

## Key Design Decisions
1. Uses Vuetify's semantic color system instead of direct color classes
2. Full-width table layout with fixed column proportions
3. Edge-to-edge color previews using absolute positioning
4. Persistent storage using localStorage
5. Dropdown selection with color dot previews

## Dependencies
- Vuetify 3.x
- Vue 3.x
- Local Storage API

## Browser Support
- All modern browsers
- Requires localStorage support
- Requires CSS position: absolute support