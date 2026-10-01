"""Rebuild the API tab of docs.json as a version switcher, and mark deprecated specs.

Run from the repo root after replacing api/openapi.json (latest). Idempotent: the developer pages come
from GUIDE_GROUPS, the endpoint groups from origin/main's API tab, and the deprecation notice is
rewritten, not appended.
"""
import json
import re
import subprocess

LEGACY_SPEC = "api/openapi-2026-09.json"
LEGACY_NOTICE = (
    "<Warning>You're viewing API version `2026-09`, which is deprecated and stops working on "
    "October 1, 2027. To see the current version, select **2026-10** in the menu at the top of the sidebar. "
    "To move your integration, see [Upgrading to 2026-10](/upgrading/2026-10).</Warning>"
)

ENDPOINT = re.compile(r"^(GET|POST|PUT|PATCH|DELETE) ")
# The hand-written developer pages of the 2026-10 dropdown, in sidebar order. The generated endpoint
# groups follow, nested under "API reference" so their names don't collide with these.
GUIDE_GROUPS = [
    {"group": "Get started", "pages": [
        "get-started/introduction",
        "get-started/quickstart",
        "get-started/authentication",
        "get-started/choosing-authentication",
        "get-started/sandbox",
        "get-started/postman",
        {"group": "Build with AI", "pages": ["ai/overview", "ai/docs-mcp", "ai/workspace-mcp"]},
    ]},
    {"group": "Core concepts", "pages": [
        "concepts/organizations",
        "concepts/workspaces",
        "concepts/documents",
        "concepts/parties",
        "concepts/fields",
        "concepts/templates-and-forms",
        "concepts/contacts",
        "concepts/signing-methods",
        "concepts/signing-certificate",
        "concepts/sajn-id",
        "concepts/activity-events",
        "concepts/glossary",
    ]},
    {"group": "Guides", "pages": [
        {"group": "Documents", "pages": [
            "guides/documents/create-document",
            "guides/documents/send-for-signing",
            "guides/documents/multi-party-signing",
            "guides/documents/reminders-expiration",
            "guides/documents/redirect-url",
            "guides/documents/downloading-documents",
            "guides/documents/file-uploads",
            "guides/documents/organizing-with-tags",
            "guides/documents/onboarding-signing-flow",
        ]},
        {"group": "Fields and data", "pages": [
            "guides/fields/signer-fields",
            "guides/fields/pdf-field-placement",
            "guides/fields/html-fields",
            "guides/fields/formatting-html-content",
            "guides/fields/product-tables",
            "guides/fields/custom-fields",
        ]},
        {"group": "Templates and forms", "pages": [
            "guides/templates/templates-and-forms",
            "guides/templates/managing-templates",
            "guides/templates/managing-forms",
        ]},
        {"group": "Contacts and companies", "pages": [
            "guides/contacts/managing-contacts",
            "guides/contacts/working-with-companies",
        ]},
        {"group": "Identity and signing", "pages": [
            "guides/identity/identity-verification",
            "guides/identity/signing-methods",
        ]},
        {"group": "Embedding", "pages": [
            "guides/embedding/overview",
            "guides/embedding/vanilla-js",
            "guides/embedding/react",
            "guides/embedding/vue",
        ]},
        {"group": "Sync and integrations", "pages": [
            "guides/integrations/syncing-documents",
            "guides/integrations/crm-field-integration",
        ]},
        {"group": "Recipes", "pages": [
            "guides/recipes/crm-contract-notifications",
            "guides/recipes/bulk-from-template",
            "guides/recipes/embed-signing",
            "guides/recipes/nightly-sync",
            "guides/recipes/verify-identity-before-signing",
        ]},
    ]},
    {"group": "Webhooks", "pages": [
        "webhooks/overview",
        "webhooks/manage-endpoints",
        "webhooks/events",
        "webhooks/payloads",
        "webhooks/verify-signatures",
        "webhooks/delivery-and-retries",
        "webhooks/replay-and-reconcile",
        "webhooks/testing",
    ]},
    {"group": "API fundamentals", "pages": [
        "api-fundamentals/versioning",
        "api-fundamentals/errors",
        "api-fundamentals/pagination",
        "api-fundamentals/rate-limits",
        "api-fundamentals/idempotency",
        "api-fundamentals/query-parameters",
        "api-fundamentals/oauth",
    ]},
    {"group": "Upgrading", "pages": [
        "upgrading/2026-10",
        "upgrading/changelog",
        "upgrading/migrate-signers-to-parties",
    ]},
    {"group": "sajn Login", "pages": [
        "login/overview",
        "login/quickstart",
        "login/oidc",
        "login/session-api",
        "login/claims",
        "login/testing",
        "login/webhooks",
        "login/errors",
    ]},
]


