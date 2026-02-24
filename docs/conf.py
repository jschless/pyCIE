"""Sphinx configuration for the pyCIE docs site."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

project = "pyCIE Workbook"
author = "pyCIE"
release = "0.1.0"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_design",
    "sphinx_copybutton",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
master_doc = "index"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
templates_path = ["_templates"]

html_theme = "sphinx_book_theme"
html_title = "pyCIE Workbook"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_theme_options = {
    "repository_url": "https://github.com/jschless/pyCIE",
    "use_repository_button": True,
    "use_issues_button": True,
    "path_to_docs": "docs",
    "use_edit_page_button": True,
    "show_navbar_depth": 2,
    "navigation_with_keys": True,
    "home_page_in_toc": True,
}

myst_heading_anchors = 3
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "attrs_block",
    "attrs_inline",
]
