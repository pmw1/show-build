#!/bin/bash

# Show-Build Frontend Debugging Quick Scan
# Usage: ./scripts/debug-frontend.sh

cd "$(dirname "$0")/.."

echo "🔍 ===== SHOW-BUILD FRONTEND DEBUG SCAN ====="
echo "Timestamp: $(date)"
echo ""

# 1. Template Ref Naming Conflicts
echo "1️⃣  TEMPLATE REF CONFLICTS:"
cd disaffected-ui/src
CONFLICTS=$(grep -rn 'ref="[^"]*"' . | sed 's/.*ref="\([^"]*\)".*/\1/' | sort | uniq -d)
if [ -z "$CONFLICTS" ]; then
    echo "   ✅ No template ref naming conflicts found"
else
    echo "   ❌ CONFLICTS FOUND:"
    echo "$CONFLICTS" | sed 's/^/      - /'
    echo "   🔧 Fix: Rename template refs to end with 'Ref' (e.g., formRef, dialogRef)"
fi
echo ""

# 2. Duplicate Component Check
echo "2️⃣  DUPLICATE COMPONENTS:"
cd disaffected-ui/src
DUPLICATES=$(find . -name "*.vue" -exec basename {} \; | sort | uniq -d)
if [ -z "$DUPLICATES" ]; then
    echo "   ✅ No duplicate components found"
else
    echo "   ⚠️  DUPLICATE COMPONENTS FOUND (can cause 'changes don't appear' issues):"
    echo "$DUPLICATES" | while read dup; do
        echo "      - $dup:"
        find . -name "$dup" -type f | sed 's/^/          → /'
    done
    echo "   🔧 Run: ./scripts/check-duplicate-components.sh for detailed analysis"
fi
echo ""

# 3. Vue App Mounting Check
echo "3️⃣  VUE APP MOUNTING:"
cd ..
MOUNTS=$(grep -n "createApp\|mount(" src/main.js | wc -l)
if [ "$MOUNTS" -eq 2 ]; then
    echo "   ✅ Normal Vue app mounting detected (createApp + mount)"
else
    echo "   ⚠️  Unusual mounting pattern detected:"
    grep -n "createApp\|mount(" src/main.js | sed 's/^/      /'
fi
echo ""

# 4. Backend Connectivity
echo "4️⃣  BACKEND CONNECTIVITY:"
cd ..
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/health 2>/dev/null)
if [ "$BACKEND_STATUS" = "200" ]; then
    echo "   ✅ Backend accessible at localhost:8888"
    
    # Test key endpoints
    echo "   📡 Testing key API endpoints:"
    
    NEXT_NUM=$(curl -s http://localhost:8888/api/episodes/next-number 2>/dev/null | jq -r '.next_number // "ERROR"' 2>/dev/null)
    if [ "$NEXT_NUM" != "ERROR" ] && [ "$NEXT_NUM" != "null" ]; then
        echo "      ✅ /api/episodes/next-number → $NEXT_NUM"
    else
        echo "      ❌ /api/episodes/next-number → Failed"
    fi
    
    TEMPLATES=$(curl -s http://localhost:8888/api/episodes/templates 2>/dev/null | jq -r 'length // "ERROR"' 2>/dev/null)
    if [ "$TEMPLATES" != "ERROR" ] && [ "$TEMPLATES" != "null" ] && [ "$TEMPLATES" -gt 0 ]; then
        echo "      ✅ /api/episodes/templates → $TEMPLATES templates"
    else
        echo "      ❌ /api/episodes/templates → Failed"
    fi
else
    echo "   ❌ Backend not accessible (HTTP $BACKEND_STATUS)"
    echo "   🔧 Fix: Run 'docker compose up --build server' or check port 8888"
fi
echo ""

# 4. Frontend Server Status
echo "5️⃣  FRONTEND SERVER:"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 2>/dev/null)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "   ✅ Frontend accessible at localhost:8080"
else
    echo "   ❌ Frontend not accessible (HTTP $FRONTEND_STATUS)"
    echo "   🔧 Fix: Run 'npm run serve' in disaffected-ui/ directory"
fi
echo ""

# 5. Common File Issues
echo "6️⃣  COMMON FILE ISSUES:"
cd disaffected-ui/src

# Check for common problematic patterns
CONSOLE_LOGS=$(grep -r "console\.log" . --include="*.vue" | wc -l)
if [ "$CONSOLE_LOGS" -gt 20 ]; then
    echo "   ⚠️  High number of console.log statements ($CONSOLE_LOGS) - consider cleanup"
else
    echo "   ✅ Reasonable console.log usage ($CONSOLE_LOGS statements)"
fi

# Check for error handling
ERROR_HANDLING=$(grep -r "catch.*error" . --include="*.vue" | wc -l)
if [ "$ERROR_HANDLING" -lt 3 ]; then
    echo "   ⚠️  Limited error handling found - consider adding more try/catch blocks"
else
    echo "   ✅ Error handling present ($ERROR_HANDLING catch blocks)"
fi

echo ""
echo "🎯 ===== NEXT STEPS ====="
echo "1. If conflicts found: Fix template ref naming immediately"
echo "2. Open browser DevTools → Console tab for runtime errors"  
echo "3. Check Network tab for failed API requests"
echo "4. Use Vue DevTools for component state inspection"
echo "5. See docs/DEBUGGING_STANDARDS.md for detailed debugging guide"
echo ""
echo "⏱️  Scan completed in $(date '+%H:%M:%S')"