def pages(groups):
    for item in groups:
        if isinstance(item, str):
            yield item
        else:
            yield from pages(item["pages"])


def lenient(text):
    return json.loads(re.sub(r",(\s*[\]}])", r"\1", text))


def operations(path):
    spec = json.load(open(path))
    return {f"{method.upper()} {p}" for p, item in spec["paths"].items() for method in item}


# One page per webhook in the spec's `webhooks` map, grouped the way sajn-app groups each event.
def webhook_groups(path):
    groups = {}
    for event, item in json.load(open(path)).get("webhooks", {}).items():
        groups.setdefault(item["post"]["x-sajn-webhook-group"], []).append(f"webhook {event}")
    return [{"group": group, "pages": events} for group, events in groups.items()]


def endpoint_groups(groups, ops):
    result = []
    for group in groups:
        pages = [p for p in group["pages"] if isinstance(p, str) and ENDPOINT.match(p) and p in ops]
        if pages:
            result.append({**group, "pages": pages})
    return result


base = lenient(subprocess.check_output(["git", "show", "origin/main:docs.json"], text=True))
base_tab = next(t for t in base["navigation"]["tabs"] if t["tab"] == "API")
base_groups = base_tab["groups"]

latest_ops = operations("api/openapi.json")
legacy_ops = operations(LEGACY_SPEC)

# Only the x-mint page content changes; the frozen contract itself is never touched.
legacy_spec = json.load(open(LEGACY_SPEC))
for item in legacy_spec["paths"].values():
    for operation in item.values():
        operation["x-mint"] = {**operation.get("x-mint", {}), "content": LEGACY_NOTICE}
open(LEGACY_SPEC, "w").write(json.dumps(legacy_spec, indent=2, ensure_ascii=False) + "\n")

api_groups = [g for g in base_groups if any(isinstance(p, str) and ENDPOINT.match(p) for p in g["pages"])]

latest_groups = GUIDE_GROUPS + [{"group": "API reference", "pages": [
    *endpoint_groups(api_groups, latest_ops),
    {"group": "Webhook events", "pages": webhook_groups("api/openapi.json")},
]}]
# A page shared with another dropdown makes Mintlify snap back to that dropdown, so 2026-09 lists only its own pages.
legacy_groups = [{"group": "Overview", "pages": ["api-reference/version-2026-09"]}] + [
    {**group, "pages": [f"{LEGACY_SPEC} {page}" for page in group["pages"]]}
    for group in endpoint_groups(api_groups, legacy_ops)
]

docs = lenient(open("docs.json").read())
tab = next(t for t in docs["navigation"]["tabs"] if t["tab"] == "API")
tab.clear()
tab.update({
    "tab": "API",
    # Dropdowns sit at the top of the sidebar; `versions` would render in the header.
    "dropdowns": [
        {
            "dropdown": "2026-10",
            "description": "Latest",
            "icon": "circle-check",
            "openapi": "api/openapi.json",
            "groups": latest_groups,
        },
        {
            "dropdown": "2026-09",
            "description": "Deprecated",
            "icon": "box-archive",
            "color": {"light": "#6B7280", "dark": "#9CA3AF"},
            "openapi": {"source": LEGACY_SPEC, "directory": "api-reference/2026-09"},
            "groups": legacy_groups,
        },
    ],
})

open("docs.json", "w").write(json.dumps(docs, indent=2, ensure_ascii=False) + "\n")

for name, groups, ops in (("2026-10", latest_groups, latest_ops), ("2026-09", legacy_groups, legacy_ops)):
    listed = {p.removeprefix(f"{LEGACY_SPEC} ") for p in pages(groups) if ENDPOINT.match(p.removeprefix(f"{LEGACY_SPEC} "))}
    print(f"{name}: {len(listed)} endpoints in nav, unlisted in spec: {sorted(ops - listed)}")
