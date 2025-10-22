#!/bin/bash
#
# OpenAPI Validation Helper for Mintlify
#
# This script fixes and validates your OpenAPI specification to ensure
# compatibility with Mintlify's requirements.
#
# Usage:
#   ./scripts/validate-openapi.sh [path-to-openapi.json]
#
# If no path is provided, defaults to: api-reference/openapi.json

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default path
OPENAPI_FILE="${1:-api-reference/openapi.json}"

echo "🔧 OpenAPI Validation & Fixer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if file exists
if [ ! -f "$OPENAPI_FILE" ]; then
    echo -e "${RED}✗ Error: File not found: $OPENAPI_FILE${NC}"
    exit 1
fi

echo "📁 File: $OPENAPI_FILE"
echo ""

# Step 1: Fix common issues
echo "Step 1: Fixing common OpenAPI issues..."
python3 scripts/fix-openapi.py "$OPENAPI_FILE"
echo ""

# Step 2: Validate with Mintlify
echo "Step 2: Validating with Mintlify CLI..."
if mint openapi-check "$OPENAPI_FILE"; then
    echo ""
    echo -e "${GREEN}✓ Success! OpenAPI specification is valid${NC}"
    echo ""
    echo "You can now:"
    echo "  1. Preview locally: mint dev"
    echo "  2. Commit and push to deploy"
else
    echo ""
    echo -e "${RED}✗ Validation failed${NC}"
    echo ""
    echo "Please check the errors above and fix manually if needed."
    exit 1
fi
