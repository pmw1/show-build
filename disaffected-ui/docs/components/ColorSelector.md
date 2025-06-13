# Color Selector Component Documentation

## Overview
The ColorSelector component provides a UI for selecting and previewing Vuetify theme colors, with separate sections for rundown items and interface elements.

## File Structure
```
disaffected-ui/
├── src/
│   ├── plugins/
│   │   └── vuetify.js       # Theme configuration
│   ├── utils/
│   │   └── themeColorMap.js # Color management utilities
│   └── components/
│       └── ColorSelector.vue # Main component
```

## Implementation Details

### Theme Configuration
Colors are defined in `vuetify.js` using Material Design color palette:
- Base colors
- Accent variations
- Light/Dark variations
- Grouped by color family

### Color Management
- Uses `themeColorMap.js` for centralized color management
- Persists selections in localStorage
- Provides default colors for initial state
- Immediate updates to color map on selection

### Component Features
1. **Dual Table Layout**
   - Rundown Items (Advert, CTA, Promo, etc.)
   - Interface Elements (Highlight, Dropline)

2. **Color Selection**
   - Grouped by color family
   - Shows color preview dot
   - Full-width color preview cell
   - Organized dropdown selection

3. **Persistence**
   - Automatic saving to localStorage
   - Confirmation dialog on save
   - Default color fallbacks

### CSS Implementation
- Full-width responsive tables
- Fixed column proportions (15/65/20)
- Edge-to-edge color previews
- Material Design-styled dropdowns

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

## Color Families Available
- Red (base, accent, dark, light)
- Purple (base, accent, dark, light)
- Blue (base, accent, dark, light)
- Light Green (base, accent, dark, light)
- Yellow (base, accent, dark, light)
- Blue Gray (base, accent, dark, light)

## Default Color Mappings
```javascript
const defaults = {
  Advert: 'blue-accent',
  CTA: 'red-accent',
  Promo: 'lightgreen-accent',
  Segment: 'purple-accent',
  Trans: 'yellow-accent',
  Highlight: 'yellow-accent',
  Dropline: 'bluegrey-accent'
}
```

## TODO and Improvement Areas

### Error Handling
- [ ] Add localStorage failure handling
- [ ] Implement color value validation
- [ ] Add try/catch blocks in critical sections
- [ ] Error state UI feedback

### Type Safety
- [ ] Add TypeScript definitions
- [ ] Implement prop validation
- [ ] Add color type validation
- [ ] Document expected prop types

### Performance Optimizations
- [ ] Add debouncing for color updates
- [ ] Implement batch localStorage saves
- [ ] Optimize color map access

### Documentation Needs
- [ ] Add JSDoc comments
- [ ] Document events and props
- [ ] Add usage examples
- [ ] Document color map integration

### Feature Additions
- [ ] Add color reset functionality
- [ ] Implement undo/redo
- [ ] Add color preview on hover
- [ ] Export/Import color configurations

### Testing
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Test localStorage fallbacks
- [ ] Test color validation
```