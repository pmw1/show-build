#!/usr/bin/env bash
# This script generates a text file with project information

# Check for minimum Bash version 4
if ((BASH_VERSINFO[0] < 4)); then
    echo "This script requires Bash version 4 or higher." >&2
    exit 1
fi


# Check for required commands
if ! command -v tree &>/dev/null; then
    echo "The 'tree' command is required but not installed."
    echo "To install on Ubuntu/Debian: sudo apt-get install tree"
    echo "To install on MacOS (Homebrew): brew install tree"
    exit 1
fi

if ! command -v realpath &>/dev/null; then
    echo "The 'realpath' command is required but not installed."
    echo "To install on Ubuntu/Debian: sudo apt-get install realpath"
    echo "To install on MacOS (Homebrew): brew install coreutils"
    exit 1
fi

print_file_info() {
    local filepath="$1"
    local abs_path
    abs_path="$(realpath "$filepath")"
    local rel_path
    rel_path="$(realpath --relative-to="$(pwd)" "$filepath")"

    echo "------------------------------------------------------------------------------------------------"
    echo "relative to project root: $rel_path"
    echo "absolute: $abs_path"
    echo
    echo '```'
    while IFS= read -r line; do
        echo "$line"
    done < "$filepath"
    echo '```'
    echo
    echo
}

scan_and_print_files() {
    local base_path="$1"
    local project_root
    project_root="$(pwd)"
    local include_dirs=()
    local subdirs=()

    # Gather subdirectories
    while IFS= read -r -d '' dir; do
        subdirs+=("$dir")
    done < <(find "$base_path" -mindepth 1 -maxdepth 1 -type d -print0)

    # Prompt user for each subdirectory
    for dir in "${subdirs[@]}"; do
        dir_name="$(basename "$dir")"
        echo "Directory: $dir_name"
        echo -n "Include this directory in scan? (i=include, o=omit): "
        read -n 1 choice
        echo
        if [[ "$choice" == "i" ]]; then
            include_dirs+=("$dir")
        fi
    done

    # Build find arguments for included directories
    find_args=()
    if [ "${#include_dirs[@]}" -eq 0 ]; then
        find_args=("$base_path")
    else
        for inc in "${include_dirs[@]}"; do
            find_args+=("$inc")
        done
    fi

    # Find all files in included directories (or base if none included)
    while IFS= read -r -d '' file; do
        local abs_path
        abs_path="$(realpath "$file")"
        local rel_path
        rel_path="$(realpath --relative-to="$project_root" "$file")"

        echo "------------------------------------------------------------------------------------------------"
        echo "relative to project root: $rel_path"
        echo "absolute: $abs_path"
        echo
        echo "Tree to file from project root:"
        tree -L 100 -f --noreport "$project_root" | grep --color=never "$rel_path"
        echo
        echo '```'
        cat "$file"
        echo '```'
        echo
        echo
    done < <(find "${find_args[@]}" -type f -print0)
}

list_and_exclude_directories() {
    local base_path="$1"
    local -a dir_list
    local -A dir_map
    local idx=1

    # Gather all directories recursively
    while IFS= read -r -d '' dir; do
        dir_list+=("$dir")
        dir_map["$idx"]="$dir"
        ((idx++))
    done < <(find "$base_path" -type d -print0)

    # Print enumerated directory list
    echo "Enumerated directory list:"
    for i in "${!dir_list[@]}"; do
        num=$((i+1))
        rel_dir="$(realpath --relative-to="$base_path" "${dir_list[$i]}")"
        echo "$num) $rel_dir"
    done

    echo
    echo "Enter comma-separated numbers of directories to EXCLUDE (e.g. 2,5,7), or leave blank for none:"
    read -r exclude_input

    # Parse exclusions
    IFS=',' read -ra exclude_nums <<< "$exclude_input"
    declare -A exclude_dirs
    for num in "${exclude_nums[@]}"; do
        num="$(echo "$num" | xargs)" # trim
        if [[ -n "${dir_map[$num]}" ]]; then
            exclude_dirs["${dir_map[$num]}"]=1
        fi
    done

    # Print tree, showing excluded dirs as "..."
    print_tree_with_exclusions() {
        local path="$1"
        local prefix="$2"
        local rel_path
        rel_path="$(realpath --relative-to="$base_path" "$path")"
        if [[ "${exclude_dirs[$path]}" == "1" ]]; then
            echo "${prefix}${rel_path}/ ..."
            return
        fi
        echo "${prefix}${rel_path}/"
        local child
        while IFS= read -r -d '' child; do
            print_tree_with_exclusions "$child" "    $prefix"
        done < <(find "$path" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)
        # List files in this directory
        while IFS= read -r -d '' file; do
            file_rel="$(realpath --relative-to="$base_path" "$file")"
            echo "${prefix}    $file_rel"
        done < <(find "$path" -mindepth 1 -maxdepth 1 -type f -print0 | sort -z)
    }

    echo
    echo "Project directory tree (excluded directories shown as ...):"
    print_tree_with_exclusions "$base_path" ""
    echo
}



