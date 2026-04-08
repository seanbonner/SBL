#!/usr/bin/env python3
"""
regenerate.py — Regenerate tiered context files and wiki from catalog.json.

Supports multi-media catalogs (books, films, music). Each media type is
organized within the thematic groupings, with type labels in the output.

Usage:
    python3 scripts/regenerate.py           # Regenerate everything (context + wiki)
    python3 scripts/regenerate.py --wiki    # Regenerate wiki pages only
    python3 scripts/regenerate.py --context # Regenerate context tiers only

Produces three context tiers from catalog.json:
  - CONTEXT.md          Full version with complete synopses (~150KB, ~40K tokens)
  - CONTEXT_COMPACT.md  One-line per entry with groupings (~15-20KB, ~5K tokens)
  - CONTEXT_OVERVIEW.md Intellectual profile only (~2-3KB, ~500 tokens)

And a wiki/ directory of synthesized thematic pages tracing intellectual
threads across the collection (via generate_wiki.py).

Run this after any changes to catalog.json to keep all generated files in sync.
"""


from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "catalog.json"
CONTEXT_PATH = REPO_ROOT / "CONTEXT.md"
COMPACT_PATH = REPO_ROOT / "CONTEXT_COMPACT.md"
OVERVIEW_PATH = REPO_ROOT / "CONTEXT_OVERVIEW.md"
CONFIG_PATH = REPO_ROOT / "config.json"
CONFIG_EXAMPLE_PATH = REPO_ROOT / "config.example.json"

VALID_MEDIA_TYPES = {"book", "film", "music"}

# Media type display labels and icons
MEDIA_LABELS = {
    "book": "\U0001F4D6",   # open book emoji
    "film": "\U0001F3AC",   # clapper board
    "music": "\U0001F3B5",  # musical note
}

MISC_CLUSTER_NAME = "Miscellaneous"


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "owner_name": "Your Name",
    "collection_name": "Your Name's Collection",
    "intellectual_profile": (
        "This is a personal media catalog — a structured record of the books, "
        "films, and music that have shaped how I think and work. Edit this in config.json."
    ),
    "profile_closer": "A working library. Edit this in config.json.",
    "cross_cutting_threads": (
        "Cross-cutting threads and relationships are traced via the "
        "`in_conversation_with` graph in the full catalog."
    ),
    "cluster_min_size": 2,
    "max_overview_clusters": 15,
}


def load_config() -> dict:
    """Load config.json if present, else config.example.json, else defaults.

    Keys missing from the loaded file fall back to DEFAULT_CONFIG so the
    pipeline always works, even against an incomplete config.
    """
    cfg = dict(DEFAULT_CONFIG)
    for path in (CONFIG_PATH, CONFIG_EXAMPLE_PATH):
        if path.exists():
            try:
                with open(path, "r") as f:
                    loaded = json.load(f)
                # Drop commentary keys (anything starting with "_") and unknown keys
                for k, v in loaded.items():
                    if k.startswith("_"):
                        continue
                    if k in DEFAULT_CONFIG:
                        cfg[k] = v
                return cfg
            except (OSError, json.JSONDecodeError):
                continue
    return cfg


# ---------------------------------------------------------------------------
# Theme-driven clustering
#
# Clusters are derived from the themes arrays on catalog entries, not from
# hardcoded keyword lists. A cluster is created for each theme that appears
# on at least `cluster_min_size` entries. Each entry is placed in its most
# specific qualifying cluster (the one with the smallest total count), so
# narrow clusters aren't swallowed by broad ones. Entries with no qualifying
# theme land in "Miscellaneous".
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_media_type(entry: dict) -> str:
    """Get the media_type of an entry, defaulting to 'book'."""
    mt = entry.get("media_type", "book")
    return mt if mt in VALID_MEDIA_TYPES else "book"


