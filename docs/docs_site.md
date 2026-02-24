# Docs Site and GitHub Pages

This repository uses Sphinx + MyST to render documentation as a navigable textbook-style site.

## Local preview

```bash
pip install -e '.[docs]'
sphinx-autobuild docs docs/_build/dirhtml
```

With `Makefile` shortcuts:

```bash
make docs-install
make docs-serve
```

Open the local URL printed by Sphinx Autobuild (typically `http://127.0.0.1:8000`).

## Strict build

```bash
sphinx-build -W -b dirhtml docs docs/_build/dirhtml
```

or:

```bash
make docs-build
```

Use `-W` before opening a PR so warnings fail the build (broken links, unresolved refs, and nav issues).

## GitHub Pages deployment

Workflow: `.github/workflows/docs.yml`

Behavior:

- Pull requests: build docs only
- Push to `main`: build docs and deploy to GitHub Pages

## Textbook authoring model

- Keep chapter content under `docs/tutorial/`
- Keep command-level reference under `docs/usage.md`
- Keep architecture and standards as supporting references
- Link each chapter to specific lab IDs and expected outcomes

## Core Sphinx files

- `docs/conf.py`: theme/extensions/options
- `docs/index.md`: landing page + site toctree
- `docs/tutorial/index.md`: chapter map + tutorial toctree

## Why this stack

- MyST keeps markdown authoring simple.
- Sphinx gives durable cross-references and warning-strict builds.
- Book theme provides chapter navigation and textbook ergonomics.
