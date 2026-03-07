#!/usr/bin/env python3
"""Generate Postman collections and environment files from api/openapi.json."""

from __future__ import annotations

import json
import re
import uuid
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = ROOT / "api" / "openapi.json"
OUTPUT_DIR = ROOT / "downloads" / "postman"


REFERENCE_FILENAME = "sajn-api-reference.postman_collection.json"
GETTING_STARTED_FILENAME = "sajn-getting-started.postman_collection.json"
DOCUMENT_LIFECYCLE_FILENAME = "sajn-document-lifecycle.postman_collection.json"
CONTACTS_SIGNERS_FILENAME = "sajn-contacts-and-signers.postman_collection.json"
ENV_FILENAME = "sajn-local.postman_environment.json"


REQUEST_OVERRIDES = {
    ("post", "/api/v1/contacts"): {
        "body": {
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
            "phone": "+46701234567",
        }
    },
    ("post", "/api/v1/documents"): {
        "body": {
            "name": "Employment Contract",
            "type": "SIGNABLE",
            "signers": [],
            "documentMeta": {
                "subject": "Employment Contract",
                "message": "Please review and sign this agreement.",
                "signingOrder": "PARALLEL",
                "preferredLanguage": "en",
            },
        }
    },
    ("post", "/api/v1/documents/{id}/signers"): {
        "body": {
            "contactId": "{{contactId}}",
            "role": "SIGNER",
            "deliveryMethod": "EMAIL",
            "requiredSignature": "DRAWING",
        }
    },
    ("post", "/api/v1/documents/{id}/send"): {
        "body": {
            "customMessage": "Please review and sign this document."
        }
    },
    ("post", "/api/v1/sajn-id"): {
        "body": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "locale": "sv-SE",
            "reference": "customer-123",
        }
    },
    ("put", "/api/v1/putFile"): {
        "formdata": [
            {"key": "file", "type": "file", "src": "/absolute/path/to/document.pdf"},
            {"key": "visibility", "type": "text", "value": "PRIVATE"},
        ]
    },
}


CURATED_COLLECTIONS = {
    GETTING_STARTED_FILENAME: {
        "name": "sajn Getting Started",
        "description": "Fastest path to a successful authenticated request and first resource creation in sajn.",
        "requests": [
            ("get", "/api/v1/health"),
            ("get", "/api/v1/documents"),
            ("get", "/api/v1/contacts"),
            ("post", "/api/v1/contacts"),
            ("post", "/api/v1/documents"),
        ],
    },
    DOCUMENT_LIFECYCLE_FILENAME: {
        "name": "sajn Document Lifecycle",
        "description": "Create a document, add a signer, send it for signing, retrieve the signer URL, and download the final document.",
        "requests": [
            ("post", "/api/v1/documents"),
            ("post", "/api/v1/documents/{id}/signers"),
            ("post", "/api/v1/documents/{id}/send"),
            ("get", "/api/v1/documents/{id}/signers/{signerId}"),
            ("get", "/api/v1/documents/{id}/download"),
        ],
    },
    CONTACTS_SIGNERS_FILENAME: {
        "name": "sajn Contacts and Signers",
        "description": "Starter flow for contact creation, lookup, and document signer management.",
        "requests": [
            ("post", "/api/v1/contacts"),
            ("get", "/api/v1/contacts/search"),
            ("patch", "/api/v1/contacts/{id}"),
            ("post", "/api/v1/documents"),
            ("post", "/api/v1/documents/{id}/signers"),
            ("get", "/api/v1/documents/{id}/signers/{signerId}"),
        ],
    },
}


FOLDER_ORDER = [
    "Health",
    "Documents",
    "Document Signers",
    "Document Fields",
    "Document Tags",
    "Contacts",
    "Companies",
    "Files",
    "Tags",
    "Custom Fields",
    "sajn ID",
]


def load_openapi() -> dict:
    with OPENAPI_PATH.open() as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def infer_folder(path: str) -> str:
    if path == "/api/v1/health":
        return "Health"
    if path.startswith("/api/v1/documents/") and "/signers" in path:
        return "Document Signers"
    if path.startswith("/api/v1/documents/") and "/fields" in path:
        return "Document Fields"
    if path.startswith("/api/v1/documents/") and "/tags" in path:
        return "Document Tags"
    if path.startswith("/api/v1/documents"):
        return "Documents"
    if path.startswith("/api/v1/contacts"):
        return "Contacts"
    if path.startswith("/api/v1/companies"):
        return "Companies"
    if path.startswith("/api/v1/custom-fields"):
        return "Custom Fields"
    if path.startswith("/api/v1/sajn-id"):
        return "sajn ID"
    if path.startswith("/api/v1/files") or path.startswith("/api/v1/putFile") or path.startswith("/upload/"):
        return "Files"
    if path.startswith("/api/v1/tags"):
        return "Tags"
    return "Other"


def infer_request_name(method: str, path: str, operation: dict) -> str:
    summary = operation.get("summary")
    if summary:
        return summary
    return f"{method.upper()} {path}"


