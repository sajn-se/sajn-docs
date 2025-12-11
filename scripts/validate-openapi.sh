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
# If no path is provided, defaults to: api/openapi.json

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default path
OPENAPI_FILE="${1:-api/openapi.json}"

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

# Step 1: Add putFile endpoint (hosted on upload.sajn.se)
echo "Step 1: Adding putFile endpoint..."
python3 scripts/add-putfile-endpoint.py "$OPENAPI_FILE"
echo ""

# Step 2: Fix common issues
echo "Step 2: Fixing common OpenAPI issues..."
python3 scripts/fix-openapi.py "$OPENAPI_FILE"
echo ""

# Step 3: Validate with Mintlify
echo "Step 3: Validating with Mintlify CLI..."

# Check if mint is installed
if ! command -v mint &> /dev/null; then
    echo -e "${YELLOW}⚠ Mintlify CLI not found${NC}"
    echo ""
    echo "Install it with:"
    echo "  npm i -g mint"
    echo ""
    echo "Then run validation manually:"
    echo "  mint openapi-check $OPENAPI_FILE"
    echo ""
    echo -e "${GREEN}✓ OpenAPI spec has been fixed (validation skipped)${NC}"
    exit 0
fi

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
