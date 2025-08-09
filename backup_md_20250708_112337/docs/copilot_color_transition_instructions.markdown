# Instructions for Copilot: Transitioning the Disaffected Production Suite Color System

## Overview
The Disaffected Production Suite uses a color system to style rundown item types (`ad`, `cta`, `promo`, `segment`, `trans`) and UI elements (`selection`, `hover`, `highlight`, `dropline`, `draft`, `approved`, `production`, `completed`) in the frontend (`/mnt/process/show-build/disaffected-ui/`). The current implementation is inconsistent, causing runtime errors, accessibility issues, and maintenance challenges. This document provides Copilot with detailed instructions to understand the current state, identify problems, and transition to a unified color system that aligns with Vue 3/Vuetify best practices.

## Current State
The color system is managed across multiple files, leading to discrepancies and errors:

1. **Files Involved**:
   - **`/mnt/process/show-build/disaffected-ui/src/plugins/vuetify.js`**: Defines the Vuetify theme with a comprehensive Material Design color palette (e.g., `red-base`, `blue-accent`) and standard theme colors (`primary: #1976D2`, `accent: #82B1FF`, etc.).
   - **`/mnt/process/show-build/disaffected-ui/src/utils/themeColorMap.js`**: Centralizes color mappings for rundown item types and UI elements, with a `resolveVuetifyColor` function to convert color names to hex values. Uses static `defaultColors` and ignores `localStorage`.
   - **`/mnt/process/show-build/disaffected-ui/src/components/ColorSelector.vue`**: UI component for selecting colors, persisting selections in `localStorage` using theme colors (e.g., `primary`, `accent`).
   - **Documentation**:
     - `ColorSelector.md`: Specifies color mappings using Vuetify theme colors (e.g., `Advert: primary`, `CTA: accent`).
     - `COLOR_SYSTEM_GUIDE.md`: Deprecated; uses Material Design colors (e.g., `advert: cyan`, `trans: yellow-accent`), causing confusion.

2. **Color Mappings**:
   - **ColorSelector.md**:
     ```javascript
     const defaults = {
       Advert: 'primary',     // #1976D2 (blue-dark)
       CTA: 'accent',         // #82B1FF (light blue)
       Promo: 'success',      // #4CAF50 (green-dark)
       Segment: 'info',       // #2196F3 (blue-base)
       Trans: 'secondary',    // #424242 (grey-dark)
       Highlight: 'highlight', // #FFD740 (yellow-accent)
       Dropline: 'dropline',  // #BBDEFB (blue-light)
     }
     ```
   - **COLOR_SYSTEM_GUIDE.md** (Deprecated):
     ```javascript
     const defaultColors = {
       segment: 'light-blue',     // #03A9F4
       advert: 'cyan',            // #00BCD4
       promo: 'cyan lighten-4',   // #B2EBF2
       cta: 'cyan lighten-3',     // #4DD0E1
       trans: 'yellow-accent',    // #FFD740
       selection: 'orange-accent', // #FF9800
       hover: 'blue-light',       // #BBDEFB
       draglight: 'cyan-light',   // #B2EBF2
       highlight: 'yellow-light', // #FFF9C4
       dropline: 'green-accent',  // #69F0AE
     }
     ```

3. **Problems**:
   - **Inconsistent Mappings**: `ColorSelector.md` uses Vuetify theme colors (e.g., `primary`), while `COLOR_SYSTEM_GUIDE.md` uses Material Design colors (e.g., `cyan`), causing potential mismatches in components expecting theme colors.
   - **Runtime Errors**:
     - `resolveVuetifyColor` in `themeColorMap.js` may return `null` if `vuetifyInstance` is unavailable, leading to unstyled UI elements (e.g., `[resolveVuetifyColor] warnings`).
     - `ColorSelector.vue` has a runtime error: `[ColorSelector] baseColors is not an array: undefined`, indicating uninitialized `baseColors`.
   - **Local Storage Inconsistency**: `ColorSelector.vue` persists selections in `localStorage`, but `themeColorMap.js` uses static `defaultColors`, ignoring `localStorage` changes.
   - **Accessibility**: Light colors (e.g., `yellow-light: #FFF9C4`) may fail WCAG 2.1 AA contrast requirements, especially for text or small UI elements (e.g., `color-dot`).
   - **Performance**: Frequent `localStorage` writes in `ColorSelector.vue` without debouncing may impact performance for large rundowns.
   - **Documentation**: `COLOR_SYSTEM_GUIDE.md` is outdated and conflicts with `ColorSelector.md`, confusing developers.

