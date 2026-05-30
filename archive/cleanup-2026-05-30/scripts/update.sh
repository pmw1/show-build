#!/bin/bash

# update.sh
# Runs task-specific scripts to fix copilot_instructions_6.md tasks.
# Run from /mnt/process/show-build/.

# Check directory
if [[ "$(pwd)" != *"/mnt/process/show-build" ]]; then
    echo "ERROR: Run from /mnt/process/show-build/"
    exit 1
fi

# Create backup directory
BACKUP_DIR="backup_md_20250709"
mkdir -p "$BACKUP_DIR"

# Backup function
backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/$(basename "$file").$(date +%Y%m%d_%H%M%S)"
        echo "Backed up: $file"
    else
        echo "Warning: $file not found"
    fi
}

# Message to Copilot
echo "Copilot: Fixing tasks from copilot_instructions_6.md:"
echo "- Cue Modals: Missing VoModal.vue, NatModal.vue, PkgModal.vue."
echo "- Virtual Scrolling: No <v-virtual-scroll> in RundownManager.vue."
echo "- Asset/Template: Missing AssetsView.vue, TemplatesView.vue."
echo "- Modal Naming: Incorrect showAssetBrowserModal, showTemplateManagerModal in ContentEditor.vue."
echo "- Docs: Outdated 06_todo_and_issues.markdown, 03_features_and_integrations.markdown."
echo "- Excluded: Obsidian plugin (main.js) updates, as it is for reference only."

# Run task-specific scripts
for script in create_modals.sh update_rundown.sh create_views.sh update_naming.sh fix_modal_naming.sh update_docs.sh update_grok.sh; do
    if [ -f "$script" ]; then
        chmod +x "$script"
        ./"$script" || { echo "Error: $script failed"; exit 1; }
    else
        echo "Error: $script not found"
        exit 1
    fi
done

# New modal naming fix script
FIX_MODAL_NAMING="fix_modal_naming.sh"
backup_file "$FIX_MODAL_NAMING"
echo '#!/bin/bash
CONTENT_EDITOR="disaffected-ui/src/components/ContentEditor.vue"
BACKUP_DIR="backup_md_20250709"
backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/$(basename "$file").$(date +%Y%m%d_%H%M%S)"
        echo "Backed up: $file"
    fi
}
backup_file "$CONTENT_EDITOR"
sed -i "s/showAssetBrowserModal/showAssetModal/g" "$CONTENT_EDITOR"
sed -i "s/showTemplateManagerModal/showTemplateModal/g" "$CONTENT_EDITOR"
echo "Updated modal naming in: $CONTENT_EDITOR"' > "$FIX_MODAL_NAMING"
chmod +x "$FIX_MODAL_NAMING"
./"$FIX_MODAL_NAMING" || { echo "Error: $FIX_MODAL_NAMING failed"; exit 1; }

echo "Tasks complete. Validate with instructions:"
echo "- Run './grok.sh' and check review_files.txt for AssetsView.vue, TemplatesView.vue, VoModal.vue, NatModal.vue, PkgModal.vue, RundownManager.vue."
echo "- Run 'npm test' to verify unit tests."
echo "- Test modals at /content-editor/0228 (trigger VO, NAT, PKG, check script updates)."
echo "- Load /rundown/0228 with >100 items, verify scrolling in DevTools (Performance tab)."
echo "- Check API: curl -H \"Authorization: Bearer \$(localStorage.getItem('auth-token'))\" http://192.168.51.210:8888/health"