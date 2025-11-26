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
- **api/openapi.json**: OpenAPI specification that auto-generates API documentation pages
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

The API Reference tab is powered by `api/openapi.json`. When updating the API:
1. Modify the OpenAPI spec in openapi.json
2. Ensure endpoint paths match the navigation structure in docs.json
3. The format uses HTTP method + path (e.g., `"GET /api/v1/documents"`) in the navigation

## Git Workflow

- **NEVER use `--no-verify`** when committing
- Create a new branch for changes when appropriate
- Commit frequently throughout development
- Changes pushed to the default branch (main) are automatically deployed to production via Mintlify's GitHub app

## Deployment

The site is deployed automatically through the Mintlify GitHub app. After pushing to the main branch, changes propagate to production within moments. No manual deployment steps required.

## Bilingual Content Note

Some content (particularly API reference introduction) is in Swedish. Maintain language consistency when editing existing pages - don't translate unless explicitly requested.
