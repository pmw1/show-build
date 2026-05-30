#!/bin/bash

# grok.sh
# Concatenates files for Disaffected Production Suite review into review_files.txt.
# Run from project root (/mnt/process/show-build/).

OUTPUT_FILE="review_files.txt"

FILES_TO_INCLUDE=(
    "docs/00_rehydration_main.markdown"
    "docs/01_architecture.markdown"
    "docs/02_setup_and_deployment.markdown"
    "docs/03_features_and_integrations.markdown"
    "docs/04_migration_and_workflow.markdown"
    "docs/05_style_guide.markdown"
    "docs/06_todo_and_issues.markdown"
    "docs/MODAL_USAGE.md"
    "disaffected-ui/vue.config.js"
    "disaffected-ui/package.json"
    "disaffected-ui/src/main.js"
    "disaffected-ui/src/components/ContentEditor.vue"
    "disaffected-ui/src/components/RundownManager.vue"
    "disaffected-ui/src/components/ColorSelector.vue"
    "disaffected-ui/src/components/EditorPanel.vue"
    "disaffected-ui/src/components/RundownPanel.vue"
    "disaffected-ui/src/components/EpisodeSelector.vue"
    "disaffected-ui/src/composables/useAuth.js"
    "disaffected-ui/src/stores/auth.js"
    "disaffected-ui/src/utils/themeColorMap.js"
    "disaffected-ui/src/views/AssetsView.vue"
    "disaffected-ui/src/views/TemplatesView.vue"
    "disaffected-ui/src/views/DashboardView.vue"
    "disaffected-ui/src/App.vue"
    "disaffected-ui/src/views/ProfileView.vue"
    "disaffected-ui/src/components/modals/FsqModal.vue"
    "disaffected-ui/src/components/modals/SotModal.vue"
    "disaffected-ui/src/components/modals/VoModal.vue"
    "disaffected-ui/src/components/modals/NatModal.vue"
    "disaffected-ui/src/components/modals/PkgModal.vue"
    "disaffected-ui/src/views/SettingsView.vue"
    "disaffected-ui/src/plugins/vuetify.js"
    "disaffected-ui/src/router/index.js"
)

> "$OUTPUT_FILE"

echo "Current directory: $(pwd)" >> "$OUTPUT_FILE"
if [[ "$(pwd)" != *"/mnt/process/show-build" ]]; then
    echo "WARNING: Run from /mnt/process/show-build/" >> "$OUTPUT_FILE"
fi

for dir in "disaffected-ui/src" "disaffected-ui/docs" "disaffected-ui/tests" "docs"; do
    if [ -d "$dir" ]; then
        echo "Found directory: $dir" >> "$OUTPUT_FILE"
    else
        echo "Directory not found: $dir" >> "$OUTPUT_FILE"
    fi
done

append_file_content() {
    local file="$1"
    if [ -f "$file" ]; then
        echo "===== $file =====" >> "$OUTPUT_FILE"
        cat "$file" >> "$OUTPUT_FILE"
        echo -e "\n===== END $file =====\n" >> "$OUTPUT_FILE"
        echo "Included: $file"
    else
        echo "Warning: $file not found"
        echo "===== $file =====\nNOT FOUND\n===== END $file =====\n" >> "$OUTPUT_FILE"
    fi
}

for file in "${FILES_TO_INCLUDE[@]}"; do
    append_file_content "$file"
done

if [ -f "$OUTPUT_FILE" ]; then
    echo "Created: $OUTPUT_FILE"
else
    echo "Failed to create: $OUTPUT_FILE"
fi