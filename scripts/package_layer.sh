#!/bin/bash
# Package bbws-auth as a Lambda Layer zip
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build"

echo "=== Packaging bbws-auth Lambda Layer ==="

# Clean
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/python"

# Copy package (no external dependencies - boto3 is provided by Lambda runtime)
cp -r "$PROJECT_ROOT/src/bbws_auth" "$BUILD_DIR/python/"

# Create zip
cd "$BUILD_DIR"
zip -r "$PROJECT_ROOT/bbws-auth-layer.zip" python/

echo "=== Layer packaged: bbws-auth-layer.zip ==="
echo "Size: $(du -h "$PROJECT_ROOT/bbws-auth-layer.zip" | cut -f1)"
