#!/usr/bin/env python3
"""
generate_wiki.py — Generate per-book wiki pages and theme cluster pages
from catalog.json, with Obsidian wikilinks throughout so the graph view
actually traces the connections in the catalog.

Layout:
    wiki/
        INDEX.md                — top-level index
        <theme-slug>.md         — one cluster page per qualifying theme
        books/<book-slug>.md    — one page per catalog entry

Each book appears on EVERY cluster page whose theme it qualifies for, so
the graph view in Obsidian shows a real web instead of a star. Cluster
pages and book pages cross-link via Obsidian [[wikilinks]], and every
in_conversation_with reference is rendered as a clickable wikilink to
the target book page.

This is deliberately honest rather than essayistic: the generator
organizes what's already in the catalog, it doesn't invent prose.

Usage:
    python3 scripts/generate_wiki.py
"""


from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "catalog.json"
WIKI_DIR = REPO_ROOT / "wiki"
BOOKS_DIR = WIKI_DIR / "books"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from regenerate import (  # noqa: E402
    load_config,
    load_catalog,
    get_media_type,
    get_creator,
    _normalize_theme,
    _display_theme,
    MISC_CLUSTER_NAME,
)


# ---------------------------------------------------------------------------
# Slugs
# ---------------------------------------------------------------------------

def slug(s: str) -> str:
    """Convert a string to a filename-safe slug."""
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-") or "page"


def book_slug(title: str) -> str:
    return slug(title)


def cluster_slug(label: str) -> str:
    return slug(label)


def book_link(title: str) -> str:
    """Wikilink to a book page (relative to wiki/)."""
    return f"[[books/{book_slug(title)}|{title}]]"


def cluster_link(label: str) -> str:
    """Wikilink to a cluster page (relative to wiki/)."""
    return f"[[{cluster_slug(label)}|{label}]]"


# ---------------------------------------------------------------------------
# Multi-cluster assignment
#
# Unlike regenerate.py's derive_clusters (which assigns each entry to its
# single most-specific theme), this script puts each entry on EVERY cluster
# page whose theme it qualifies for. This is what produces the graph-view
# web Sean wants in Obsidian.
# ---------------------------------------------------------------------------

def derive_multi_clusters(
    catalog: list[dict], min_size: int
) -> tuple[list[str], dict[str, list[dict]], dict[str, list[str]]]:
    """Assign each entry to all clusters it qualifies for.

    Returns:
        cluster_order: list of cluster display labels, largest first,
                       Miscellaneous always last (if non-empty).
        buckets:       label -> list of entries belonging to that cluster.
        entry_themes:  entry title -> list of cluster display labels the
                       entry was placed in (used to render theme wikilinks
                       on each book page).
    """
    # 1) Count theme frequencies (one per entry, deduped within entry)
    theme_counts: Counter[str] = Counter()
    for entry in catalog:
        seen = set()
        for t in entry.get("themes", []):
            n = _normalize_theme(t)
            if n and n not in seen:
                theme_counts[n] += 1
                seen.add(n)

    qualifying = {t for t, c in theme_counts.items() if c >= min_size}

    # 2) Assign each entry to ALL of its qualifying themes
    buckets_norm: dict[str, list[dict]] = {}
    entry_clusters: dict[str, list[str]] = {}
    for entry in catalog:
        entry_themes_norm = []
        seen = set()
        for t in entry.get("themes", []):
            n = _normalize_theme(t)
            if n and n not in seen:
                entry_themes_norm.append(n)
                seen.add(n)

        qual = [t for t in entry_themes_norm if t in qualifying]
        if qual:
            for t in qual:
                buckets_norm.setdefault(t, []).append(entry)
            entry_clusters[entry["title"]] = [_display_theme(t) for t in qual]
        else:
            buckets_norm.setdefault(None, []).append(entry)
            entry_clusters[entry["title"]] = []

    # 3) Convert internal keys to display labels
    type_order = {"book": 0, "film": 1, "music": 2}
    buckets: dict[str, list[dict]] = {}
    for key, entries in buckets_norm.items():
        label = MISC_CLUSTER_NAME if key is None else _display_theme(key)
        buckets.setdefault(label, []).extend(entries)
    for label in buckets:
        buckets[label].sort(key=lambda e: (
            type_order.get(get_media_type(e), 9),
            e.get("title", "").lower(),
        ))

    # 4) Order: largest first, Miscellaneous last
    named = [(label, len(entries)) for label, entries in buckets.items()
             if label != MISC_CLUSTER_NAME]
    named.sort(key=lambda x: (-x[1], x[0]))
    cluster_order = [label for label, _ in named]
    if MISC_CLUSTER_NAME in buckets:
        cluster_order.append(MISC_CLUSTER_NAME)

    return cluster_order, buckets, entry_clusters


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def yaml_list(items: list[str]) -> str:
    """Render a list as YAML frontmatter inline-list."""
    if not items:
        return "[]"
    escaped = [f'"{i.replace(chr(34), chr(92) + chr(34))}"' for i in items]
    return "[" + ", ".join(escaped) + "]"