## Desired State
- **Unified Color System**:
  - Use Vuetify theme colors (`primary`, `accent`, `success`, etc.) as defined in `vuetify.js`.
  - Centralize color management in `themeColorMap.js` for all components.
  - Synchronize `localStorage` updates between `ColorSelector.vue` and `themeColorMap.js`.
- **Best Practices** (Vue 3/Vuetify):
  - Leverage Vuetify’s theme system for dynamic color application.
  - Use CSS custom properties for theme consistency.
  - Ensure WCAG 2.1 AA compliance for accessibility.
  - Optimize performance with debounced `localStorage` writes.
- **Project Needs**:
  - Consistent styling for rundown item types (`ad`, `cta`, `promo`, `segment`, `trans`) and UI elements (`selection`, `hover`, `highlight`, `dropline`, `draft`, `approved`, `production`, `completed`).
  - Reliable color rendering in `ContentEditor.vue` and `RundownManager.vue`.
  - User-configurable colors via `ColorSelector.vue`.

## Step-by-Step Transition Plan
1. **Update `themeColorMap.js`**:
   - Replace `defaultColors` with `ColorSelector.md` mappings:
     ```javascript
     const defaultColors = {
       Advert: 'primary',     // #1976D2
       CTA: 'accent',         // #82B1FF
       Promo: 'success',      // #4CAF50
       Segment: 'info',       // #2196F3
       Trans: 'secondary',    // #424242
       Highlight: 'highlight', // #FFD740
       Dropline: 'dropline',  // #BBDEFB
       draft: 'grey-dark',    // #616161
       approved: 'green-accent', // #69F0AE
       production: 'blue-accent', // #448AFF
       completed: 'yellow-accent' // #FFD740
     };
     ```
   - Update `resolveVuetifyColor` to prevent `null` returns and add WCAG contrast checks:
     ```javascript
     const getContrastRatio = (color1, color2) => {
       const luminance = (hex) => {
         const rgb = parseInt(hex.replace('#', ''), 16);
         const r = (rgb >> 16) & 0xff;
         const g = (rgb >> 8) & 0xff;
         const b = rgb & 0xff;
         return 0.2126 * (r / 255) + 0.7152 * (g / 255) + 0.0722 * (b / 255);
       };
       const lum1 = luminance(color1);
       const lum2 = luminance(color2);
       return (Math.max(lum1, lum2) + 0.05) / (Math.min(lum1, lum2) + 0.05);
     };
     export const resolveVuetifyColor = (colorName, vuetifyInstance, textColor = '#FFFFFF') => {
       if (!colorName) return '#000000';
       if (vuetifyInstance && vuetifyInstance.theme) {
         const theme = vuetifyInstance.theme.themes[vuetifyInstance.theme.dark ? 'dark' : 'light'].colors;
         if (theme && theme[colorName]) {
           const color = theme[colorName];
           if (getContrastRatio(color, textColor) < 4.5) {
             console.warn(`Low contrast for ${colorName}: ${color}`);
             return '#000000';
           }
           return color;
         }
       }
       const fallbackColors = {
         primary: '#1976D2',
         secondary: '#424242',
         accent: '#82B1FF',
         error: '#FF5252',
         info: '#2196F3',
         success: '#4CAF50',
         warning: '#FB8C00',
         highlight: '#FFD740',
         dropline: '#BBDEFB',
         'grey-dark': '#616161',
         'green-accent': '#69F0AE',
         'blue-accent': '#448AFF',
         'yellow