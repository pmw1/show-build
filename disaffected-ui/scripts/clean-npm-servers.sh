#!/bin/bash

# Clean NPM Cache and Hanging Servers Script
# Clears npm cache, kills hanging processes, and reinstalls dependencies

set -e  # Exit on any error

echo "🧹 Starting NPM cache and server cleanup..."

# Function to print colored output
print_step() {
    echo -e "\n🔄 $1..."
}

print_success() {
    echo "✅ $1"
}

print_error() {
    echo "❌ $1"
}

# Step 1: Clear NPM cache globally
print_step "Clearing NPM cache globally"
npm cache clean --force 2>/dev/null || {
    print_error "Failed to clear npm cache"
    exit 1
}
print_success "NPM cache cleared"

# Step 2: Kill hanging Node.js processes
print_step "Killing hanging Node.js processes"

# Find and kill Node.js related processes
NODE_PROCESSES=$(ps aux | grep -E "(node|npm|vue-cli)" | grep -v grep | awk '{print $2}' || true)

if [ ! -z "$NODE_PROCESSES" ]; then
    echo "Found hanging processes: $NODE_PROCESSES"
    echo "$NODE_PROCESSES" | xargs kill -9 2>/dev/null || true
    print_success "Killed hanging Node.js processes"
else
    print_success "No hanging Node.js processes found"
fi

# Step 3: Clear frontend dependencies and reinstall
print_step "Clearing frontend node_modules and reinstalling"

# Get script directory to find disaffected-ui
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
FRONTEND_DIR="$(dirname "$SCRIPT_DIR")"

if [ ! -f "$FRONTEND_DIR/package.json" ]; then
    print_error "Could not find package.json in $FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR"

# Remove existing node_modules and package-lock.json
rm -rf node_modules package-lock.json 2>/dev/null || true
print_success "Removed node_modules and package-lock.json"

# Reinstall dependencies
npm install
print_success "Dependencies reinstalled"

# Step 4: Fix SSL certificate permissions if needed
print_step "Fixing SSL certificate permissions"
if [ -d "$FRONTEND_DIR/ssl" ]; then
    # Check if SSL directory has permission issues
    if ! [ -r "$FRONTEND_DIR/ssl/key.pem" ] 2>/dev/null || ! [ -r "$FRONTEND_DIR/ssl/cert.pem" ] 2>/dev/null; then
        echo "SSL certificates have permission issues, removing them"
        rm -rf "$FRONTEND_DIR/ssl" 2>/dev/null || true
        print_success "Removed problematic SSL certificates - will auto-generate on startup"
    else
        print_success "SSL certificates are readable"
    fi
else
    print_success "No SSL directory found - will auto-generate on startup"
fi

# Step 5: Clean up Docker containers
print_step "Cleaning up problematic Docker containers"

# Find containers that are unhealthy, exited, or restarting
PROBLEM_CONTAINERS=$(docker ps -a --filter "status=exited" --filter "health=unhealthy" -q 2>/dev/null || true)
RESTARTING_CONTAINERS=$(docker ps --filter "status=restarting" -q 2>/dev/null || true)

ALL_PROBLEM_CONTAINERS="$PROBLEM_CONTAINERS $RESTARTING_CONTAINERS"

if [ ! -z "$ALL_PROBLEM_CONTAINERS" ]; then
    echo "Found problematic containers: $ALL_PROBLEM_CONTAINERS"
    # Stop any running problematic containers
    echo "$ALL_PROBLEM_CONTAINERS" | xargs docker stop 2>/dev/null || true
    # Remove the containers
    echo "$ALL_PROBLEM_CONTAINERS" | xargs docker rm 2>/dev/null || true
    print_success "Cleaned up problematic Docker containers"
else
    print_success "No problematic Docker containers found"
fi

echo -e "\n🎉 Cleanup complete! NPM cache cleared, hanging servers killed, dependencies reinstalled, and Docker cleaned up."
echo "You can now start your development servers fresh."