def get_creator(entry: dict) -> str:
    """Get the primary creator field based on media_type."""
    mt = get_media_type(entry)
    if mt == "film":
        return (entry.get("director") or "").strip()
    elif mt == "music":
        return (entry.get("artist") or "").strip()
    else:
        return (entry.get("author") or "").strip()


def get_creator_label(entry: dict) -> str:
    """Get the label for the creator field based on media_type."""
    mt = get_media_type(entry)
    if mt == "film":
        return "dir."
    elif mt == "music":
        return "by"
    return ""  # books use em-dash convention


def media_type_tag(entry: dict) -> str:
    """Return a short tag like [film] or [music] for non-book entries."""
    mt = get_media_type(entry)
    if mt == "book":
        return ""
    return f"[{mt}] "


# ---------------------------------------------------------------------------
# Data loading & categorization
# ---------------------------------------------------------------------------

def load_catalog() -> list[dict]:
    with open(CATALOG_PATH, "r") as f:
        return json.load(f)


def _normalize_theme(t: str) -> str:
    """Normalize a theme string for counting and display."""
    return " ".join(t.strip().split()).lower()


def _display_theme(t: str) -> str:
    """Render a normalized theme as a human-friendly cluster label.

    - Short function words (and, or, the, of, in, for, a, an) stay lowercase
      unless they're the first word.
    - Words matching SPECIAL_CASE keep their canonical casing (NFTs, DAO, etc.).
    - Everything else is title-cased.
    """
    SPECIAL_CASE = {
        "nft": "NFT",
        "nfts": "NFTs",
        "ai": "AI",
        "dj": "DJ",
        "dao": "DAO",
        "daos": "DAOs",
        "url": "URL",
        "cpu": "CPU",
        "gpu": "GPU",
        "3d": "3D",
        "2d": "2D",
        "obey": "OBEY",
        "mtv": "MTV",
        "mschf": "MSCHF",
        "kaws": "KAWS",
        "bbc": "BBC",
        "nyc": "NYC",
        "uk": "UK",
        "usa": "USA",
    }
    LOWER_WORDS = {"and", "or", "the", "of", "in", "for", "a", "an", "to", "on", "with", "as"}
    parts = t.split()
    out = []
    for i, p in enumerate(parts):
        lower = p.lower()
        if lower in SPECIAL_CASE:
            out.append(SPECIAL_CASE[lower])
        elif i > 0 and lower in LOWER_WORDS:
            out.append(lower)
        else:
            out.append(p[:1].upper() + p[1:])
    return " ".join(out)


