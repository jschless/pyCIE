# Docs Site and GitHub Pages

This repository uses MkDocs to render documentation as a navigable site.

## Local preview

```bash
pip install -e '.[docs]'
mkdocs serve
```

With `Makefile` shortcuts:

```bash
make docs-install
make docs-serve
```

Open the local URL printed by MkDocs (typically `http://127.0.0.1:8000`).

## Strict build

```bash
mkdocs build --strict
```

or:

```bash
make docs-build
```

Use strict mode before opening a PR to catch broken links and bad nav references.

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

## Sphinx alternative

If you later want full API autodoc and tighter Python-domain directives, you can migrate this structure to Sphinx.

Suggested migration path:

1. Keep chapter markdown under `docs/tutorial/`.
2. Use MyST in Sphinx to preserve markdown sources.
3. Move CI workflow from `mkdocs build --strict` to `sphinx-build -W`.
