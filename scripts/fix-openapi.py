#!/usr/bin/env python3
"""
OpenAPI 3.0.2 Fixer for Mintlify

This script fixes common OpenAPI validation issues to ensure compatibility
with Mintlify's validation requirements and OpenAPI 3.0.2 specification.

Fixes applied:
1. Replace 'const' with 'enum' (single-value array)
2. Replace anyOf nullable patterns with nullable: true
3. Fix empty schema objects ({}) by adding type: string
4. Remove invalid 'propertyNames' fields (not in OpenAPI 3.0.2)

Usage:
    python3 scripts/fix-openapi.py [path-to-openapi.json]

If no path is provided, defaults to: api-reference/openapi.json
"""

import json
import sys
from pathlib import Path


def fix_const_to_enum(obj):
    """Recursively replace 'const' with 'enum' containing single value"""
    if isinstance(obj, dict):
        if 'const' in obj:
            const_value = obj.pop('const')
            obj['enum'] = [const_value]
        for value in obj.values():
            fix_const_to_enum(value)
    elif isinstance(obj, list):
        for item in obj:
            fix_const_to_enum(item)


def fix_nullable_fields(obj):
    """Recursively replace anyOf patterns with nullable: true"""
    if isinstance(obj, dict):
        # Pattern 1: anyOf with empty object {} and {type: null}
        # Pattern 2: anyOf with {type: X} and {type: null}
        if 'anyOf' in obj and isinstance(obj['anyOf'], list):
            any_of = obj['anyOf']
            has_null = any(item.get('type') == 'null' for item in any_of if isinstance(item, dict))
            has_empty = any(item == {} for item in any_of)

            if has_null and len(any_of) == 2:
                if has_empty:
                    # Empty object + null = nullable string
                    obj.pop('anyOf')
                    obj['type'] = 'string'
                    obj['nullable'] = True
                else:
                    # Has a real type + null
                    non_null_items = [item for item in any_of if item.get('type') != 'null' and item != {}]
                    if len(non_null_items) == 1:
                        obj.pop('anyOf')
                        obj.update(non_null_items[0])
                        obj['nullable'] = True

        # Recurse into nested objects
        for value in list(obj.values()):
            fix_nullable_fields(value)
    elif isinstance(obj, list):
        for item in obj:
            fix_nullable_fields(item)


def fix_empty_schemas(obj, path=""):
    """Recursively find and fix empty schema objects"""
    if isinstance(obj, dict):
        # Check if this looks like a property definition that's just {}
        for key, value in list(obj.items()):
            if key in ['properties', 'items', 'additionalProperties'] and isinstance(value, dict):
                # Check nested properties
                if 'properties' in value and isinstance(value['properties'], dict):
                    for prop_name, prop_schema in list(value['properties'].items()):
                        if prop_schema == {}:
                            # Empty schema - default to string type
                            value['properties'][prop_name] = {'type': 'string'}
                elif value == {} and key != 'additionalProperties':
                    # The value itself is empty
                    obj[key] = {'type': 'string'}

        # Recurse
        for key, value in list(obj.items()):
            new_path = f"{path}.{key}" if path else key
            fix_empty_schemas(value, new_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            fix_empty_schemas(item, f"{path}[{i}]")


def remove_property_names(obj):
    """Remove propertyNames which is not valid in OpenAPI 3.0.2"""
    if isinstance(obj, dict):
        # Remove propertyNames if it exists
        if 'propertyNames' in obj:
            del obj['propertyNames']

        # Recurse
        for value in obj.values():
            remove_property_names(value)
    elif isinstance(obj, list):
        for item in obj:
            remove_property_names(item)


def fix_openapi_spec(file_path):
    """Apply all fixes to an OpenAPI specification file"""
    print(f"Loading OpenAPI spec from: {file_path}")

    # Read the OpenAPI file
    with open(file_path, 'r') as f:
        spec = json.load(f)

    print("Applying fixes...")
    print("  1. Replacing 'const' with 'enum'...")
    fix_const_to_enum(spec)

    print("  2. Fixing nullable fields (anyOf patterns)...")
    fix_nullable_fields(spec)

    print("  3. Fixing empty schema objects...")
    fix_empty_schemas(spec)

    print("  4. Removing invalid 'propertyNames' fields...")
    remove_property_names(spec)

    # Write back
    with open(file_path, 'w') as f:
        json.dump(spec, f, indent=2)

    print(f"\n✓ OpenAPI spec fixed and saved to: {file_path}")
    print("\nRun validation:")
    print(f"  mint openapi-check {file_path}")


def main():
    # Default path
    default_path = Path("api-reference/openapi.json")

    # Get path from command line or use default
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        file_path = default_path

    # Check if file exists
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    # Check if it's a JSON file
    if file_path.suffix != '.json':
        print(f"Error: File must be a .json file: {file_path}")
        sys.exit(1)

    # Fix the spec
    try:
        fix_openapi_spec(file_path)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}")
        print(f"  {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