def derive_clusters(
    catalog: list[dict], min_size: int
) -> tuple[list[str], dict[str, list[dict]]]:
    """Derive cluster names and assign catalog entries to them.

    Algorithm:
      1. Count theme frequencies across the catalog.
      2. A theme initially "qualifies" if it appears on >= min_size entries.
      3. Each entry is assigned to its most specific qualifying theme
         (smallest count among its themes; alphabetical tiebreak).
      4. Because "most specific" can drain a broader theme of its members
         (its entries prefer narrower sub-themes), we then prune any cluster
         whose actual assigned size is below min_size and reassign those
         entries — repeating until stable. The pruning is bounded to avoid
         infinite loops on pathological inputs.

    Returns:
        cluster_order: list of cluster display names, largest first,
                       with MISC_CLUSTER_NAME appended last if non-empty.
        buckets: dict mapping display name -> list of entries, sorted by
                 media type then title within each cluster.
    """
    # 1) Count normalized theme frequencies
    theme_counts: Counter[str] = Counter()
    for entry in catalog:
        seen = set()
        for t in entry.get("themes", []):
            n = _normalize_theme(t)
            if n and n not in seen:
                theme_counts[n] += 1
                seen.add(n)

    # 2) Initial qualifying set
    qualifying = {t for t, c in theme_counts.items() if c >= min_size}

    # 3 + 4) Iterate: assign, prune undersized clusters, repeat
    def assign(qual: set[str]) -> dict[str, list[dict]]:
        assigned: dict[str, list[dict]] = {}
        for entry in catalog:
            entry_themes = {_normalize_theme(t) for t in entry.get("themes", [])}
            candidates = entry_themes & qual
            if candidates:
                chosen = min(candidates, key=lambda t: (theme_counts[t], t))
                key = chosen  # use raw key internally; display later
            else:
                key = None  # Miscellaneous sentinel
            assigned.setdefault(key, []).append(entry)
        return assigned

    assigned = assign(qualifying)
    for _ in range(20):  # bounded; usually converges in 1-3 passes
        undersized = {k for k, v in assigned.items()
                      if k is not None and len(v) < min_size}
        if not undersized:
            break
        qualifying -= undersized
        assigned = assign(qualifying)

    # 5) Convert internal keys -> display labels and sort entries
    type_order = {"book": 0, "film": 1, "music": 2}
    buckets: dict[str, list[dict]] = {}
    for key, entries in assigned.items():
        label = MISC_CLUSTER_NAME if key is None else _display_theme(key)
        buckets.setdefault(label, []).extend(entries)
    for label in buckets:
        buckets[label].sort(key=lambda e: (
            type_order.get(get_media_type(e), 9),
            e.get("title", "").lower()
        ))

    # 6) Cluster order: largest first, Miscellaneous always last
    named = [(label, len(entries)) for label, entries in buckets.items()
             if label != MISC_CLUSTER_NAME]
    named.sort(key=lambda x: (-x[1], x[0]))
    cluster_order = [label for label, _ in named]
    if MISC_CLUSTER_NAME in buckets:
        cluster_order.append(MISC_CLUSTER_NAME)

    return cluster_order, buckets


def build_buckets(
    catalog: list[dict], config: dict
) -> tuple[list[str], dict[str, list[dict]]]:
    """Cluster the catalog and return (cluster_order, buckets)."""
    return derive_clusters(catalog, min_size=int(config.get("cluster_min_size", 2)))


# ---------------------------------------------------------------------------
# TIER 1: CONTEXT.md — Full version with complete synopses
# ---------------------------------------------------------------------------

def format_entry_full(entry: dict, all_titles: set) -> list[str]:
    """Format a single catalog entry as full markdown lines."""
    lines = []
    mt = get_media_type(entry)
    title = entry.get("title", "").strip()
    creator = get_creator(entry)
    year = entry.get("year")
    synopsis = entry.get("synopsis", "").strip()
    themes = entry.get("themes", [])
    connections = entry.get("in_conversation_with", [])

    # Title line with media type tag for non-books
    tag = media_type_tag(entry)
    parts = [f"{tag}**{title}**"]
    if creator:
        parts[0] += f" — {creator}"
    if year:
        parts[0] += f" ({year})"
    lines.append(parts[0])

    # Film-specific: cast
    if mt == "film":
        cast = entry.get("cast", [])
        if cast:
            lines.append(f"**Cast:** {', '.join(cast)}")
        fmt = entry.get("format")
        if fmt:
            lines.append(f"**Format:** {fmt}")

    # Music-specific: label, format
    if mt == "music":
        label = entry.get("label")
        if label:
            lines.append(f"**Label:** {label}")
        fmt = entry.get("format")
        if fmt:
            lines.append(f"**Format:** {fmt}")

    if synopsis:
        lines.append(synopsis)
    if themes:
        lines.append(f"**Themes:** {', '.join(themes)}")

    valid_conns = [c for c in connections if c in all_titles]
    if valid_conns:
        lines.append(f"**In conversation with:** {', '.join(valid_conns)}")

    lines.append("")
    return lines


def _type_summary(catalog: list[dict]) -> str:
    """Return a human-readable media breakdown like '12 books, 3 films'."""
    type_counts = Counter(get_media_type(e) for e in catalog)
    parts = []
    for mt in ["book", "film", "music"]:
        if type_counts[mt]:
            label = "books" if mt == "book" else "films" if mt == "film" else "albums"
            parts.append(f"{type_counts[mt]} {label}")
    return ", ".join(parts)


