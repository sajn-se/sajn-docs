# Scripts

This directory contains utility scripts for maintaining the sajn documentation site.

## OpenAPI Validation & Fixing

### Quick Start

```bash
# Fix and validate your OpenAPI spec (recommended)
./scripts/validate-openapi.sh

# Or specify a custom path
./scripts/validate-openapi.sh path/to/your/openapi.json
```

### Available Scripts

#### `validate-openapi.sh`
**All-in-one script** that fixes common issues and validates your OpenAPI specification.

**What it does:**
1. Automatically fixes common OpenAPI 3.0.2 compatibility issues
2. Validates the spec using Mintlify's CLI
3. Provides clear success/failure feedback

**Usage:**
```bash
./scripts/validate-openapi.sh [path-to-openapi.json]
```

Default path: `api/openapi.json`

---

#### `fix-openapi.py`
**Python script** that fixes OpenAPI 3.0.2 compatibility issues for Mintlify.

**Fixes applied:**
- Replace `const` with `enum` (single-value array)
- Replace `anyOf` nullable patterns with `nullable: true`
- Fix empty schema objects (`{}`) by adding `type: string`
- Remove invalid `propertyNames` fields (not in OpenAPI 3.0.2 spec)

**Usage:**
```bash
python3 scripts/fix-openapi.py [path-to-openapi.json]
```

**Direct usage:**
```bash
# Fix the default OpenAPI spec
python3 scripts/fix-openapi.py

# Fix a custom file
python3 scripts/fix-openapi.py path/to/your/openapi.json
```

---

## Common Issues & Solutions

### Issue: `const` keyword not supported
**Error:** `must NOT have additional properties`
**Fix:** The script replaces `const: "value"` with `enum: ["value"]`

### Issue: Nullable fields using `anyOf`
**Error:** `type must be equal to one of the allowed values`
**Fix:** Converts `anyOf: [{type: "string"}, {type: "null"}]` to `type: "string", nullable: true`

### Issue: Empty schema objects
**Error:** `must have required property '$ref'`
**Fix:** Adds `type: "string"` to properties that are empty objects `{}`

### Issue: Invalid `propertyNames`
**Error:** `must NOT have additional properties`
**Fix:** Removes `propertyNames` which is not part of OpenAPI 3.0.2 spec

---

## Workflow

### After Updating OpenAPI Spec

1. Edit your `api/openapi.json` file
2. Run the validation script:
   ```bash
   ./scripts/validate-openapi.sh
   ```
3. If validation passes, you're ready to commit
4. Preview locally with `mint dev`
5. Commit and push to deploy

### CI/CD Integration (Optional)

You can add this to your CI pipeline to ensure OpenAPI specs are always valid:

```yaml
# Example GitHub Actions workflow
- name: Validate OpenAPI
  run: |
    npm i -g mint
    ./scripts/validate-openapi.sh
```

---

## Requirements

- **Python 3.x** - for fix-openapi.py
- **Mintlify CLI** - for validation (`npm i -g mint`)
- **Bash** - for validate-openapi.sh

## Troubleshooting

### Script not executable
```bash
chmod +x scripts/validate-openapi.sh
chmod +x scripts/fix-openapi.py
```

### Mintlify CLI not found
```bash
npm i -g mint
```

### Python not found
Install Python 3 from [python.org](https://www.python.org/) or use your package manager:
```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt install python3
```
