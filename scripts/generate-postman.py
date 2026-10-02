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
DOCS_PATH = ROOT / "docs.json"
OUTPUT_DIR = ROOT / "downloads" / "postman"


REFERENCE_FILENAME = "sajn-api-reference.postman_collection.json"
GETTING_STARTED_FILENAME = "sajn-getting-started.postman_collection.json"
DOCUMENT_LIFECYCLE_FILENAME = "sajn-document-lifecycle.postman_collection.json"
CONTACTS_PARTIES_FILENAME = "sajn-contacts-and-parties.postman_collection.json"
ENV_FILENAME = "sajn-local.postman_environment.json"
API_VERSION = "2026-10"


# Bodies that differ from the spec's example: they chain variables between requests or drop example IDs that would 404.
REQUEST_OVERRIDES = {
    ("post", "/api/v1/documents"): {
        "name": "Anställningsavtal – Kai Lindqvist",
        "type": "SIGNABLE",
        "expiresAt": "2027-03-31T22:00:00.000Z",
        "documentMeta": {
            "subject": "Ditt anställningsavtal från Exempelbolaget AB",
            "message": "Hej Kai! Här är ditt anställningsavtal.",
            "signingMode": "PARALLEL",
            "language": "sv",
        },
        "parties": [
            {
                "name": "Maja Holm",
                "email": "maja.holm@example.com",
                "role": "SIGNER",
                "company": {"name": "Exempelbolaget AB", "orgNumber": "5561234567", "role": "HR-chef"},
                "country": "SE",
                "deliveryMethod": "EMAIL",
                "requiredSignature": "DRAWING",
            }
        ],
    },
    ("post", "/api/v1/documents/{id}/parties"): {
        "contactId": "{{contactId}}",
        "role": "SIGNER",
        "deliveryMethod": "EMAIL",
        "requiredSignature": "DRAWING",
    },
    ("post", "/api/v1/documents/{id}/send"): {
        "customMessage": "Hej! Här är anställningsavtalet. Läs igenom det och signera.",
    },
    ("post", "/api/v1/identity-checks"): {
        "fullName": "Kai Lindqvist",
        "email": "kai@example.com",
        "channel": "EMAIL",
        "reference": "HR-2026-0142",
        "language": "sv",
    },
}


# Variables that test scripts set from responses, as (variable, JavaScript expression over `response`).
CAPTURES = {
    ("post", "/api/v1/contacts"): [("contactId", "response.id")],
    ("get", "/api/v1/contacts"): [("contactId", "response.data && response.data[0] && response.data[0].id")],
    ("post", "/api/v1/documents"): [
        ("documentId", "response.id"),
        ("partyId", "response.parties && response.parties[0] && response.parties[0].id"),
    ],
    ("post", "/api/v1/documents/{id}/parties"): [("partyId", "response.id")],
    ("get", "/api/v1/documents/{id}/parties/{partyId}"): [("signingUrl", "response.signingUrl")],
    ("post", "/api/v1/identity-checks"): [("identityCheckId", "response.id")],
    ("post", "/api/v1/files"): [("fileId", "response.id")],
    ("post", "/api/v1/approval-requests"): [("approvalRequestId", "response.id")],
}
CAPTURED_VARIABLES = {variable for captures in CAPTURES.values() for variable, _ in captures}


# Each request is (method, path) or (method, path, enabled query parameters).
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
        "description": "Create a contact and a document, add the contact as a party, send the document, get the signing URL, and get the signed PDF.",
        "requests": [
            ("post", "/api/v1/contacts"),
            ("post", "/api/v1/documents"),
            ("post", "/api/v1/documents/{id}/parties"),
            ("post", "/api/v1/documents/{id}/send"),
            ("get", "/api/v1/documents/{id}/parties/{partyId}"),
            ("get", "/api/v1/documents/{id}/files/{type}"),
        ],
    },
    CONTACTS_PARTIES_FILENAME: {
        "name": "sajn Contacts and Parties",
        "description": "Create a contact, find it by email, update it, and add it to a document as a party.",
        "requests": [
            ("post", "/api/v1/contacts"),
            ("get", "/api/v1/contacts", {"email": "kai@example.com"}),
            ("patch", "/api/v1/contacts/{id}"),
            ("post", "/api/v1/documents"),
            ("post", "/api/v1/documents/{id}/parties"),
            ("get", "/api/v1/documents/{id}/parties/{partyId}"),
        ],
    },
}