print_system_info() {
    echo "System Information:"
    echo "-------------------"
    echo "Hostname: $(hostname)"
    echo "Date: $(date)"
    echo "Uptime: $(uptime -p)"
    echo "User: $(whoami)"
    echo "OS: $(uname -a)"
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "Distribution: $PRETTY_NAME"
    fi
    echo

    echo "CPU Info:"
    if command -v lscpu &>/dev/null; then
        lscpu | grep -E 'Model name|Socket|Thread|Core|CPU\(s\):'
    else
        grep -E 'model name|cpu cores|siblings' /proc/cpuinfo | sort | uniq
    fi
    echo

    echo "Memory Info:"
    free -h
    echo

    echo "Disk Usage:"
    df -h /
    echo

    if command -v nvidia-smi &>/dev/null; then
        echo "NVIDIA GPU Info:"
        nvidia-smi
        echo
    else
        echo "NVIDIA GPU Info: nvidia-smi not found."
        echo
    fi

    echo "Docker Info:"
    if command -v docker &>/dev/null; then
        docker info 2>/dev/null | head -n 20
        echo
        echo "Docker Containers:"
        docker ps -a
        echo
        echo "Docker Images:"
        docker images
        echo
    else
        echo "Docker not installed."
        echo
    fi

        # Print running Docker containers and their networks
        if command -v docker &>/dev/null; then
            echo
            echo "Running Docker Containers and Networks:"
            docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"
            echo

            echo "Docker Networks and Connected Containers:"
            docker network ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"
            echo

            for net in $(docker network ls --format "{{.Name}}"); do
                echo "Network: $net"
                docker network inspect "$net" --format '{{range .Containers}}{{.Name}}{{"\t"}}{{end}}'
                echo
            done
            echo
        fi
        echo
}


echo "#PROJECT INFO FOR SHOW BUILD" > info.txt
echo "This document is compiled on-the-fly using a bash script executed in the root of the project." >> info.txt                                                                                                                             
echo "The contents of the bash script generating this file will be included in this text file." >> info.txt                                                              
echo "The script is designed to be run in the root directory of the project." >> info.txt
echo "" >> info.txt
echo "TABLE OF CONTENTS" >> info.txt
echo "----------------------------------------" >> info.txt
echo "Contents of:     This file (info.txt):" >> info.txt
echo "Contents of:     README.md (the main project documentation file)" >> info.txt
echo "Contents of:     The project file system structure" >> info.txt
echo "Contents of:     gather.sh (the bash script generating this file)" >> info.txt
echo "Contents of:     backend of the system (multiple file) e.g. the app folder and FastAPI/python/routes etc" >> info.txt
echo "Contents of:     frontend of the system e.g. the app folder and ReactJS/NextJS/components etc" >> info.txt
echo "----------------------------------------" >> info.txt
echo "System info:     System information including docker info" >> info.txt
echo "----------------------------------------" >> info.txt
echo "" >> info.txt
echo "BEGIN SCRIPT OUTPUT" >> info.txt
echo ""

print_file_info "gather.sh" >> info.txt
print_file_info "README.md" >> info.txt

# Interactive functions: capture output to temp files, then append
tmpdir=$(mktemp -d)
list_and_exclude_directories "." > "$tmpdir/tree.txt"
scan_and_print_files "app" > "$tmpdir/app.txt"
scan_and_print_files "disaffected-ui" > "$tmpdir/ui.txt"

cat "$tmpdir/tree.txt" >> info.txt
cat "$tmpdir/app.txt" >> info.txt
cat "$tmpdir/ui.txt" >> info.txt
rm -rf "$tmpdir"

##system info
print_system_info >> info.txt

echo "Script completed successfully. Project information has been saved to info.txt."
echo "You can view the file using any text editor."
