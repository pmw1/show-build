# TODO and Issues

## Current Status (July 8, 2025)
Following the completion of `copilot_instructions_3.markdown`, all critical issues from the urgent fixes have been addressed. The Disaffected Production Suite is now in a stable, production-ready state.

## Recently Completed - copilot_instructions_3.markdown (July 8, 2025)
- **Navigation drawer fix**: Confirmed working correctly - uses `:temporary="$route.name !== 'ContentEditor'"`.
- **Rundown item types standardization**: Fixed computed properties in `RundownManager.vue` to use only standard types (segment, ad, promo, cta, trans, unknown).
- **Unit test enhancement**: Improved `ContentEditor.spec.js` with drag-and-drop test and proper Vuetify setup.
- **RundownManager unit tests**: Created comprehensive `RundownManager.spec.js` with rendering, segment display, and count calculation tests.
- **ColorSelector debouncing**: Verified lodash debounce implementation in `saveColors` method.
- **Episode selection persistence**: Confirmed `EpisodeSelector.vue` uses sessionStorage for persistence.
- **Virtual scrolling**: Confirmed `RundownManager.vue` implements `<v-virtual-scroll>` for large rundowns.
- **Asset management completion**: `AssetsView.vue` has full CRUD functionality - file explorer, upload, preview, rename, delete, folder navigation.
- **Template management completion**: `TemplatesView.vue` has full CRUD functionality with proper API integration patterns.
- **Authentication refactoring**: Fully converted `App.vue` and `ProfileView.vue` to use `useAuth` composable exclusively, eliminating direct localStorage access.

## Previous Completions - copilot_instructions_2.markdown
- **Authentication refactoring**: `App.vue` and `ProfileView.vue` use `useAuth` composable exclusively.
- **Cue modal completion**: Implemented `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` with full form logic.
- **File cleanup**: Removed redundant markdown files as specified in instructions.
- **Accessibility improvements**: Added black border to `ColorSelector.vue` preview box for contrast.

## Current Issues (Minor)
- **Unit testing configuration**: Jest setup may need refinement for complex Vuetify 3 interactions.
- **ContentEditor.vue size**: Still large (2154 lines), though functionally complete.
- **Test coverage**: Could be expanded beyond current core component coverage.

## Technical Debt (Non-Critical)
- **Component size**: `ContentEditor.vue` and `RundownManager.vue` are large but functionally appropriate.
- **CSS organization**: Styling is functional but could be more centralized.
- **Error handling**: Generally consistent, some minor improvements possible.

## TODO (Lower Priority)
- **Cue modal enhancements**: Implement VO, NAT, PKG modal fixes per `copilot_instructions_4.md`.
- **E2E testing**: Implement Cypress or Playwright tests for critical user workflows.
- **Performance optimization**: Consider additional optimizations for very large rundowns (>500 items).
- **Documentation**: Add JSDoc comments to critical methods and components.
- **Accessibility audit**: Run Lighthouse accessibility checks on all views.
- **Code splitting**: Implement dynamic imports for better bundle size management.

## Feature Enhancements (Future)
- **Real-time collaboration**: WebSocket integration for multi-user editing.
- **Export functionality**: PDF/Word export for rundowns and scripts.
- **Template inheritance**: Advanced template system with inheritance and variables.
- **Asset versioning**: Version control for asset files.
- **Analytics**: Usage analytics and performance monitoring.
- **Advanced search**: Global search across rundowns, scripts, and assets.

*Last Updated: July 8, 2025 - Post copilot_instructions_3.markdown completion*