def generate_full(
    catalog: list[dict],
    cluster_order: list[str],
    buckets: dict[str, list[dict]],
    config: dict,
) -> int:
    """Generate CONTEXT.md — full version with complete synopses."""
    all_titles = {e["title"] for e in catalog}
    type_summary = _type_summary(catalog)

    md = [
        f"# {config['collection_name']} — Intellectual Context (Full)",
        "",
        f"*{len(catalog)} entries ({type_summary}) across "
        f"{len(cluster_order)} thematic clusters. "
        "This is the full rendering with complete synopses, themes, and relationship annotations. "
        "For lighter versions, see CONTEXT_COMPACT.md (~5K tokens) or CONTEXT_OVERVIEW.md (~500 tokens).*",
        "",
        config["intellectual_profile"],
        "",
        "## Catalog",
        "",
    ]

    entry_count = 0
    for label in cluster_order:
        entries = buckets.get(label, [])
        if not entries:
            continue
        md.append(f"### {label}")
        md.append("")
        for entry in entries:
            md.extend(format_entry_full(entry, all_titles))
            entry_count += 1

    CONTEXT_PATH.write_text("\n".join(md))
    return entry_count


# ---------------------------------------------------------------------------
# TIER 2: CONTEXT_COMPACT.md — One-line per entry with groupings
# ---------------------------------------------------------------------------

def format_entry_compact(entry: dict, all_titles: set) -> str:
    """Format a single entry as one compact line: [type] title, creator, year."""
    mt = get_media_type(entry)
    title = entry.get("title", "").strip()
    creator = get_creator(entry)
    year = entry.get("year")

    tag = f"[{mt}] " if mt != "book" else ""
    line = f"- {tag}{title}"
    if creator:
        line += f" — {creator}"
    if year:
        line += f" ({year})"

    return line


def generate_compact(
    catalog: list[dict],
    cluster_order: list[str],
    buckets: dict[str, list[dict]],
    config: dict,
) -> int:
    """Generate CONTEXT_COMPACT.md — one-line per entry with clusters."""
    all_titles = {e["title"] for e in catalog}
    type_summary = _type_summary(catalog)

    md = [
        f"# {config['collection_name']} — Compact Reference",
        "",
        f"*{len(catalog)} entries ({type_summary}). One-line entries with themes and relationship pointers. "
        "For full synopses see CONTEXT.md; for intellectual profile only see CONTEXT_OVERVIEW.md.*",
        "",
    ]

    entry_count = 0
    for label in cluster_order:
        entries = buckets.get(label, [])
        if not entries:
            continue
        md.append(f"### {label}")
        md.append("")
        for entry in entries:
            md.append(format_entry_compact(entry, all_titles))
            entry_count += 1
        md.append("")

    COMPACT_PATH.write_text("\n".join(md))
    return entry_count


# ---------------------------------------------------------------------------
# TIER 3: CONTEXT_OVERVIEW.md — Intellectual profile only
# ---------------------------------------------------------------------------

