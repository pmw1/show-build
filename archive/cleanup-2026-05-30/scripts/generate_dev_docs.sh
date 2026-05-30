#!/bin/bash
#
# Name: generate_dev_docs.sh
#
# Description:
# This script creates themed development documentation chunks from the docs/ directory.
# Unlike the full rehydrate script, this focuses on creating tool-agnostic development
# documentation organized by topic for easier consumption by developers and LLMs.
#

# --- Configuration ---
SRC_DIR="docs"
OUTPUT_DIR="docs"

# --- File Groups for Each Development Chunk ---

# Architecture & Setup chunk
ARCHITECTURE_FILES=(
    "01_architecture.markdown"
    "02_setup_and_deployment.markdown"
    "PROJECT_ARCHITECTURE_REPORT.md"
    "00_rehydration_main.markdown"
)

# Features & Components chunk  
FEATURES_FILES=(
    "03_features_and_integrations.markdown"
    "MODAL_USAGE.md"
    "ColorSelector.md"
)

# Development Workflow chunk
WORKFLOW_FILES=(
    "04_migration_and_workflow.markdown"
    "05_style_guide.markdown"
    "STYLE_GUIDE.md"
)

# Authentication & Security chunk
AUTH_FILES=(
    "AUTHENTICATION_GUIDE.md"
)

# Current Issues & Tasks chunk
ISSUES_FILES=(
    "06_todo_and_issues.markdown"
    "Stuff to do.md"
    "copilot_instructions_7.markdown"
)

# API & Integration chunk (will be created from extracted content)
API_FILES=(
    "19_documentation_updates.markdown"
    "20_changelog.markdown"
)

# --- Helper Functions ---
write_chunk_header() {
    local output_file="$1"
    local chunk_title="$2"
    local chunk_description="$3"
    
    cat > "$output_file" << EOF
# $chunk_title

$chunk_description

---

EOF
}

process_file_group() {
    local output_file="$1"
    local chunk_title="$2"
    local chunk_description="$3"
    shift 3
    local files=("$@")
    
    echo "Creating $output_file..."
    write_chunk_header "$output_file" "$chunk_title" "$chunk_description"
    
    for file in "${files[@]}"; do
        local file_path="$SRC_DIR/$file"
        if [ -f "$file_path" ]; then
            echo "  -> Adding $file"
            echo "## From: $file" >> "$output_file"
            echo "" >> "$output_file"
            
            # Special handling for copilot instructions - extract technical content only
            if [[ "$file" == copilot_instructions_* ]]; then
                # Extract technical sections, skip Copilot-specific instructions
                awk '
                    /^### [0-9]+\. / { in_technical = 1; print; next }
                    /^## / && !/Copilot/ { in_technical = 1; print; next }
                    /Copilot/ && /^#/ { in_technical = 0; next }
                    in_technical { print }
                ' "$file_path" >> "$output_file"
            else
                cat "$file_path" >> "$output_file"
            fi
            
            echo "" >> "$output_file"
            echo "---" >> "$output_file"
            echo "" >> "$output_file"
        else
            echo "  -> Warning: $file not found, skipping"
        fi
    done
}

# --- Main Execution ---

echo "Generating development documentation chunks..."
echo ""

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Generate each themed chunk
process_file_group \
    "$OUTPUT_DIR/dev_architecture.md" \
    "Architecture & Setup" \
    "Core technical architecture, deployment configuration, and system setup documentation." \
    "${ARCHITECTURE_FILES[@]}"

process_file_group \
    "$OUTPUT_DIR/dev_features.md" \
    "Features & Components" \
    "Component patterns, modal system, cue types, and feature implementations." \
    "${FEATURES_FILES[@]}"

process_file_group \
    "$OUTPUT_DIR/dev_workflow.md" \
    "Development Workflow" \
    "Development practices, coding standards, migration strategies, and style guides." \
    "${WORKFLOW_FILES[@]}"

process_file_group \
    "$OUTPUT_DIR/dev_auth.md" \
    "Authentication & Security" \
    "Authentication patterns, JWT/API key implementation, and security guidelines." \
    "${AUTH_FILES[@]}"

process_file_group \
    "$OUTPUT_DIR/dev_issues.md" \
    "Current Issues & Tasks" \
    "Known issues, pending development tasks, and implementation details for outstanding work." \
    "${ISSUES_FILES[@]}"

process_file_group \
    "$OUTPUT_DIR/dev_api.md" \
    "API & Integration" \
    "API documentation, integration patterns, and change history." \
    "${API_FILES[@]}"

echo ""
echo "Development documentation chunks created successfully!"
echo "Output files:"
echo "  - docs/dev_architecture.md"
echo "  - docs/dev_features.md" 
echo "  - docs/dev_workflow.md"
echo "  - docs/dev_auth.md"
echo "  - docs/dev_issues.md"
echo "  - docs/dev_api.md"
echo ""
echo "These files provide focused, tool-agnostic development context for specific areas of work."