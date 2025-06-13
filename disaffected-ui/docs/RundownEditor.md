# Rundown Editor Documentation

## Current Status & Critical Issues

### 1. Data Management Issues
- Save & Commit functionality not working correctly
- Episode selector implementation incomplete
- Hard-coded to episode 225
- No error handling for missing episodes
- No validation of segment order
- Duration calculations not implemented

### 2. Architectural Concerns
- Currently positioned as main page when it should be a component
- Needs to be integrated into larger application structure:
  ```
  DisaffectedUI
  ├── Layout/
  │   ├── Navigation
  │   ├── Toolbar
  │   └── StatusBar
  ├── Views/
  │   ├── Dashboard
  │   ├── RundownManager     <-- Current component should live here
  │   ├── AssetLibrary
  │   └── Settings
  └── Components/
      ├── RundownEditor     <-- Should be renamed and moved here
      ├── SegmentEditor
      └── MediaPreview
  ```

## Required Features

### High Priority
1. **Data Management**
   - Implement proper episode loading
   - Add episode list fetching from API
   - Fix Save & Commit functionality
   - Add validation before save
   - Implement proper error handling

2. **Navigation & Layout**
   - Create main application layout
   - Add navigation structure
   - Move RundownEditor to proper component location
   - Implement proper routing
   - Add breadcrumb navigation

3. **Episode Management**
   - Add episode creation
   - Implement episode duplication
   - Add episode deletion with confirmation
   - Add episode metadata editing

### Medium Priority
1. **User Interface**
   - Add loading states
   - Improve error messages
   - Add success notifications
   - Implement proper form validation
   - Add keyboard shortcuts

2. **Data Display**
   - Show total duration
   - Add segment validation indicators
   - Show segment availability status
   - Add change indicators
   - Implement search/filter

### Low Priority
1. **Performance**
   - Add pagination for large rundowns
   - Implement virtual scrolling
   - Optimize drag and drop
   - Cache episode data

## Integration Requirements

### Parent Application
1. **Layout Integration**
   ```vue
   <template>
     <v-app>
       <v-navigation-drawer>
         <!-- App navigation -->
       </v-navigation-drawer>
       
       <v-main>
         <v-container>
           <router-view></router-view>
         </v-container>
       </v-main>
       
       <v-footer>
         <!-- Status information -->
       </v-footer>
     </v-app>
   </template>
   ```

2. **Router Configuration**
   ```javascript
   const routes = [
     {
       path: '/rundown/:episodeId?',
       component: RundownView,
       children: [
         {
           path: 'edit',
           component: RundownEditor
         }
       ]
     }
   ]
   ```

3. **State Management**
   - Add Vuex/Pinia store
   - Implement episode state
   - Add user preferences
   - Handle global notifications

### API Integration
1. **Required Endpoints**
   - GET /episodes - List all episodes
   - GET /episode/:id - Get episode details
   - POST /episode/:id/save - Save changes
   - GET /episode/:id/segments - Get segment list
   - POST /episode/:id/reorder - Save segment order

2. **Data Validation**
   - Add request/response validation
   - Implement proper error handling
   - Add retry logic
   - Handle network issues

## Testing Requirements

### Unit Tests
- Test segment ordering
- Validate drag and drop
- Test episode loading
- Test save functionality

### Integration Tests
- Test API integration
- Test navigation flow
- Test error handling
- Test state management

### E2E Tests
- Test full rundown workflow
- Test episode management
- Test error scenarios
- Test performance

## Documentation Needs

### User Documentation
- Add usage guidelines
- Document keyboard shortcuts
- Add troubleshooting guide
- Include best practices

### Developer Documentation
- Add component API documentation
- Document state management
- Add setup instructions
- Include contribution guidelines

## Future Considerations

### Scalability
- Handle large episode counts
- Manage multiple simultaneous users
- Handle concurrent edits
- Implement change tracking

### Features
- Add multi-episode view
- Implement templates
- Add batch operations
- Include search functionality

### Integration
- Add webhook support
- Implement external API
- Add export options
- Include import functionality