def schema_to_example(schema: dict | None) -> object:
    if not schema:
        return {}
    if "$ref" in schema:
        return {}
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]
    if schema.get("nullable"):
        stripped = deepcopy(schema)
        stripped.pop("nullable", None)
        return schema_to_example(stripped)
    for combinator in ("anyOf", "oneOf", "allOf"):
        if combinator in schema:
            for option in schema[combinator]:
                if option.get("type") == "null":
                    continue
                return schema_to_example(option)
    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema:
        required = set(schema.get("required", []))
        example = {}
        for prop_name, prop_schema in schema.get("properties", {}).items():
            if prop_name in required:
                example[prop_name] = schema_to_example(prop_schema)
        return example
    if schema_type == "array":
        return [schema_to_example(schema.get("items", {}))]
    if schema_type == "string":
        fmt = schema.get("format")
        if fmt == "date-time":
            return "2026-03-06T12:00:00Z"
        if fmt == "date":
            return "2026-03-06"
        if fmt == "email":
            return "john.doe@example.com"
        if fmt == "uri":
            return "https://example.com/callback"
        return "string"
    if schema_type in {"number", "integer"}:
        minimum = schema.get("minimum")
        return minimum if minimum is not None else 1
    if schema_type == "boolean":
        return True
    return {}


def resolve_request_body(method: str, path: str, operation: dict) -> dict | None:
    override = REQUEST_OVERRIDES.get((method, path), {})
    request_body = operation.get("requestBody")
    if not request_body:
        return None

    content = request_body.get("content", {})
    if "multipart/form-data" in content:
        formdata = override.get("formdata")
        if not formdata:
            schema = content["multipart/form-data"].get("schema", {})
            formdata = []
            for key, prop_schema in schema.get("properties", {}).items():
                entry = {"key": key}
                if prop_schema.get("format") == "binary":
                    entry["type"] = "file"
                    entry["src"] = "/absolute/path/to/file"
                else:
                    entry["type"] = "text"
                    entry["value"] = str(schema_to_example(prop_schema))
                formdata.append(entry)
        return {"mode": "formdata", "formdata": formdata}

    if "application/json" in content:
        body = override.get("body")
        if body is None:
            schema = content["application/json"].get("schema", {})
            body = schema_to_example(schema)
        return {
            "mode": "raw",
            "raw": json.dumps(body, indent=2, ensure_ascii=True),
            "options": {"raw": {"language": "json"}},
        }

    return None


def query_params_for(operation: dict) -> list[dict]:
    params = []
    for parameter in operation.get("parameters", []):
        if parameter.get("in") != "query":
            continue
        schema = parameter.get("schema")
        if not schema and "content" in parameter:
            schema = next(iter(parameter["content"].values())).get("schema")
        value = schema_to_example(schema)
        if value == {}:
            value = ""
        params.append(
            {
                "key": parameter["name"],
                "value": str(value),
                "description": parameter.get("description", ""),
            }
        )
    return params


def variable_name_for(path_parameter: str) -> str:
    mapping = {
        "id": "documentId",
        "signerId": "signerId",
        "fieldId": "fieldId",
        "tagId": "tagId",
        "key": "fileKey",
    }
    return mapping.get(path_parameter, path_parameter)


def build_url(path: str, operation: dict) -> str:
    base_variable = "uploadBaseUrl" if path == "/api/v1/putFile" else "baseUrl"
    raw_path = re.sub(r"\{([^}]+)\}", lambda match: "{{" + variable_name_for(match.group(1)) + "}}", path)
    raw = f"{{{{{base_variable}}}}}{raw_path}"
    query = query_params_for(operation)
    if query:
        query_string = "&".join(f"{param['key']}={param['value']}" for param in query)
        raw = f"{raw}?{query_string}"
    return raw


def build_headers(method: str, body: dict | None) -> list[dict]:
    if not body:
        return []
    if body["mode"] == "raw":
        return [{"key": "Content-Type", "value": "application/json"}]
    return []


def success_status(operation: dict) -> int:
    for code in operation.get("responses", {}):
        if code.isdigit() and 200 <= int(code) < 300:
            return int(code)
    return 200


def curated_test_script(method: str, path: str, operation: dict) -> list[str]:
    lines = [
        f"pm.test('Status code is {success_status(operation)}', function () {{",
        f"  pm.response.to.have.status({success_status(operation)});",
        "});",
    ]

    capture_map = {
        ("post", "/api/v1/contacts"): ("contactId", "response.id"),
        ("post", "/api/v1/documents"): ("documentId", "response.id"),
        ("post", "/api/v1/documents/{id}/signers"): ("signerId", "response.id"),
        ("post", "/api/v1/sajn-id"): ("sajnIdId", "response.id"),
        ("put", "/api/v1/putFile"): ("fileId", "response.id"),
    }
    capture = capture_map.get((method, path))
    if capture:
        variable_name, _ = capture
        lines.extend(
            [
                "var response = {};",
                "try {",
                "  response = pm.response.json();",
                "} catch (error) {",
                "  response = {};",
                "}",
                f"if (response.id) {{ pm.collectionVariables.set('{variable_name}', response.id); }}",
            ]
        )

    if (method, path) == ("get", "/api/v1/documents/{id}/signers/{signerId}"):
        lines.extend(
            [
                "var response = {};",
                "try {",
                "  response = pm.response.json();",
                "} catch (error) {",
                "  response = {};",
                "}",
                "if (response.signingUrl) { pm.collectionVariables.set('signingUrl', response.signingUrl); }",
            ]
        )

    return lines


