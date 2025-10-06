#!/bin/bash
# Duplicate Component Checker for Show-Build
# Detects Vue components with identical names in different directories

echo "🔍 SHOW-BUILD: Checking for duplicate Vue components..."
echo ""

# Find all .vue files and check for duplicates
duplicates_found=false

find src/ -name "*.vue" -type f | while read file; do
    basename=$(basename "$file")
    count=$(find src/ -name "$basename" -type f | wc -l)
    
    if [ "$count" -gt 1 ]; then
        echo "⚠️  DUPLICATE COMPONENT FOUND: $basename"
        echo "   This can cause 'changes don't appear' issues when editing the wrong file."
        echo ""
        echo "   Files found:"
        find src/ -name "$basename" -type f | sed 's/^/     → /'
        echo ""
        echo "   Check import statements to see which file is actually used:"
        echo "   grep -r \"import.*${basename%.*}\" src/"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        duplicates_found=true
    fi
done

if [ "$duplicates_found" = false ]; then
    echo "✅ No duplicate Vue components found."
else
    echo "📋 NEXT STEPS:"
    echo "   1. Check import statements to identify which file is actually used"
    echo "   2. Rename or consolidate duplicate components"  
    echo "   3. Update import paths to use unique component names"
    echo ""
    echo "📖 See docs/DUPLICATE_COMPONENT_FILES.md for detailed guidance"
fi

echo ""
echo "🎯 If changes don't appear after editing, run this script first!"