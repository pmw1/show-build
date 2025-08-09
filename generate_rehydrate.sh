#!/bin/bash
#
# Name: generate_rehydrate.sh
#
# Description:
# This script concatenates text files from a source directory into a single
# output file or into multiple, size-limited chunks for LLM context windows.
#
# It automatically sorts files alphabetically, with special handling for
# 'copilot_instructions_*' files, which are grouped and sorted numerically at the end.
# It also has special handling for '20_changelog.markdown' to only include recent entries.
#

# --- Configuration ---
SRC_DIR="docs"
OUTPUT_FILE="docs/rehydrate.md"
FILE_PATTERNS=(-name "*.md" -o -name "*.markdown" -o -name "*.txt")
SPECIAL_PREFIX="copilot_instructions_"
CHANGELOG_FILE="20_changelog.markdown"

# --- Instructions for Changelog ---
CHANGELOG_INSTRUCTIONS="---
**Instructions for LLM Submissions:**

LLMs that have submitted an \`update.py\` script must log their changes in this file (\`docs/20_changelog.markdown\`).
LLMs including Grok, Gemini, Claude, and ChatGPT can submit \`update.py\` files that will be run from the project root, so long as the details of that submission are logged here.

**Log Entry Format:**
- **Date/Time:** The timestamp of when the update script was run.
- **LLM:** The name of the model submitting the update (e.g., Gemini).
- **Description:** A bulleted list explaining:
  - What the update does.
  - The reason for each operation.
  - The final status (success or failure).

**Important:** All log entries must be performed by the \`update.py\` script itself. Do not manually edit this file.
---"

# --- Script Flags & Parameters ---
CHUNK_MODE=false
DEBUG_MODE=false
CHUNK_SIZE_KB=4096 # Default chunk size in Kilobytes (e.g., 4096KB = 4MB)

# --- Help Function ---
show_help() {
  echo "Usage: $(basename "$0") [options]"
  echo ""
  echo "Concatenates text files from './${SRC_DIR}/' into a single file or multiple chunks."
  echo ""
  echo "Options:"
  echo "  --chunk                Enable chunking mode. Splits output into multiple files."
  echo "  --chunk-size <KB>      Set the maximum size for each chunk in Kilobytes (KB)."
  echo "                         Default is ${CHUNK_SIZE_KB}KB. To test, try a small value like 60."
  echo "  --debug                Enable verbose debugging output to diagnose issues."
  echo "  --help                 Display this help message and exit."
  echo ""
  echo "Details:"
  echo "  - Processes .md, .markdown, and .txt files, ignoring subdirectories."
  echo "  - Files named '${SPECIAL_PREFIX}*' are grouped together and sorted numerically at the end."
  echo "  - For '${CHANGELOG_FILE}', instructions are added and only the last 75 lines are included."
  echo "  - A 'tree -L 3 -I \"node_modules\"' command output is appended to the end."
  echo ""
  echo "Requirements:"
  echo "  - Must be run from the directory containing the '${SRC_DIR}/' folder."
  echo "  - The 'tree', 'wc', and 'tail' commands must be installed."
}

# --- Argument Parsing ---
while [[ $# -gt 0 ]]; do
  case $1 in
    --chunk)
      CHUNK_MODE=true
      shift # past argument
      ;;
    --chunk-size)
      if [[ -n "$2" && "$2" != --* ]]; then
        CHUNK_SIZE_KB="$2"
        shift 2 # past argument and value
      else
        echo "Error: --chunk-size requires a numeric argument." >&2
        exit 1
      fi
      ;;
    --debug)
      DEBUG_MODE=true
      shift # past argument
      ;;
    --help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      show_help
      exit 1
      ;;
  esac
done

# --- Prerequisite Validation ---
if [ ! -d "$SRC_DIR" ]; then
  echo "Error: Source directory './${SRC_DIR}/' not found." >&2
  exit 1
fi
if ! command -v tree &> /dev/null; then
  echo "Error: 'tree' command not found. Please install it to continue." >&2
  exit 1
fi
if ! command -v wc &> /dev/null; then
  echo "Error: 'wc' command not found. It is required for this script." >&2
  exit 1
fi
if ! command -v tail &> /dev/null; then
    echo "Error: 'tail' command not found. It is required for this script." >&2
    exit 1
fi

# --- File Discovery and Sorting ---

# Find all standard files (those NOT matching the special prefix) and sort them alphabetically.
readarray -d '' standard_files < <(find "$SRC_DIR" -maxdepth 1 -type f \
  \( "${FILE_PATTERNS[@]}" \) \
  ! -name "${SPECIAL_PREFIX}*" -print0 | sort -z)

# Find all special files (those matching the prefix) and sort them using version-sort (-V).
readarray -d '' special_files < <(find "$SRC_DIR" -maxdepth 1 -type f \
  -name "${SPECIAL_PREFIX}*" \
  \( "${FILE_PATTERNS[@]}" \) -print0 | sort -zV)

# Combine the two arrays into a single list for processing.
all_files=("${standard_files[@]}" "${special_files[@]}")


if [ ${#all_files[@]} -eq 0 ]; then
  echo "Warning: No files found to process in './${SRC_DIR}/'."
  exit 0
fi

# --- File Concatenation Logic ---
if [ "$CHUNK_MODE" = false ]; then
    # --- SINGLE FILE MODE ---
    echo "Initializing output file: ${OUTPUT_FILE}"
    > "$OUTPUT_FILE"
    echo "Processing ${#all_files[@]} files into a single output..."

    for file in "${all_files[@]}"; do
        if [ -f "$file" ]; then
            if [[ "$(basename "$file")" == "$CHANGELOG_FILE" ]]; then
                echo "  -> Adding last 75 lines of ${file}"
                echo "------------------- filepath: ${file} (last 75 lines) ----------------------" >> "$OUTPUT_FILE"
                echo "$CHANGELOG_INSTRUCTIONS" >> "$OUTPUT_FILE"
                printf '\n\n' >> "$OUTPUT_FILE"
                tail -n 75 "$file" >> "$OUTPUT_FILE"
            else
                echo "  -> Adding ${file}"
                echo "------------------- filepath: ${file} ----------------------" >> "$OUTPUT_FILE"
                cat "$file" >> "$OUTPUT_FILE"
            fi
            printf '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n' >> "$OUTPUT_FILE"
        fi
    done
    echo "Appending directory tree..."
    echo "---------------------- tree structure for reference -----------------" >> "$OUTPUT_FILE"
    tree -L 3 -I "node_modules" >> "$OUTPUT_FILE"
else
    # --- CHUNK MODE ---
    echo "Running in chunk mode. Max chunk size: ${CHUNK_SIZE_KB}KB"
    chunk_counter=1
    current_chunk_bytes=0
    chunk_size_bytes=$((CHUNK_SIZE_KB * 1024))
    output_base_name="${OUTPUT_FILE%.*}"
    current_output_file="${output_base_name}_chunk_${chunk_counter}.md"

    echo "Initializing first chunk: ${current_output_file}"
    > "$current_output_file"

    for file in "${all_files[@]}"; do
        if [ -f "$file" ]; then
            header_text=""
            file_size_bytes=0
            instruction_size_bytes=0

            if [[ "$(basename "$file")" == "$CHANGELOG_FILE" ]]; then
                header_text="------------------- filepath: ${file} (last 75 lines) ----------------------"
                changelog_content=$(tail -n 75 "$file")
                file_size_bytes=$(echo -n "$changelog_content" | wc -c)
                instruction_size_bytes=${#CHANGELOG_INSTRUCTIONS}
                # Add size of instructions and the extra newlines
                size_to_add=$(( ${#header_text} + 2 + instruction_size_bytes + 4 + file_size_bytes + 10 ))
            else
                header_text="------------------- filepath: ${file} ----------------------"
                file_size_bytes=$(wc -c < "$file")
                size_to_add=$(( ${#header_text} + 2 + file_size_bytes + 10 )) # +2 for newlines, +10 for separator
            fi

            if [ "$DEBUG_MODE" = true ]; then
                echo "--- DEBUG ---" >&2
                echo "File: $file" >&2
                echo "Current Chunk Bytes: $current_chunk_bytes" >&2
                echo "Size to Add: $size_to_add" >&2
                echo "Limit: $chunk_size_bytes" >&2
                echo "Condition: if [[ $current_chunk_bytes -gt 0 && $((current_chunk_bytes + size_to_add)) -gt $chunk_size_bytes ]]" >&2
            fi

            if [[ $current_chunk_bytes -gt 0 && $((current_chunk_bytes + size_to_add)) -gt $chunk_size_bytes ]]; then
                if [ "$DEBUG_MODE" = true ]; then echo "DEBUG: Condition MET. Creating new chunk." >&2; fi
                ((chunk_counter++))
                current_chunk_bytes=0
                current_output_file="${output_base_name}_chunk_${chunk_counter}.md"
                echo "Initializing new chunk: ${current_output_file}"
                > "$current_output_file"
            else
                 if [ "$DEBUG_MODE" = true ]; then echo "DEBUG: Condition NOT met. Continuing with current chunk." >&2; fi
            fi

            echo "$header_text" >> "$current_output_file"
            echo "" >> "$current_output_file"

            if [[ "$(basename "$file")" == "$CHANGELOG_FILE" ]]; then
                echo "  -> Adding last 75 lines of ${file} to ${current_output_file}"
                echo "$CHANGELOG_INSTRUCTIONS" >> "$current_output_file"
                printf '\n\n' >> "$current_output_file"
                tail -n 75 "$file" >> "$current_output_file"
            else
                echo "  -> Adding ${file} to ${current_output_file}"
                cat "$file" >> "$current_output_file"
            fi
            
            printf '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n' >> "$current_output_file"
            
            current_chunk_bytes=$(( current_chunk_bytes + size_to_add ))
        fi
    done
    # Append tree to the very last chunk
    echo "Appending directory tree to the final chunk: ${current_output_file}"
    echo "---------------------- tree structure for reference -----------------" >> "$current_output_file"
    tree -L 3 -I "node_modules" >> "$current_output_file"
fi

# --- Finalization ---
echo ""
echo "Script finished successfully."
if [ "$CHUNK_MODE" = false ]; then
    echo "Concatenated content is available in '${OUTPUT_FILE}'."
else
    echo "Chunked content is available in files named '${output_base_name}_chunk_*.md'."
fi