def yaml_string(s: str | None) -> str:
    if s is None:
        return "null"
    return '"' + str(s).replace('"', '\\"') + '"'


def make_book_page(
    entry: dict,
    title_to_clusters: dict[str, list[str]],
    all_titles: set[str],
) -> tuple[str, str, str]:
    """Build one wiki page for a single catalog entry."""
    title = entry.get("title", "").strip()
    creator = get_creator(entry)
    year = entry.get("year")
    publisher = entry.get("publisher")
    synopsis = (entry.get("synopsis") or "").strip()
    themes = entry.get("themes") or []
    conns = entry.get("in_conversation_with") or []
    contributors = entry.get("contributors") or []
    mt = get_media_type(entry)
    confidence = entry.get("confidence", "")
    needs_review = entry.get("needs_review", False)
    source_image = entry.get("source_image", "")

    clusters = title_to_clusters.get(title, [])

    fm = ["---"]
    fm.append(f"title: {yaml_string(title)}")
    fm.append(f"type: {mt}")
    if creator:
        creator_field = "author" if mt == "book" else ("director" if mt == "film" else "artist")
        fm.append(f"{creator_field}: {yaml_string(creator)}")
    if year:
        fm.append(f"year: {year}")
    if publisher:
        fm.append(f"publisher: {yaml_string(publisher)}")
    if contributors:
        fm.append(f"contributors: {yaml_list(contributors)}")
    fm.append(f"themes: {yaml_list(themes)}")
    fm.append(f"clusters: {yaml_list(clusters)}")
    if confidence:
        fm.append(f"confidence: {yaml_string(confidence)}")
    if needs_review:
        fm.append("needs_review: true")
    if source_image:
        fm.append(f"source_image: {yaml_string(source_image)}")
    fm.append("---")

    body = ["", f"# {title}", ""]

    byline_bits = []
    if creator:
        byline_bits.append(f"*by {creator}*")
    if year:
        byline_bits.append(f"({year})")
    if publisher:
        byline_bits.append(f"— {publisher}")
    if byline_bits:
        body.append(" ".join(byline_bits))
        body.append("")

    if contributors:
        body.append("**Contributors:** " + ", ".join(contributors))
        body.append("")

    if synopsis:
        body.append(synopsis)
        body.append("")

    if clusters:
        body.append("## Themes")
        body.append("")
        for c in clusters:
            body.append(f"- {cluster_link(c)}")
        body.append("")

    valid_conns = [c for c in conns if c in all_titles]
    if valid_conns:
        body.append("## In conversation with")
        body.append("")
        for c in valid_conns:
            body.append(f"- {book_link(c)}")
        body.append("")

    # Surface unresolved cross-refs separately so they aren't silently dropped
    unresolved = [c for c in conns if c not in all_titles]
    if unresolved:
        body.append("## Unresolved references")
        body.append("")
        body.append("*These referenced titles aren't in the catalog yet:*")
        body.append("")
        for c in unresolved:
            body.append(f"- {c}")
        body.append("")

    if needs_review:
        body.append("---")
        body.append("")
        body.append("> ⚠️ This entry is flagged for review.")
        body.append("")

    content = "\n".join(fm) + "\n" + "\n".join(body).rstrip() + "\n"
    filename = book_slug(title) + ".md"
    return title, filename, content


def format_cluster_entry(entry: dict, all_titles: set[str]) -> list[str]:
    """Multi-line block for an entry on a cluster page."""
    title = entry.get("title", "").strip()
    creator = get_creator(entry)
    year = entry.get("year")
    mt = get_media_type(entry)
    tag = f"[{mt}] " if mt != "book" else ""

    head = f"- {tag}{book_link(title)}"
    if creator:
        head += f" — {creator}"
    if year:
        head += f" ({year})"

    lines = [head]
    synopsis = (entry.get("synopsis") or "").strip()
    if synopsis:
        lines.append(f"  {synopsis}")

    conns = [c for c in (entry.get("in_conversation_with") or []) if c in all_titles]
    if conns:
        linked = ", ".join(book_link(c) for c in conns)
        lines.append(f"  *In conversation with:* {linked}")

    return lines