def generate_overview(
    catalog: list[dict],
    cluster_order: list[str],
    buckets: dict[str, list[dict]],
    config: dict,
) -> None:
    """Generate CONTEXT_OVERVIEW.md — short intellectual profile + top clusters."""
    total = len(catalog)
    type_summary = _type_summary(catalog)

    # Year range (only real years)
    years = [e["year"] for e in catalog if e.get("year")]
    year_range = f"{min(years)}\u2013{max(years)}" if years else "various"

    def representatives(label: str, n: int = 2) -> list[str]:
        entries = buckets.get(label, [])
        scored = sorted(
            entries,
            key=lambda e: len(e.get("in_conversation_with", [])),
            reverse=True,
        )
        return [e["title"] for e in scored[:n]]

    max_clusters = int(config.get("max_overview_clusters", 15))
    top_clusters = [lbl for lbl in cluster_order if lbl != MISC_CLUSTER_NAME][:max_clusters]

    md = [
        f"# {config['collection_name']} — Intellectual Profile",
        "",
        f"*{total} entries ({type_summary}) spanning {year_range}. Lightweight overview for "
        "baseline context loading. For entries see CONTEXT_COMPACT.md or CONTEXT.md.*",
        "",
        config["intellectual_profile"],
        "",
        config["profile_closer"],
        "",
        "## Major Clusters",
        "",
    ]

    for label in top_clusters:
        count = len(buckets.get(label, []))
        reps = representatives(label, 2)
        short_reps = [r if len(r) < 40 else r[:37] + "..." for r in reps]
        md.append(f"- **{label}** ({count}) \u2014 {', '.join(short_reps)}")

    md.append("")
    md.append(config["cross_cutting_threads"])
    md.append("")

    OVERVIEW_PATH.write_text("\n".join(md))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate():
    catalog = load_catalog()
    config = load_config()
    cluster_order, buckets = build_buckets(catalog, config)

    # Generate all three tiers
    full_count = generate_full(catalog, cluster_order, buckets, config)
    compact_count = generate_compact(catalog, cluster_order, buckets, config)
    generate_overview(catalog, cluster_order, buckets, config)

    # Report
    active = len([lbl for lbl in cluster_order if buckets.get(lbl)])
    type_counts = Counter(get_media_type(e) for e in catalog)
    type_parts = []
    for mt in ["book", "film", "music"]:
        if type_counts[mt]:
            type_parts.append(f"{type_counts[mt]} {mt}s")

    print(f"Generated {len(catalog)} entries ({', '.join(type_parts)}) across {active} clusters:\n")

    for path, label in [
        (CONTEXT_PATH, "CONTEXT.md (full)"),
        (COMPACT_PATH, "CONTEXT_COMPACT.md (compact)"),
        (OVERVIEW_PATH, "CONTEXT_OVERVIEW.md (overview)"),
    ]:
        size = path.stat().st_size
        lines = len(path.read_text().splitlines())
        if size >= 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} bytes"
        print(f"  {label:40s} {size_str:>10s}  ({lines} lines)")

    return full_count, compact_count


def generate_wiki_pages():
    """Generate wiki pages by delegating to generate_wiki.py."""
    from generate_wiki import generate_wiki
    pages = generate_wiki()

    print(f"\nGenerated {len(pages)} wiki pages + index-sbl.md in wiki/\n")
    for title, filename, content in sorted(pages, key=lambda x: x[0]):
        size = len(content)
        lines = content.count('\n')
        print(f"  {filename:55s} {size:>6d} bytes  ({lines} lines)")

    wiki_dir = REPO_ROOT / "wiki"
    index_size = (wiki_dir / "index-sbl.md").stat().st_size
    print(f"\n  {'index-sbl.md':55s} {index_size:>6d} bytes")
    return pages


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regenerate context files and wiki from catalog.json")
    parser.add_argument("--wiki", action="store_true", help="Regenerate wiki pages only")
    parser.add_argument("--context", action="store_true", help="Regenerate context tiers only")
    args = parser.parse_args()

    # Default: regenerate everything
    do_context = not args.wiki or args.context
    do_wiki = not args.context or args.wiki
    if not args.wiki and not args.context:
        do_context = True
        do_wiki = True

    ok = True

    if do_context:
        full_count, compact_count = generate()
        catalog = load_catalog()
        expected = len(catalog)

        for label, count in [("full", full_count), ("compact", compact_count)]:
            if count == expected:
                print(f"\n  {label}: all {expected} entries included \u2713")
            else:
                print(f"\n  {label}: expected {expected} entries, got {count} \u2717", file=sys.stderr)
                ok = False

    if do_wiki:
        # Add scripts dir to path so generate_wiki can be imported
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        generate_wiki_pages()

    if not ok:
        sys.exit(1)