def load_json(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def endpoint_groups() -> list[tuple[str, list[str]]]:
    """The 2026-10 API reference groups in docs.json, so the reference collection mirrors the sidebar."""
    docs = load_json(DOCS_PATH)
    tab = next(tab for tab in docs["navigation"]["tabs"] if tab["tab"] == "API")
    dropdown = next(dropdown for dropdown in tab["dropdowns"] if dropdown["dropdown"] == API_VERSION)
    reference = next(group for group in dropdown["groups"] if group["group"] == "API reference")

    def flatten(pages: list) -> list[str]:
        return [entry for page in pages for entry in ([page] if isinstance(page, str) else flatten(page["pages"]))]

    return [(group["group"], flatten(group["pages"])) for group in reference["pages"]]


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
    # OpenAPI 3.1 spells a nullable field as a type array, such as ["string", "null"].
    if isinstance(schema_type, list):
        schema_type = next((entry for entry in schema_type if entry != "null"), None)
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
            return "2026-12-31T12:00:00Z"
        if fmt == "date":
            return "2026-12-31"
        if fmt == "email":
            return "kai@example.com"
        if fmt == "uri":
            return "https://example.com/callback"
        return ""
    if schema_type in {"number", "integer"}:
        minimum = schema.get("minimum")
        return minimum if minimum is not None else 1
    if schema_type == "boolean":
        return True
    return {}


def resolve_request_body(method: str, path: str, operation: dict) -> dict | None:
    content = operation.get("requestBody", {}).get("content", {}).get("application/json")
    if content is None:
        return None

    body = REQUEST_OVERRIDES.get((method, path))
    if body is None:
        body = deepcopy(content["example"]) if "example" in content else schema_to_example(content.get("schema"))
        # Point example IDs at the variables that earlier requests capture.
        if isinstance(body, dict):
            body.update({key: f"{{{{{key}}}}}" for key in body if key in CAPTURED_VARIABLES})
    return {
        "mode": "raw",
        "raw": json.dumps(body, indent=2, ensure_ascii=False),
        "options": {"raw": {"language": "json"}},
    }


def query_value(value: object) -> str:
    if isinstance(value, list):
        return ",".join(query_value(entry) for entry in value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return "" if value == {} else str(value)


def variable_name_for(path: str, parameter: str) -> str:
    if parameter == "type":
        return "fileType"
    if parameter != "id":
        return parameter
    # `{id}` names the resource before it: /identity-checks/{id} -> identityCheckId.
    resource = path.split("/{id}")[0].rsplit("/", 1)[-1]
    resource = resource[:-3] + "y" if resource.endswith("ies") else resource.removesuffix("s")
    return re.sub(r"-(\w)", lambda match: match.group(1).upper(), resource) + "Id"


def build_url(path: str, operation: dict, enabled_query: dict) -> dict:
    raw_path = re.sub(r"\{([^}]+)\}", lambda match: "{{" + variable_name_for(path, match.group(1)) + "}}", path)
    query = [
        {
            "key": parameter["name"],
            "value": enabled_query.get(parameter["name"], query_value(schema_to_example(parameter.get("schema")))),
            "description": parameter.get("description", ""),
            "disabled": parameter["name"] not in enabled_query,
        }
        for parameter in operation.get("parameters", [])
        if parameter.get("in") == "query"
    ]
    query_string = "&".join(f"{entry['key']}={entry['value']}" for entry in query if not entry["disabled"])
    url = {
        "raw": "{{baseUrl}}" + raw_path + (f"?{query_string}" if query_string else ""),
        "host": ["{{baseUrl}}"],
        "path": raw_path.strip("/").split("/"),
    }
    if query:
        url["query"] = query
    return url


def build_headers(operation: dict, body: dict | None) -> list[dict]:
    # Pinned so the collections keep working when the API releases a new version.
    headers = [{"key": "Sajn-Version", "value": "{{apiVersion}}"}]
    if body:
        headers.append({"key": "Content-Type", "value": "application/json"})
    if any(parameter["name"] == "Idempotency-Key" for parameter in operation.get("parameters", [])):
        headers.append({"key": "Idempotency-Key", "value": "{{$guid}}", "disabled": True})
    return headers


def success_status(operation: dict) -> int:
    for code in operation.get("responses", {}):
        if code.isdigit() and 200 <= int(code) < 300:
            return int(code)
    return 200


def test_script(method: str, path: str, operation: dict, curated: bool) -> list[str]:
    lines = []
    if curated:
        status = success_status(operation)
        lines.extend(
            [
                f"pm.test('Status code is {status}', function () {{",
                f"  pm.response.to.have.status({status});",
                "});",
            ]
        )

    captures = CAPTURES.get((method, path))
    if captures:
        lines.extend(
            [
                "var response = {};",
                "try { response = pm.response.json(); } catch (error) {}",
                "var save = function (key, value) {",
                "  if (!value) { return; }",
                "  pm.collectionVariables.set(key, value);",
                "  if (pm.environment.name) { pm.environment.set(key, value); }",
                "};",
                *(f"save('{variable}', {expression});" for variable, expression in captures),
            ]
        )
    return lines


def build_request_item(method: str, path: str, operation: dict, curated: bool = False, enabled_query: dict | None = None) -> dict:
    body = resolve_request_body(method, path, operation)
    item = {
        "name": operation.get("summary") or f"{method.upper()} {path}",
        "request": {
            "method": method.upper(),
            "header": build_headers(operation, body),
            "url": build_url(path, operation, enabled_query or {}),
            "description": operation.get("description") or operation.get("summary", ""),
        },
        "response": [],
    }

    if body:
        item["request"]["body"] = body

    if operation.get("security") == []:
        item["request"]["auth"] = {"type": "noauth"}

    script = test_script(method, path, operation, curated)
    if script:
        item["event"] = [{"listen": "test", "script": {"type": "text/javascript", "exec": script}}]

    return item


def variables_in(collection: dict) -> list[str]:
    # Descriptions are skipped: they show sajn's own {{variable}} template syntax.
    def requests(items: list[dict]) -> list[dict]:
        return [entry for item in items for entry in (requests(item["item"]) if "item" in item else [item])]

    text = json.dumps([({**item["request"], "description": ""}, item.get("event")) for item in requests(collection["item"])])
    found = set(re.findall(r"\{\{(\w+)\}\}|save\('(\w+)'", text))
    found = {name for pair in found for name in pair if name} - {"baseUrl", "apiKey", "apiVersion"}
    return ["baseUrl", "apiKey", "apiVersion", *sorted(found)]


def default_value(variable: str) -> str:
    return {"baseUrl": "https://app.sajn.se", "apiVersion": API_VERSION, "fileType": "SIGNED"}.get(variable, "")


def build_collection(name: str, description: str, items: list[dict]) -> dict:
    collection = {
        "info": {
            "_postman_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"sajn:{name}")),
            "name": name,
            "description": description,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "auth": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{apiKey}}", "type": "string"}],
        },
        "item": items,
    }
    collection["variable"] = [{"key": key, "value": default_value(key)} for key in variables_in(collection)]
    return collection


def build_reference_collection(openapi: dict) -> dict:
    operations = {f"{method.upper()} {path}": (method, path) for path, item in openapi["paths"].items() for method in item}
    folders = []
    for group, pages in endpoint_groups():
        items = [
            build_request_item(method, path, openapi["paths"][path][method])
            for method, path in (operations.pop(page) for page in pages if page in operations)
        ]
        if items:
            folders.append({"name": group, "item": items})
    if operations:
        folders.append({"name": "Other", "item": [build_request_item(method, path, openapi["paths"][path][method]) for method, path in operations.values()]})

    return build_collection(
        "sajn API Reference",
        "Every sajn API endpoint, generated from the OpenAPI specification and grouped like the API reference.",
        folders,
    )


def build_curated_collection(openapi: dict, filename: str) -> dict:
    definition = CURATED_COLLECTIONS[filename]
    items = [
        build_request_item(method, path, openapi["paths"][path][method], curated=True, enabled_query=query[0] if query else None)
        for method, path, *query in definition["requests"]
    ]
    return build_collection(definition["name"], definition["description"], items)


def build_environment(collections: list[dict]) -> dict:
    variables = []
    for collection in collections:
        variables.extend(key for key in variables_in(collection) if key not in variables)
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "sajn:local-environment")),
        "name": "sajn Local",
        "values": [{"key": key, "value": default_value(key), "enabled": True} for key in variables],
        "_postman_variable_scope": "environment",
        "_postman_exported_at": "2026-10-01T00:00:00.000Z",
        "_postman_exported_using": "sajn-docs/scripts/generate-postman.py",
    }


def main() -> None:
    openapi = load_json(OPENAPI_PATH)
    collections = {REFERENCE_FILENAME: build_reference_collection(openapi)}
    for filename in CURATED_COLLECTIONS:
        collections[filename] = build_curated_collection(openapi, filename)

    for filename, collection in collections.items():
        write_json(OUTPUT_DIR / filename, collection)
    write_json(OUTPUT_DIR / ENV_FILENAME, build_environment(list(collections.values())))

    print("Generated Postman artifacts:")
    for name in [*collections, ENV_FILENAME]:
        print(f" - downloads/postman/{name}")


if __name__ == "__main__":
    main()