def make_cluster_page(
    label: str,
    entries: list[dict],
    all_titles: set[str],
) -> tuple[str, str, str]:
    count = len(entries)
    noun = "entry" if count == 1 else "entries"

    md = [
        f"# {label}",
        "",
        f"*{count} {noun} in this cluster.*",
        "",
        "[← Back to wiki index](INDEX.md)",
        "",
    ]

    for entry in entries:
        md.extend(format_cluster_entry(entry, all_titles))
        md.append("")

    return label, cluster_slug(label) + ".md", "\n".join(md).rstrip() + "\n"


def make_index_page(
    cluster_pages: list[tuple[str, str, str]],
    book_pages: list[tuple[str, str, str]],
    config: dict,
    total_entries: int,
) -> str:
    lines = [
        f"# {config['collection_name']} — Wiki Index",
        "",
        f"*{total_entries} entries across {len(cluster_pages)} theme clusters and "
        f"{len(book_pages)} per-book pages. Auto-generated from `catalog.json`.*",
        "",
        "Each book appears on every theme cluster page it qualifies for, "
        "and every cross-reference is a `[[wikilink]]`, so the Obsidian graph view "
        "traces the actual connections in the collection.",
        "",
        "## Theme Clusters",
        "",
    ]

    def cluster_sort_key(item):
        title, _, content = item
        count = sum(1 for line in content.splitlines() if line.startswith("- "))
        is_misc = 1 if title == MISC_CLUSTER_NAME else 0
        return (is_misc, -count, title.lower())

    for title, filename, content in sorted(cluster_pages, key=cluster_sort_key):
        count = sum(1 for line in content.splitlines() if line.startswith("- "))
        noun = "entry" if count == 1 else "entries"
        lines.append(f"- [{title}]({filename}) — {count} {noun}")

    lines.append("")
    lines.append("## Books (A–Z)")
    lines.append("")

    for title, filename, _content in sorted(book_pages, key=lambda x: x[0].lower()):
        lines.append(f"- [{title}](books/{filename})")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_wiki() -> list[tuple[str, str, str]]:
    catalog = load_catalog()
    config = load_config()
    cluster_order, buckets, title_to_clusters = derive_multi_clusters(
        catalog, min_size=int(config.get("cluster_min_size", 2))
    )
    all_titles = {e["title"] for e in catalog}

    WIKI_DIR.mkdir(exist_ok=True)
    BOOKS_DIR.mkdir(exist_ok=True)

    # Wipe stale per-book pages so renames/removals don't leave orphans behind
    for stale in BOOKS_DIR.glob("*.md"):
        stale.unlink()
    # Wipe stale cluster pages too
    for stale in WIKI_DIR.glob("*.md"):
        if stale.name == "INDEX.md":
            continue
        stale.unlink()

    cluster_pages = []
    for label in cluster_order:
        entries = buckets.get(label, [])
        if not entries:
            continue
        cluster_pages.append(make_cluster_page(label, entries, all_titles))

    book_pages = [make_book_page(e, title_to_clusters, all_titles) for e in catalog]

    for _title, filename, content in cluster_pages:
        (WIKI_DIR / filename).write_text(content)
    for _title, filename, content in book_pages:
        (BOOKS_DIR / filename).write_text(content)

    (WIKI_DIR / "INDEX.md").write_text(
        make_index_page(cluster_pages, book_pages, config, len(catalog))
    )

    # Return cluster pages for the report (matches old contract)
    return cluster_pages


if __name__ == "__main__":
    pages = generate_wiki()
    print(f"Generated {len(pages)} cluster pages + per-book pages + INDEX.md\n")
    for title, filename, content in pages:
        size = len(content)
        n_lines = content.count("\n")
        print(f"  {filename:45s} {size:>6d} bytes  ({n_lines} lines)")

    index_path = WIKI_DIR / "INDEX.md"
    index_size = index_path.stat().st_size
    print(f"\n  {'INDEX.md':45s} {index_size:>6d} bytes")

    book_count = len(list(BOOKS_DIR.glob("*.md")))
    print(f"  books/ contains {book_count} per-book pages")