def build_request_item(method: str, path: str, operation: dict, curated: bool = False) -> dict:
    body = resolve_request_body(method, path, operation)
    item = {
        "name": infer_request_name(method, path, operation),
        "request": {
            "method": method.upper(),
            "header": build_headers(method, body),
            "url": build_url(path, operation),
            "description": operation.get("description") or operation.get("summary", ""),
        },
        "response": [],
    }

    if body:
        item["request"]["body"] = body

    if path == "/api/v1/health":
        item["request"]["auth"] = {"type": "noauth"}

    if curated:
        item["event"] = [
            {
                "listen": "test",
                "script": {
                    "type": "text/javascript",
                    "exec": curated_test_script(method, path, operation),
                },
            }
        ]

    return item


def collection_info(name: str, description: str) -> dict:
    return {
        "_postman_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"sajn:{name}")),
        "name": name,
        "description": description,
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    }


def collection_variables() -> list[dict]:
    return [
        {"key": "baseUrl", "value": "https://app.sajn.se"},
        {"key": "uploadBaseUrl", "value": "https://upload.sajn.se"},
        {"key": "apiKey", "value": ""},
        {"key": "documentId", "value": ""},
        {"key": "contactId", "value": ""},
        {"key": "signerId", "value": ""},
        {"key": "fieldId", "value": ""},
        {"key": "tagId", "value": ""},
        {"key": "fileId", "value": ""},
        {"key": "fileKey", "value": ""},
        {"key": "sajnIdId", "value": ""},
        {"key": "signingUrl", "value": ""},
    ]


def build_reference_collection(openapi: dict) -> tuple[dict, dict]:
    folders = {name: [] for name in FOLDER_ORDER}
    request_lookup = {}

    for path in sorted(openapi["paths"]):
        path_item = openapi["paths"][path]
        for method in sorted(path_item):
            operation = path_item[method]
            item = build_request_item(method, path, operation, curated=False)
            folder = infer_folder(path)
            folders.setdefault(folder, []).append(item)
            request_lookup[(method, path)] = item

    collection = {
        "info": collection_info(
            "sajn API Reference",
            "Complete Postman reference collection generated from the sajn OpenAPI specification.",
        ),
        "auth": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{apiKey}}", "type": "string"}],
        },
        "variable": collection_variables(),
        "item": [{"name": folder, "item": folders[folder]} for folder in FOLDER_ORDER if folders.get(folder)],
    }
    return collection, request_lookup


def build_curated_collection(spec: dict, request_lookup: dict, filename: str) -> dict:
    definition = CURATED_COLLECTIONS[filename]
    items = []
    for method, path in definition["requests"]:
        operation = spec["paths"][path][method]
        items.append(build_request_item(method, path, operation, curated=True))

    return {
        "info": collection_info(definition["name"], definition["description"]),
        "auth": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{apiKey}}", "type": "string"}],
        },
        "variable": collection_variables(),
        "item": items,
    }


def build_environment() -> dict:
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "sajn:local-environment")),
        "name": "sajn Local",
        "values": [
            {"key": "baseUrl", "value": "https://app.sajn.se", "enabled": True},
            {"key": "uploadBaseUrl", "value": "https://upload.sajn.se", "enabled": True},
            {"key": "apiKey", "value": "", "enabled": True},
            {"key": "documentId", "value": "", "enabled": True},
            {"key": "contactId", "value": "", "enabled": True},
            {"key": "signerId", "value": "", "enabled": True},
            {"key": "fieldId", "value": "", "enabled": True},
            {"key": "tagId", "value": "", "enabled": True},
            {"key": "fileId", "value": "", "enabled": True},
            {"key": "fileKey", "value": "", "enabled": True},
            {"key": "sajnIdId", "value": "", "enabled": True},
            {"key": "signingUrl", "value": "", "enabled": True},
        ],
        "_postman_variable_scope": "environment",
        "_postman_exported_at": "2026-03-06T00:00:00.000Z",
        "_postman_exported_using": "sajn-docs/scripts/generate-postman.py",
    }


def main() -> None:
    openapi = load_openapi()
    reference_collection, request_lookup = build_reference_collection(openapi)

    write_json(OUTPUT_DIR / REFERENCE_FILENAME, reference_collection)
    for filename in CURATED_COLLECTIONS:
        curated_collection = build_curated_collection(openapi, request_lookup, filename)
        write_json(OUTPUT_DIR / filename, curated_collection)
    write_json(OUTPUT_DIR / ENV_FILENAME, build_environment())

    generated = [
        REFERENCE_FILENAME,
        *CURATED_COLLECTIONS.keys(),
        ENV_FILENAME,
    ]
    print("Generated Postman artifacts:")
    for name in generated:
        print(f" - downloads/postman/{name}")


if __name__ == "__main__":
    main()
