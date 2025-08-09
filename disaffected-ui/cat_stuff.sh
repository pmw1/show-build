#!/bin/bash

# This script concatenates specific files needed to review fixes for the Disaffected Production Suite into a single text file.
# Run from the project root directory (/mnt/process/show-build/disaffected-ui/).

# Output file
OUTPUT_FILE="review_files.txt"

# List of files to include
FILES_TO_INCLUDE=(
    "vue.config.js"
    "package.json"
    "src/main.js"
    "src/components/ContentEditor.vue"
    "src/components/RundownManager.vue"
    "src/components/ColorSelector.vue"
    "src/components/EditorPanel.vue"
    "src/components/RundownPanel.vue"
    "src/components/EpisodeSelector.vue"
    "src/composables/useAuth.js"
    "src/stores/auth.js"
    "src/utils/themeColorMap.js"
    "docs/todo_and_issues.md"
    "src/components/TemplatesView.vue"
    "src/components/AssetsView.vue"
    "src/components/DashboardView.vue"
    "src/components/App.vue"
    "src/components/ProfileView.vue"
    "src/components/modals/FsqModal.vue"
    "src/components/modals/SotModal.vue"
    "src/components/modals/VoModal.vue"
    "src/components/modals/NatModal.vue"
    "src/components/modals/PkgModal.vue"
    "tests/unit/ContentEditor.spec.js"
)

# Clear or create the output file
> "$OUTPUT_FILE"

# Function to append file content with a header
append_file_content() {
    local file="$1"
    if [ -f "$file" ]; then
        echo "===== $file =====" >> "$OUTPUT_FILE"
        cat "$file" >> "$OUTPUT_FILE"
        echo -e "\n===== END $file =====\n" >> "$OUTPUT_FILE"
        echo "Included: $file"
    else
        echo "Warning: $file not found, skipping."
        echo "===== $file =====\nNOT FOUND\n===== END $file =====\n" >> "$OUTPUT_FILE"
    fi
}

# Loop through files and append their contents
for file in "${FILES_TO_INCLUDE[@]}"; do
    append_file_content "$file"
done

# Check if output file was created
if [ -f "$OUTPUT_FILE" ]; then
    echo "Text file created successfully: $OUTPUT_FILE"
else
    echo "Failed to create text file."
fi
