# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Mintlify documentation site for sajn, a digital document signing platform. The documentation includes guides, API references, and changelogs organized in a multi-tab structure.

## Local Development Commands

### Preview Documentation Locally
```bash
# Install Mintlify CLI globally (first time only)
npm i -g mint

# Start the local development server
mint dev
```
The preview will be available at `http://localhost:3000` and updates automatically as you edit files.

### Update CLI (troubleshooting)
```bash
mint update
```

## Project Structure

- **docs.json**: Central configuration file defining navigation, theme, colors, and OpenAPI integration
- **api/openapi.json**: OpenAPI specification that auto-generates API documentation pages. **Generated from the `sajn-app` contract — never hand-edit** (see [OpenAPI Integration](#openapi-integration))
- **MDX files**: Documentation content with YAML frontmatter and Mintlify components
- **Key directories**:
  - `api/`: API documentation and OpenAPI spec
  - `concepts/`, `guides/`: Conceptual and procedural documentation (referenced in docs.json but files may need creation)
  - `essentials/`: General Mintlify documentation templates
  - `changelog/`: Version history
  - `snippets/`: Reusable content blocks
  - `images/`, `logo/`: Media assets

## Navigation Architecture

The site uses a **tab-based navigation** defined in docs.json:

1. **Documentation tab**: Getting Started, Core Concepts, Guides
2. **API Reference tab**: Auto-generated from OpenAPI spec with custom groupings
3. **Changelog tab**: Version history

Navigation is controlled entirely through docs.json. When adding new pages:
1. Create the MDX file with proper frontmatter
2. Add the file path (without `.mdx` extension) to the appropriate `pages` array in docs.json
3. For API endpoints, they're auto-generated from openapi.json but must be listed in docs.json navigation

## Content Requirements

### MDX File Frontmatter (Required)
Every MDX file must include:
```yaml
---
title: "Page Title"
description: "Concise description for SEO and navigation"
---
```

### Writing Standards
- Use second-person voice ("you")
- Include prerequisites at the start of procedural content
- Test all code examples before committing
- Add language tags to all code blocks
- Use relative paths for internal links (e.g., `/quickstart` not absolute URLs)
- Match style and formatting of existing pages

### Mintlify Components
The site uses Mintlify-specific MDX components:
- `<Card>`, `<CardGroup>`: Visual navigation cards
- `<Accordion>`, `<AccordionGroup>`: Collapsible content
- `<Tip>`, `<Note>`, `<Warning>`: Callout boxes
- `<Columns>`: Multi-column layouts

## OpenAPI Integration

The API Reference tab is powered by `api/openapi.json`.

> **`api/openapi.json` is GENERATED — never hand-edit it.** It is built from the
> ts-rest contract in the **`sajn-app`** repo (`lib/api/v1/{contract,schema,openapi}.ts`).
> Any manual edit is silently overwritten on the next regeneration, and in the
> meantime the reference documents an API that doesn't exist.

When the API changes:
1. Change the contract in `sajn-app` (`lib/api/v1/contract.ts` + `schema.ts`), then regenerate
   into this repo from the `sajn-app` checkout:
   ```bash
   cd ../sajn-app && pnpm generate:openapi:v1 ../sajn-docs/api/openapi.json
   ```
   (`SKIP_MINTLIFY_VALIDATION=1` skips the Mintlify CLI step if it isn't installed.)
2. Ensure endpoint paths match the navigation structure in docs.json
3. The format uses HTTP method + path (e.g., `"GET /api/v1/documents"`) in the navigation

The generator deliberately injects one path that is **not** in the ts-rest contract:
`/api/v1/putFile`, the direct upload against `upload.sajn.se`. It is not drift — don't
"clean" it out.

Hand-written `.mdx` pages (guides, concepts) are the opposite: those are the source of
truth and are edited here.

## Git Workflow

- **NEVER use `--no-verify`** when committing
- Create a new branch for changes when appropriate
- Commit frequently throughout development
- Changes pushed to the default branch (main) are automatically deployed to production via Mintlify's GitHub app

## Deployment

The site is deployed automatically through the Mintlify GitHub app. After pushing to the main branch, changes propagate to production within moments. No manual deployment steps required.

## Bilingual Content Note

Some content (particularly API reference introduction) is in Swedish. Maintain language consistency when editing existing pages - don't translate unless explicitly requested.
