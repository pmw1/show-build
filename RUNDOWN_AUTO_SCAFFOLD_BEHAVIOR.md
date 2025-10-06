# Rundown Auto-Scaffolding Behavior

## Observed Issue

**Date**: 2025-10-04
**Status**: Deferred - Not critical for current workflow

### Description

When deleting all rundown items from an episode and then creating a new Cold Open, the system automatically creates additional items:
- Promo
- Tease
- CTA

These items appear to be created automatically alongside the Cold Open, even though only a single Cold Open was requested through the UI.

### Steps to Reproduce

1. Open an episode with existing rundown items
2. Delete all rundown items individually (or assume they're all deleted)
3. Create a new Cold Open item via the New Item modal
4. **Expected**: Only the Cold Open is created
5. **Actual**: Cold Open + Promo + Tease + CTA are all created

### Questions to Answer (When Debugging)

1. **Timing**: Do these items appear immediately after Cold Open creation, or after page reload?
2. **Position**: Where are promo/tease/cta positioned relative to Cold Open?
3. **Content**: Are these generic placeholders or do they have specific titles/content?
4. **Source**: Where is this scaffolding logic?
   - Not in `NewItemModal.vue` (only emits single item)
   - Not in `ContentEditor.createNewItem()` (creates single item via API)
   - Not in backend `/rundown/item` POST endpoint (creates single DB record)
   - Possibly in episode scaffolding service?

### Investigation Starting Points

- `/app/services/episode_scaffold.py` - Episode scaffolding logic
- `/app/episode_scaffold_router.py` - Scaffold API endpoints
- `/app/setup_episode_scaffolding.py` - Initial setup script
- Database triggers or cascading inserts in `RundownItem` model
- Frontend rundown reload logic after item creation
- Check if "delete" actually deletes or just marks items as deleted

### Potential Causes

1. **Template-based scaffolding**: Creating a Cold Open triggers a template that includes default show structure
2. **Database restoration**: Deleted items aren't actually deleted, just hidden, and reappear on reload
3. **Episode blueprint**: Episodes have a default structure that auto-populates when items are created
4. **Client-side caching**: Old items cached and re-inserted during rundown reload

### Priority

**Low** - Not blocking current keyboard navigation work. Can investigate later when refactoring rundown item management.

### Related Files

- `disaffected-ui/src/components/content-editor/modals/NewItemModal.vue` (item creation UI)
- `disaffected-ui/src/components/ContentEditor.vue:2906` (createNewItem method)
- `app/episodes_router.py:1535` (create_rundown_item endpoint)
- `app/services/episode_scaffold.py`
- `app/episode_scaffold_router.py`
