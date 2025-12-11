#!/usr/bin/env python3
"""
Add putFile endpoint to OpenAPI specification.

This script adds the PUT /api/v1/putFile endpoint to the OpenAPI spec.
This endpoint is hosted on upload.sajn.se (not app.sajn.se) and is not
auto-generated from the main API's OpenAPI spec.

Run this script BEFORE validate-openapi.sh when updating the OpenAPI spec:
    python3 scripts/add-putfile-endpoint.py
    ./scripts/validate-openapi.sh

Usage:
    python3 scripts/add-putfile-endpoint.py [path-to-openapi.json]

If no path is provided, defaults to: api/openapi.json
"""

import json
import sys
from pathlib import Path

# The putFile endpoint definition
PUTFILE_ENDPOINT = {
    "put": {
        "description": "Upload a file directly to sajn storage.\n\n**Important:** This endpoint uses `https://upload.sajn.se` as the base URL, not `https://app.sajn.se`.\n\n**File Requirements:**\n- Maximum size: 100 MB\n- Allowed types: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, MP4, MOV, AVI, WEBM, JPG, PNG, GIF, WEBP, SVG\n\n**Visibility:**\n- `PRIVATE` (default): Files require signed URLs for access (60 min expiry)\n- `PUBLIC`: Files are accessible via direct CloudFront URL\n\n**Example Upload:**\n```bash\n# Private file (default)\ncurl -X PUT https://upload.sajn.se/api/v1/putFile \\\n  -H \"Authorization: Bearer YOUR_API_KEY\" \\\n  -F \"file=@/path/to/document.pdf\"\n\n# Public file\ncurl -X PUT https://upload.sajn.se/api/v1/putFile \\\n  -H \"Authorization: Bearer YOUR_API_KEY\" \\\n  -F \"file=@/path/to/image.png\" \\\n  -F \"visibility=PUBLIC\"\n```",
        "summary": "Upload file",
        "tags": [],
        "parameters": [
            {
                "name": "authorization",
                "in": "header",
                "description": "Bearer token for API authentication",
                "required": True,
                "schema": {
                    "type": "string"
                }
            }
        ],
        "operationId": "putFile",
        "requestBody": {
            "description": "Multipart form data with file and optional visibility",
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "description": "File upload request",
                        "type": "object",
                        "properties": {
                            "file": {
                                "description": "The file to upload. Allowed types: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, MP4, MOV, AVI, WEBM, JPG, PNG, GIF, WEBP, SVG",
                                "type": "string",
                                "format": "binary"
                            },
                            "visibility": {
                                "description": "File visibility: PRIVATE (requires signed URL) or PUBLIC (direct access)",
                                "default": "PRIVATE",
                                "type": "string",
                                "enum": [
                                    "PRIVATE",
                                    "PUBLIC"
                                ]
                            }
                        },
                        "required": [
                            "file"
                        ],
                        "additionalProperties": False
                    }
                }
            }
        },
        "responses": {
            "200": {
                "description": "File uploaded successfully",
                "content": {
                    "application/json": {
                        "schema": {
                            "description": "File upload response",
                            "type": "object",
                            "properties": {
                                "key": {
                                    "description": "Storage key for the uploaded file",
                                    "type": "string"
                                },
                                "file": {
                                    "description": "File metadata",
                                    "type": "object",
                                    "properties": {
                                        "id": {
                                            "description": "Unique file identifier",
                                            "type": "string"
                                        },
                                        "filename": {
                                            "description": "Original filename",
                                            "type": "string"
                                        },
                                        "mimeType": {
                                            "description": "MIME type of the file",
                                            "type": "string"
                                        },
                                        "size": {
                                            "description": "File size in bytes",
                                            "type": "integer"
                                        },
                                        "hash": {
                                            "description": "SHA-256 hash of the file",
                                            "type": "string"
                                        }
                                    },
                                    "required": [
                                        "id",
                                        "filename",
                                        "mimeType",
                                        "size",
                                        "hash"
                                    ],
                                    "additionalProperties": False
                                }
                            },
                            "required": [
                                "key",
                                "file"
                            ],
                            "additionalProperties": False
                        }
                    }
                }
            },
            "400": {
                "description": "Error response",
                "content": {
                    "application/json": {
                        "schema": {
                            "description": "Error response",
                            "type": "object",
                            "properties": {
                                "message": {
                                    "description": "Error message describing what went wrong",
                                    "type": "string"
                                }
                            },
                            "required": [
                                "message"
                            ],
                            "additionalProperties": False
                        }
                    }
                }
            },
            "401": {
                "description": "Error response",
                "content": {
                    "application/json": {
                        "schema": {
                            "description": "Error response",
                            "type": "object",
                            "properties": {
                                "message": {
                                    "description": "Error message describing what went wrong",
                                    "type": "string"
                                }
                            },
                            "required": [
                                "message"
                            ],
                            "additionalProperties": False
                        }
                    }
                }
            }
        }
    }
}


def add_putfile_endpoint(file_path):
    """Add the putFile endpoint to the OpenAPI specification"""
    print(f"Loading OpenAPI spec from: {file_path}")

    # Read the OpenAPI file
    with open(file_path, 'r') as f:
        spec = json.load(f)

    # Check if paths exists
    if 'paths' not in spec:
        spec['paths'] = {}

    # Remove old presigned-url endpoint if it exists
    if '/api/v1/files/presigned-url' in spec['paths']:
        print("  Removing old /api/v1/files/presigned-url endpoint...")
        del spec['paths']['/api/v1/files/presigned-url']

    # Add the putFile endpoint
    print("  Adding /api/v1/putFile endpoint...")
    spec['paths']['/api/v1/putFile'] = PUTFILE_ENDPOINT

    # Write back
    with open(file_path, 'w') as f:
        json.dump(spec, f, indent=2)

    print(f"\n✓ putFile endpoint added to: {file_path}")


def main():
    # Default path
    default_path = Path("api/openapi.json")

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

    # Add the endpoint
    try:
        add_putfile_endpoint(file_path)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}")
        print(f"  {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
