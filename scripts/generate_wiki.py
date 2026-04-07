#!/usr/bin/env python3
"""
generate_wiki.py — Generate theme-based wiki pages from catalog.json.

Each page corresponds to a theme cluster (derived from the themes arrays on
catalog entries) and lists the entries that belong to it, with their
synopses and cross-references via `in_conversation_with`.

This is deliberately honest rather than essayistic: the generator doesn't
invent prose, it organizes what's already in the catalog. If you want
essay-length synthesis for a particular theme, hand-edit the generated page
(wiki/ is gitignored, so your edits stay local) or write your own
page in a separate tool.

Usage:
    python3 scripts/generate_wiki.py
"""


from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "catalog.json"
WIKI_DIR = REPO_ROOT / "wiki"

# Import config + clustering from regenerate.py so wiki and context tiers
# agree on how the catalog is grouped.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from regenerate import (  # noqa: E402
    load_config,
    load_catalog,
    derive_clusters,
    get_media_type,
    get_creator,
    MISC_CLUSTER_NAME,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slug(title: str) -> str:
    """Convert a display title to a filename-safe slug."""
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-") or "page"


def format_entry_line(entry: dict) -> str:
    """One-line bullet for an entry: title, creator, year, media type."""
    title = entry.get("title", "").strip()
    creator = get_creator(entry)
    year = entry.get("year")
    mt = get_media_type(entry)
    tag = f"[{mt}] " if mt != "book" else ""

    parts = [f"**{title}**"]
    if creator:
        parts[0] += f" — {creator}"
    if year:
        parts[0] += f" ({year})"
    return f"- {tag}{parts[0]}"


def format_entry_block(entry: dict, all_titles: set[str]) -> list[str]:
    """Multi-line block for an entry: title/creator/year, synopsis, cross-refs."""
    lines = [format_entry_line(entry)]

    synopsis = (entry.get("synopsis") or "").strip()
    if synopsis:
        lines.append(f"  {synopsis}")

    # Only surface cross-refs that point to other entries actually in the catalog
    conns = [c for c in (entry.get("in_conversation_with") or []) if c in all_titles]
    if conns:
        lines.append(f"  *In conversation with:* {', '.join(conns)}")

    return lines


# ---------------------------------------------------------------------------
# Page generation
# ---------------------------------------------------------------------------

def make_cluster_page(
    label: str,
    entries: list[dict],
    all_titles: set[str],
) -> tuple[str, str, str]:
    """Build a wiki page for a single cluster. Returns (title, filename, content)."""
    count = len(entries)
    noun = "entry" if count == 1 else "entries"

    md = [
        f"# {label}",
        "",
        f"*{count} {noun} in this cluster.*",
        "",
    ]

    for entry in entries:
        md.extend(format_entry_block(entry, all_titles))
        md.append("")

    return label, slug(label) + ".md", "\n".join(md).rstrip() + "\n"


def make_index_page(
    pages: list[tuple[str, str, str]],
    config: dict,
    total_entries: int,
) -> str:
    """Build the wiki INDEX.md linking all cluster pages."""
    lines = [
        f"# {config['collection_name']} — Wiki Index",
        "",
        f"*Theme-based cluster pages auto-generated from `catalog.json` "
        f"({total_entries} total entries across {len(pages)} clusters).*",
        "",
        "Each page lists the catalog entries belonging to a theme cluster, "
        "with their synopses and cross-references. Edit pages by hand if you "
        "want deeper synthesis — the `wiki/` directory is gitignored so local "
        "edits stay local.",
        "",
        "---",
        "",
    ]

    # Sort: largest cluster first, Miscellaneous last
    def sort_key(item: tuple[str, str, str]) -> tuple[int, int, str]:
        title, _, content = item
        # Count bullet-list entries by looking for top-level "- " at line start
        count = sum(1 for line in content.splitlines() if line.startswith("- "))
        is_misc = 1 if title == MISC_CLUSTER_NAME else 0
        return (is_misc, -count, title.lower())

    for title, filename, content in sorted(pages, key=sort_key):
        count = sum(1 for line in content.splitlines() if line.startswith("- "))
        noun = "entry" if count == 1 else "entries"
        lines.append(f"- [{title}]({filename}) — {count} {noun}")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_wiki() -> list[tuple[str, str, str]]:
    """Generate all wiki pages and INDEX.md. Returns list of (title, filename, content)."""
    catalog = load_catalog()
    config = load_config()
    cluster_order, buckets = derive_clusters(
        catalog, min_size=int(config.get("cluster_min_size", 2))
    )

    all_titles = {e["title"] for e in catalog}

    WIKI_DIR.mkdir(exist_ok=True)

    pages = []
    for label in cluster_order:
        entries = buckets.get(label, [])
        if not entries:
            continue
        pages.append(make_cluster_page(label, entries, all_titles))

    # Write pages
    for _title, filename, content in pages:
        (WIKI_DIR / filename).write_text(content)

    # Write index
    (WIKI_DIR / "INDEX.md").write_text(make_index_page(pages, config, len(catalog)))

    return pages


if __name__ == "__main__":
    pages = generate_wiki()
    print(f"Generated {len(pages)} wiki pages + INDEX.md in wiki/\n")
    for title, filename, content in pages:
        size = len(content)
        n_lines = content.count("\n")
        print(f"  {filename:45s} {size:>6d} bytes  ({n_lines} lines)")

    index_path = WIKI_DIR / "INDEX.md"
    index_size = index_path.stat().st_size
    print(f"\n  {'INDEX.md':45s} {index_size:>6d} bytes")
