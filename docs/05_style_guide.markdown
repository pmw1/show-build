# Style Guide

## Overview
This document defines the UI/UX guidelines and color system for the Disaffected Production Suite, ensuring consistent styling across components. The color system is centralized in `themeColorMap.js` and uses Vuetify theme colors, with `COLOR_SYSTEM_GUIDE.md` deprecated.

## Color System
- **Configuration**: Defined in `/mnt/process/show-build/disaffected-ui/src/plugins/vuetify.js`
- **Mappings**:
  - `Advert`: `primary` (#1976D2)
  - `CTA`: `accent` (#82B1FF)
  - `Promo`: `success` (#4CAF50)
  - `Segment`: `info` (#2196F3)
  - `Trans`: `secondary` (#424242)
  - `Highlight`: `highlight` (#FFD740)
  - `Dropline`: `dropline` (#BBDEFB)
  - `draft`: `grey-dark` (#616161)
  - `approved`: `green-accent` (#69F0AE)
  - `production`: `blue-accent` (#448AFF)
  - `completed`: `yellow-accent` (#FFD740)
- **Implementation Notes**:
  - Colors are applied via `themeColorMap.js` using `resolveVuetifyColor`.
  - `ColorSelector.vue` persists selections in `localStorage`, but synchronization with `themeColorMap.js` is pending.
  - Potential issues: `null` color returns, `baseColors` undefined errors in `ColorSelector.vue`.
- **Recommendations**:
  - Centralize color application through `themeColorMap.js`.
  - Add fallback for `null` colors in `resolveVuetifyColor` (e.g., `#000000`).
  - Initialize `baseColors` in `ColorSelector.vue` to prevent errors.
  - Implement WCAG 2.1 AA contrast checks.
  - Synchronize `localStorage` updates.
- **Deprecation Notice**: `COLOR_SYSTEM_GUIDE.md` is deprecated; its Material Design color mappings (e.g., `cyan`, `yellow-accent`) may exist in legacy code but should be replaced with Vuetify theme colors.

## UI Guidelines
- **Rundown List Items**:
  - **Selected**: Background `primary` (#1976D2), text `#FFFFFF`, 4px left border `accent` (#82B1FF)
  - **Hover**: Background `#C8E6C9`, text black
  - **Ghost (drag)**: Opacity 0.5, background `#c8ebfb`
- **Layout**:
  - Rundown panel: 40% width
  - Editor panel: Flex, fills remaining space
  - Toolbar: Flat with divider
- **Typography**:
  - Index: Font weight 500, multiples of 10 (10, 20, 30, ...)
  - Item type: 11px, bold, uppercase
  - Item slug: 14px, normal
  - Duration: 14px, bold, right-aligned

*Last Updated: July 8, 2025*