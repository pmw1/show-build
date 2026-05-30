#!/bin/bash

# Navigate to the project root
cd /mnt/process/show-build || exit 1

# Search for common assetID variations
echo "Searching for assetID references..."
grep -rIn --color=always \
  -e 'assetID' \
  -e 'asset_id' \
  -e '"asset_id"' \
  --exclude-dir=node_modules \
  --exclude-dir=__pycache__ \
  --exclude=\*.log \
  .

